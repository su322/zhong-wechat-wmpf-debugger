# WMPF 版本适配指南

## 概述

微信小程序的 WMPF（WeChat Mini Program Framework）运行时独立于微信主程序更新。
当 WMPF 版本更新时，`flue.dll`（小程序宿主进程的核心模块）中的关键函数偏移地址会发生变化。
本指南说明如何为新版本查找这些偏移地址。

## 适配工作流

```
发现新 WMPF 版本不支持
    ↓
运行 `python tools/find_offsets.py` 自动分析
    ↓
创建 `vendor/wmpfdebugger/frida/config/addresses.{version}.json`
    ↓
运行 `python main.py --check` 验证新版本被识别
    ↓
测试 `python main.py -x` 开启 F12
```

## 地址文件格式

```json
{
    "Version": 20089,
    "LoadStartHookOffset": "0x25e0170",
    "CDPFilterHookOffset": "0x2d95ab0",
    "SceneBaseOffset": 64,
    "SceneOffsets": [1480, 1416, 456]
}
```

| 字段 | 说明 |
|------|------|
| `Version` | WMPF 版本号，来自 `RadiumWMPF/{version}/` 路径 |
| `LoadStartHookOffset` | `AppletIndexContainer::OnLoadStart` 函数的 RVA 偏移 |
| `CDPFilterHookOffset` | `SendToClientFilter` 函数的 RVA 偏移 |
| `SceneBaseOffset` | 场景链基址偏移（近年未变，固定 64） |
| `SceneOffsets` | C++ 对象成员偏移（近年未变，固定 [1480, 1416, 456]） |

## 快速适配（推荐）

```bash
# 1. 运行自动分析工具
python tools/find_offsets.py

# 2. 在交互模式下输入版本号，自动生成配置文件
```

如果工具无法精确识别，使用下面的运行时探测。

## 运行时探测（备用方案）

```bash
# 1. 打开微信，运行一个小程序
# 2. 找到 WeChatAppEx 主进程 PID（父进程是 Weixin.exe 的那个）

# 3. 探测 CDPFilterHook 候选偏移
python tools/probe_offsets.py --cdpfilter 0x2d95ab0

# 4. 探测 LoadStartHook 候选偏移
python tools/probe_offsets.py --loadstart 0x25e0170
```

探测原理：Frida 会在候选地址安装 Hook，当小程序加载时，
如果 Hook 触发则说明偏移正确。

如果没有一个候选触发，需要扩大搜索范围或使用 IDA Pro 逆向。

## 手动逆向方法（IDA Pro）

如需手动逆向 `flue.dll`：

### 1. 找到 LoadStartHookOffset

1. 在 IDA 中打开 `flue.dll`（ARM: 用 ARM64 分析，x64: 用 x64 分析）
2. 搜索字符串 `"applet::AppletIndexContainer::OnLoadStart"` 或 `"OnLoadStart"`
3. 找到引用该字符串的代码位置，向上回溯到函数入口
4. 函数入口特征：`push r15; push r14; push rsi; push rdi; push rbx`（Windows x64）
   或 `sub sp, sp, #XX; stp x29, x30, [sp, #XX]`（ARM64 macOS）
5. 记录函数入口 RVA（相对 `flue.dll` 基址的偏移）

### 2. 找到 CDPFilterHookOffset

1. 搜索字符串 `"devtools_message_filter_applet_webview.cc"` 或 `"SendToClientFilter"`
2. 找到引用字符串的代码，向上回溯到函数入口
3. 函数特征：`push r15; push r14; push r13; push r12; push rsi; push rdi; push rbx`（Windows x64）
4. 记录函数入口 RVA

### 3. macOS ARM 注意事项

- Windows 上目标模块为 `flue.dll`，macOS 上为 `flue.dylib` 或 `WeChatAppEx Framework`
- 架构为 ARM64 (AArch64)，函数序言不同
- macOS 上此项目的 WMPF 桥模式不适用（仅 Windows）
- macOS 用户请使用 [JaveleyQAQ/WeChatOpenDevTools-Python](https://github.com/JaveleyQAQ/WeChatOpenDevTools-Python) 
  或 [f4l1k/WeChatOpenDevTools-Python-arm](https://github.com/f4l1k/WeChatOpenDevTools-Python-arm)
- `find_offsets.py` 工具使用 pefile（仅 PE 格式），不支持 macOS 的 Mach-O 格式

## SceneOffsets 的确定方法

SceneOffsets 通常不需要修改，但如果工具在小程序加载后崩溃，
可能需要调整。方法：

1. 用 IDA 打开 `flue.dll`
2. 定位到 `AppletIndexContainer::OnLoadStart` 函数
3. 查找 `hookOnLoadScene` 调用逻辑中的指针链偏移
4. 根据 C++ 类的成员布局确定新偏移

## 验证适配是否成功

```bash
# 1. 检查 WMPF 版本是否被识别
python main.py --check

# 2. 开启 F12
python main.py -x

# 3. 打开小程序，按 F12
# 如果 DevTools 正常弹出，适配成功
```

## 常见问题

**Q: WMPF 版本未被识别**
A: 检查 `vendor/wmpfdebugger/frida/config/` 目录下是否有对应版本的 `addresses.{version}.json` 文件

**Q: 适配后小程序崩溃**
A: SceneOffsets 可能不正确。尝试使用前一个版本的 SceneOffsets 值

**Q: CDP 端口 62000 未开放**
A: Node.js 桥可能未正确启动。检查 Node.js 是否安装，运行 `npm install` 

**Q: 工具提示 "unsupported WMPF version"**
A: 运行 `find_offsets.py` 自动适配，或手动创建地址文件
