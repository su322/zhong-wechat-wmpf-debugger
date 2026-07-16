# zhong-wechat-wmpf-debugger (Fork)

> Windows WeChat 小程序 F12 开启工具（WMPF 协议桥方案）
>
> 原始项目：[netz888/zhong-wechat-wmpf-debugger](https://github.com/netz888/zhong-wechat-wmpf-debugger)

---

## 支持的版本

| WeChat | WMPF | 状态 |
|--------|------|------|
| 4.1.11.54 | **20089** | ✅ 本 fork 新增 |
| 4.1.11.52 | 20079 | ✅ (upstream) |
| 4.1.11.23 | 20005 | ✅ (upstream) |
| ... | ... | 详见 `vendor/wmpfdebugger/frida/config/` |

## 快速开始

```powershell
pip install -r requirements.txt
pushd vendor\wmpfdebugger
npm install --force
popd
python main.py --check
python main.py -x
```

执行完 `python main.py -x` 后，在微信中打开一个小程序，然后访问终端输出的 DevTools URL 即可调试。

## 已知局限

此工具有其适用范围，不一定能满足所有调试需求：

| 类型 | 能否调试 | 说明 |
|------|---------|------|
| **纯小程序**（原生页面） | ✅ | 可查看 Console、Source、Elements 等面板 |
| **WebView 小程序**（嵌套外部网页） | ❌ | 只能看到外层壳 `page-frame.html`，看不到内层网页的请求和报错 |
| **wx.request() API 请求** | ❌ | 走微信原生网络栈，不在 CDP Network 面板中显示 |
| **内置浏览器 F12** | ✅ | 使用 `-c` 参数 |

如果你的小程序是 **webview 类型**（即加载外部 URL 的），请使用 **Fiddler / Charles** 抓包，或直接在浏览器中调试对应的 URL 地址。

## 系统要求

- **Windows** 10/11 (x64)
- **Python** 3.10+
- **Node.js** 18+
- **微信** 4.x (已安装并登录)

## 命令

| 命令 | 说明 |
|------|------|
| `python main.py -x` | 开启小程序 F12（WMPF 协议桥模式） |
| `python main.py -c` | 开启内置浏览器 F12（传统模式） |
| `python main.py --check` | 检查当前运行时是否支持 |
| `python main.py -x --debug` | 开启详细调试日志 |

## 适配新 WMPF 版本

当微信更新后 WMPF 版本变化，工具会提示 "unsupported WMPF version"。
此时需要为本地的 WMPF 版本创建地址偏移文件。

### 自动适配（推荐）

```bash
python tools/find_offsets.py --interactive
```

详见 [ADAPTATION.md](ADAPTATION.md)。

## 与本仓库其他内容的关系

本仓库还包含了 WeChatOpenDevTools 的技术调研成果：

- 调研文档：[docs/research-and-roadmap.md](docs/research-and-roadmap.md) — 所有公开方案的对比分析
- 实验代码：process injection 方案验证（详见 WeChatOpenDevTools 仓库）

## 致谢

- [netz888](https://github.com/netz888) — 原始 WMPF 协议桥项目
- [志远](https://github.com/chinanji111) — WeChatOpenDevTools 原始项目
- [JaveleyQAQ](https://github.com/JaveleyQAQ) — Python 移植版
