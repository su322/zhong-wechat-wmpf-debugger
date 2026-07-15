#!/usr/bin/env python3
"""
运行时 Hook 偏移探测工具

在已运行的 WeChatAppEx 进程上，尝试多个候选偏移，
通过 Frida Hook 来验证哪个偏移是正确的。

用法:
    python tools/probe_offsets.py                                     # 自动探测
    python tools/probe_offsets.py --pid 24232                          # 指定 PID
    python tools/probe_offsets.py --loadstart 0x25e0170                # 测试特定偏移
    python tools/probe_offsets.py --cdpfilter 0x2d95ab0                # 测试特定偏移
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import frida
import psutil

# ============================================================
# 配置：20089 的候选偏移（基于逆向分析）
# ============================================================
CANDIDATES = {
    # CDPFilterHook: 从 SendToClientFilter 字符串引用往前找函数入口
    "CDPFilterHook": [
        "0x2d95500",  # 保守估计（20079 + 0x30）
        "0x2d95ab0",  # 工具分析结果（推荐）
        "0x2d95130",  # 另一个候选
    ],
    # LoadStartHook: 以下是可能的候选
    "LoadStartHook": [
        "0x25e0170",  # 20079 附近有 push r15,r14,rsi,rdi,rbx prologue
        "0x25e05f0",  # 另一个靠近的 prologue
        "0x25dedf0",  # 另一个候选
        "0x25d2b70",  # 另一个候选
    ],
}

TEST_SCRIPT = """
'use strict';

const config = JSON.parse(`@@CONFIG@@`);
const testType = `@@TYPE@@`;

function main() {
    const module = Process.findModuleByName("flue.dll");
    if (!module) {
        send(JSON.stringify({type: "error", message: "找不到 flue.dll"}));
        return;
    }

    const base = module.base;
    const offset = parseInt(config.offset, 16);
    const addr = base.add(offset);

    send(JSON.stringify({
        type: "info",
        message: `flue.dll base: ${base}, offset: ${config.offset}, addr: ${addr}`,
        testType: testType,
        offset: config.offset
    }));

    try {
        Interceptor.attach(addr, {
            onEnter(args) {
                send(JSON.stringify({
                    type: "hit",
                    message: `[${testType}] Hook 触发!`,
                    testType: testType,
                    offset: config.offset,
                    timestamp: Date.now()
                }));

                if (testType === "CDPFilterHook") {
                    // 验证是否是 SendToClientFilter
                    try {
                        const val = args[0].readPointer().add(8).readU32();
                        send(JSON.stringify({
                            type: "data",
                            message: `args[0]+8 value: ${val}`,
                            val: val
                        }));
                    } catch(e) {}
                }

                if (testType === "LoadStartHook") {
                    // 验证是否是 OnLoadStart（rdx 标志位操作）
                    try {
                        const rdx = this.context.rdx;
                        send(JSON.stringify({
                            type: "data",
                            message: `rdx: 0x${rdx.toString(16)}`,
                            rdx: rdx.toString(16)
                        }));
                    } catch(e) {}
                }
            },
            onLeave(retval) {}
        });

        send(JSON.stringify({
            type: "attached",
            message: `Hook 安装成功，等待触发...`,
            testType: testType,
            offset: config.offset
        }));

    } catch(e) {
        send(JSON.stringify({
            type: "error",
            message: `Hook 安装失败: ${e.message}`,
            testType: testType,
            offset: config.offset
        }));
    }
}

main();
"""


def find_wechatappex():
    """找到可附加的 WeChatAppEx 主进程"""
    device = frida.get_local_device()
    for proc in psutil.process_iter(["pid", "name", "ppid"]):
        try:
            if "WeChatAppEx" in proc.info["name"]:
                pid = proc.info["pid"]
                ppid = proc.info["ppid"]
                # 选择父进程是 Weixin.exe 的主进程
                try:
                    parent = psutil.Process(ppid)
                    if "Weixin" in parent.name():
                        # 验证可附加
                        s = device.attach(pid)
                        s.detach()
                        return pid
                except:
                    continue
        except:
            continue
    return None


def probe_offset(pid, offset_hex, hook_type, timeout=15):
    """探测单个偏移"""
    device = frida.get_local_device()
    session = device.attach(pid)

    script_code = TEST_SCRIPT.replace("@@CONFIG@@", json.dumps({"offset": offset_hex}))
    script_code = script_code.replace("@@TYPE@@", hook_type)

    result = {"offset": offset_hex, "hook_installed": False, "triggered": False, "hits": []}

    def on_message(message, data):
        if message["type"] == "send":
            try:
                msg = json.loads(message["payload"])
                if msg.get("type") == "attached":
                    result["hook_installed"] = True
                    print(f"    ✅ Hook 安装成功")
                elif msg.get("type") == "hit":
                    result["triggered"] = True
                    result["hits"].append(msg)
                    print(f"    🎯 Hook 触发! {msg.get('message', '')}")
                elif msg.get("type") == "error":
                    print(f"    ❌ 错误: {msg.get('message', '')}")
                elif msg.get("type") == "info":
                    print(f"    ℹ️  {msg.get('message', '')}")
                elif msg.get("type") == "data":
                    print(f"    📊  {msg.get('message', '')}")
            except:
                pass

    script = session.create_script(script_code)
    script.on("message", on_message)
    script.load()

    print(f"\n  📡 探测 {hook_type} @ {offset_hex} (等待 {timeout} 秒, 请打开/刷新小程序)")
    time.sleep(timeout)

    session.detach()
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="运行时 Hook 偏移探测工具")
    parser.add_argument("--pid", type=int, help="WeChatAppEx PID")
    parser.add_argument("--loadstart", help="测试单个 LoadStart 偏移")
    parser.add_argument("--cdpfilter", help="测试单个 CDPFilter 偏移")
    parser.add_argument("--timeout", type=int, default=15, help="每个偏移的等待时间(秒)")
    args = parser.parse_args()

    print("=" * 55)
    print("  WMPF Hook 偏移探测工具")
    print("=" * 55)

    # 获取 PID
    pid = args.pid or find_wechatappex()
    if not pid:
        print("找不到 WeChatAppEx 进程，请先打开微信并运行小程序")
        return

    print(f"\n📌 目标进程: WeChatAppEx (PID: {pid})")
    print()

    if args.loadstart:
        probe_offset(pid, args.loadstart, "LoadStartHook", args.timeout)
    elif args.cdpfilter:
        probe_offset(pid, args.cdpfilter, "CDPFilterHook", args.timeout)
    else:
        # 探测所有候选
        results = {"CDPFilterHook": [], "LoadStartHook": []}

        for hook_type, candidates in CANDIDATES.items():
            print(f"\n🔍 探测 {hook_type} 候选偏移:")
            for offset_hex in candidates:
                r = probe_offset(pid, offset_hex, hook_type, args.timeout)
                results[hook_type].append(r)
                if r["triggered"]:
                    print(f"    ✅ 候选 {offset_hex} 触发了 Hook!")
                    # 继续探测其他候选确认
                print()

        # 总结
        print("\n" + "=" * 55)
        print("  探测结果总结")
        print("=" * 55)
        for hook_type, rs in results.items():
            triggered = [r for r in rs if r["triggered"]]
            installed = [r for r in rs if r["hook_installed"]]
            print(f"\n  {hook_type}:")
            print(f"    Hook 安装成功: {len(installed)}/{len(rs)}")
            print(f"    Hook 触发: {len(triggered)}/{len(rs)}")
            for r in triggered:
                print(f"    ✅ {r['offset']} == 正确的偏移!")


if __name__ == "__main__":
    main()
