# H5 内置浏览器控制台接口探测

本目录用于探测 Windows PC 微信内置浏览器 H5 页面是否能通过 XWeb inspect/DevTools 入口打开控制台。

它和小程序调试不是同一条链路：

- 小程序/WMPF 调试走 `WeChatAppEx.exe`、WMPF remote-debug bridge 和 `devtools://...ws=127.0.0.1:62000`。
- H5 内置浏览器调试走 PC 微信启动 XWeb 子进程时的 inspect 参数。当前项目已有的 `python main.py -c` 会尝试把子进程参数改为 `--xweb-enable-inspect=1`。

## 边界

- 只检查本机微信/XWeb 进程参数和控制台入口。
- 不伪造微信登录态。
- 不绕过网页“仅微信打开”的限制。
- 不读取、保存或复用 Cookie、Token、openid、授权 code。
- 不向第三方 H5 页面注入脚本。

如果页面属于你或客户自己维护，更稳定的方案是在页面源码中加入受控调试模式，例如测试环境、白名单账号或后台开关加载 `vConsole` / `eruda`。

## 使用方式

在仓库根目录执行：

```powershell
powershell -ExecutionPolicy Bypass -File h5-webview-debugger\run_h5_debug.ps1
```

推荐流程：

1. 先关闭所有 PC 微信窗口和后台进程。
2. 运行上面的 PowerShell 脚本。
3. 脚本会调用 `python ..\main.py -c`，启动带 XWeb inspect 参数的微信。
4. 终端出现“Hook 保持中”时，不要按 Enter。
5. 在 PC 微信内打开目标 H5 页面。
6. 页面打开后，用普通浏览器访问 `http://127.0.0.1:9222/json/list`。
7. 如果返回 targets，继续打开其中的 `devtoolsFrontendUrl` 或连接 `webSocketDebuggerUrl`。
8. 回到终端按 Enter 结束 Hook，再根据 `check_h5_debug.py` 输出判断 inspect 参数和端口是否生效。

注意：PC 微信内置浏览器不一定绑定 F12 快捷键。F12 没反应不能直接说明失败，应该优先看 `http://127.0.0.1:9222/json/list` 是否可访问。

## 单独诊断

如果微信已经运行，可以只检查当前进程参数：

```powershell
python h5-webview-debugger\check_h5_debug.py
```

状态含义：

- `enabled`：检测到 inspect 相关参数。还要继续看 `DevTools endpoint probe` 是否能访问固定端口。
- `disabled`：检测到微信相关进程，但没有 inspect 参数。通常需要关闭微信后重新运行 `run_h5_debug.ps1`。
- `not_found`：没有检测到微信或 XWeb 相关进程。
- `unknown`：检测到微信相关进程，但当前权限无法读取命令行。

固定调试端口：

```text
http://127.0.0.1:9222/json/list
```

如果诊断输出里端口不可访问，说明当前 PC 微信版本没有真正暴露 DevTools HTTP 入口，或者 H5 进程没有按预期接受 remote-debugging 参数。

## 记录结果

人工验证后，把结果复制到 `reports/` 目录下的新文件中。模板见：

```text
h5-webview-debugger/reports/manual-check-template.md
```

目标 URL 的普通浏览器取证记录保留在：

```text
h5-url-debug/report.md
```
