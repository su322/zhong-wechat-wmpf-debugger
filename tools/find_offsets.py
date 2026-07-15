#!/usr/bin/env python3
"""
WMPF 版本适配工具 — 自动查找 flue.dll 中的 Hook 偏移地址

用法:
    python tools/find_offsets.py                              # 分析当前 WMPF 版本
    python tools/find_offsets.py --dll <path_to_flue.dll>     # 指定 DLL 文件
    python tools/find_offsets.py --dir <wmpf_runtime_dir>     # 指定 WMPF 运行时目录
    python tools/find_offsets.py --interactive                 # 交互模式

原理:
    在 flue.dll 中搜索目标函数的特征:
    - LoadStartHook: AppletIndexContainer::OnLoadStart 函数入口
    - CDPFilterHook: SendToClientFilter / devtools_message_filter 函数入口
    - SceneOffsets: C++ 对象成员偏移（多版本间通常不变）
"""

import sys
import os
import json
import glob

# 添加 vendor 到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def find_wmpf_runtimes():
    """自动发现本机安装的 WMPF 运行时版本"""
    base_paths = [
        os.path.expanduser("~/AppData/Roaming/Tencent/xwechat/XPlugin/Plugins/RadiumWMPF"),
        os.path.expanduser("~/.xwechat/XPlugin/Plugins/RadiumWMPF"),
        "/Applications/WeChat.app/Contents/MacOS/RadiumWMPF",
    ]
    versions = []
    for base in base_paths:
        if os.path.isdir(base):
            for d in sorted(os.listdir(base), reverse=True):
                dll_path = os.path.join(base, d, "extracted", "runtime", "flue.dll")
                if os.path.isfile(dll_path):
                    versions.append((d, dll_path))
    return versions


def analyze_dll(dll_path, verbose=True):
    """分析 flue.dll，找到 Hook 偏移地址"""
    try:
        import pefile
    except ImportError:
        print("请先安装 pefile: pip install pefile")
        return None

    pe = pefile.PE(dll_path)

    # 找到 .text section
    text_section = None
    for section in pe.sections:
        name = section.Name.decode().rstrip('\x00').rstrip()
        if name == '.text':
            text_section = section
            break
    if not text_section:
        print("找不到 .text section")
        return None

    TEXT_VA = text_section.VirtualAddress
    TEXT_RAW = section.PointerToRawData

    def rva_to_file(rva):
        return rva - TEXT_VA + TEXT_RAW

    file_size = os.path.getsize(dll_path)

    with open(dll_path, 'rb') as f:
        dll_data = f.read()

    # 查找关键字符串的位置
    string_targets = {
        'SendToClientFilter': b'SendToClientFilter',
        'devtools_message_filter': b'devtools_message_filter',
        'AppletIndexContainer_OnLoadStart': b'AppletIndexContainer',
        'OnLoadStart': b'OnLoadStart',
    }

    string_rvas = {}
    for name, pattern in string_targets.items():
        pos = dll_data.find(pattern)
        if pos >= 0:
            rva = None
            for section in pe.sections:
                sec_name = section.Name.decode().rstrip('\x00').rstrip()
                raw_start = section.PointerToRawData
                raw_end = raw_start + section.SizeOfRawData
                if raw_start <= pos < raw_end:
                    rva = section.VirtualAddress + (pos - raw_start)
                    break
            string_rvas[name] = rva
            if verbose:
                print(f"  [字符串] {name} @ RVA 0x{rva:x}")
        else:
            if verbose:
                print(f"  [字符串] {name} -> 未找到")

    # 查找代码中引用这些字符串的位置
    # 搜索 RIP-relative LEA 指令
    code_start = rva_to_file(TEXT_VA)
    code_end = min(code_start + text_section.SizeOfRawData, file_size)
    text_data = dll_data[code_start:code_end]

    print(f"\n  代码段: 0x{code_start:x} - 0x{code_end:x} ({len(text_data)} 字节)")
    print()

    # 查找引用 SendToClientFilter 字符串的代码
    results = {}
    for str_name, str_rva in string_rvas.items():
        if str_rva is None:
            continue

        # 搜索 LEA rdx, [rip+offset] 模式 (48 8d 15 xx xx xx xx)
        # 和 LEA rcx, [rip+offset] 模式 (48 8d 0d xx xx xx xx)
        refs = []
        for pattern in [b'\x48\x8d\x15', b'\x48\x8d\x0d', b'\x48\x8d\x05']:
            pos = 0
            while True:
                pos = text_data.find(pattern, pos)
                if pos == -1:
                    break
                rel = int.from_bytes(text_data[pos+3:pos+7], 'little', signed=True)
                instr_rva = TEXT_VA + (code_start - text_section.PointerToRawData) + pos
                target_rva = (instr_rva + 7 + rel) & 0xFFFFFFFF
                if target_rva == str_rva or abs(target_rva - str_rva) < 5:
                    refs.append(instr_rva)
                pos += 1

        if refs:
            results[str_name] = refs
            if verbose:
                print(f"  [引用] {str_name}: 在 {len(refs)} 个位置被引用")
                for r in refs[:5]:
                    print(f"    RVA 0x{r:x}")

    # 从引用位置往前找函数入口
    all_refs = []
    for name, refs in results.items():
        all_refs.extend(refs)

    all_refs.sort()

    # 按组聚类（同一个函数的引用通常在一起）
    print("\n  --- 函数入口分析 ---")

    # 搜索函数入口模式：push r15; push r14 (41 57 41 56)
    func_entries = []
    search_start = max(0, code_start)
    search_data = dll_data[search_start:code_end]

    for pattern, name in [
        (b'\x41\x57\x41\x56\x56\x57\x53', "push r15,r14,rsi,rdi,rbx"),
        (b'\x41\x57\x41\x56\x41\x55\x41\x54', "push r15,r14,r13,r12"),
        (b'\x40\x55\x48\x81\xec', "push rbp; sub rsp, XXXX"),
        (b'\x48\x89\x5c\x24', "mov [rsp+XX],rbx"),
        (b'\x55\x48\x8b\xec', "push rbp; mov rbp,rsp"),
    ]:
        pos = 0
        while True:
            pos = search_data.find(pattern, pos)
            if pos == -1:
                break
            abs_file_off = search_start + pos
            rva = abs_file_off - TEXT_RAW + TEXT_VA
            func_entries.append((abs_file_off, rva, pattern, name))
            pos += 1

    # 对那些引用 SendToClientFilter 和 AppletIndexContainer 的，找最近的函数入口
    for str_name, refs in results.items():
        if not refs:
            continue
        first_ref = min(refs)
        first_ref_file = rva_to_file(first_ref)

        # 找最近的函数入口（前向）
        best_entry = None
        for entry_file, entry_rva, pat, pat_name in func_entries:
            if entry_file <= first_ref_file and (best_entry is None or entry_file > rva_to_file(best_entry)):
                best_entry = entry_rva

        if best_entry:
            print(f"  [{str_name}] 推荐 Hook 偏移: {hex(best_entry)}")
            # 检查是否和 20079 的偏移接近
            known = {"SendToClientFilter": 0x2D954D0, "OnLoadStart": 0x25DFB90}
            if str_name in known:
                diff = best_entry - known[str_name]
                print(f"            相对 20079 偏移: {diff:+d} ({hex(diff)})")

    # 输出 SceneOffsets 建议
    print()
    print("  [SceneOffsets] 近年来保持 [1480, 1416, 456] 不变")
    print("  [SceneBaseOffset] 保持 64 不变")
    print()

    # 输出配置
    print("  --- 生成配置 ---")
    config = {
        "Version": 0,
        "LoadStartHookOffset": "0x0",
        "CDPFilterHookOffset": "0x0",
        "SceneBaseOffset": 64,
        "SceneOffsets": [1480, 1416, 456]
    }

    # 优先使用更具体的字符串
    priority_map = {
        "AppletIndexContainer_OnLoadStart": "LoadStartHookOffset",
        "SendToClientFilter": "CDPFilterHookOffset",
        "OnLoadStart": "LoadStartHookOffset",
    }

    for str_name, refs in results.items():
        if not refs:
            continue
        first_ref = min(refs)
        first_ref_file = rva_to_file(first_ref)
        best_entry = None
        for entry_file, entry_rva, pat, pat_name in func_entries:
            if entry_file <= first_ref_file and (best_entry is None or entry_file > rva_to_file(best_entry)):
                best_entry = entry_rva
        if best_entry and str_name in priority_map:
            key = priority_map[str_name]
            # 更具体的字符串优先（不覆盖已有结果）
            if config[key] == "0x0" or str_name in ["AppletIndexContainer_OnLoadStart", "SendToClientFilter"]:
                config[key] = hex(best_entry)

    print(json.dumps(config, indent=4))
    return config


def main():
    import argparse
    parser = argparse.ArgumentParser(description="WMPF Hook 偏移查找工具")
    parser.add_argument("--dll", help="指定 flue.dll 路径")
    parser.add_argument("--dir", help="指定 WMPF 运行时目录")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    args = parser.parse_args()

    print("=" * 55)
    print("  WMPF 版本适配工具 — Hook 偏移查找")
    print("=" * 55)

    if args.dll:
        dll_path = args.dll
    elif args.dir:
        dll_path = os.path.join(args.dir, "flue.dll")
    else:
        # 自动发现
        versions = find_wmpf_runtimes()
        if not versions:
            print("未找到本机 WMPF 运行时")
            return
        print(f"\n发现 {len(versions)} 个 WMPF 版本:")
        for ver, path in versions:
            base_size = os.path.getsize(path) // 1024 // 1024
            print(f"  {ver} -> {path} ({base_size}MB)")
        print()
        # 选择最新版本
        dll_path = versions[0][1]
        print(f"选择最新版本: {versions[0][0]}")

    if not os.path.isfile(dll_path):
        print(f"文件不存在: {dll_path}")
        return

    print(f"\n分析 DLL: {dll_path}")
    file_size_mb = os.path.getsize(dll_path) / 1024 / 1024
    print(f"文件大小: {file_size_mb:.1f} MB")

    config = analyze_dll(dll_path)

    if config and args.interactive:
        ver = input("\n请输入 WMPF 版本号: ")
        config["Version"] = int(ver)
        # 保存
        out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "vendor", "wmpfdebugger", "frida", "config")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"addresses.{ver}.json")
        with open(out_path, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"已保存: {out_path}")


if __name__ == "__main__":
    main()
