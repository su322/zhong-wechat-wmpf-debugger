# H5 内置浏览器控制台人工检查记录

## 基本信息

- 检查时间：
- 操作系统：
- PC 微信版本：
- 目标 URL：
- 是否已关闭微信后重新运行 `run_h5_debug.ps1`：
- 是否在终端“Hook 保持中”期间打开 H5 页面：

## 自动诊断输出

```text
粘贴 `python h5-webview-debugger\check_h5_debug.py` 的输出。
```

## inspect 参数检查

- 是否检测到 `--xweb-enable-inspect=1`：
- 是否检测到 `inspect` / `remote-debugging` / `devtools` 相关参数：
- 是否检测到 `--remote-debugging-port=9222`：
- `http://127.0.0.1:9222/json/list` 是否可访问：
- 如果未检测到，微信是否是在脚本启动后打开：

## 控制台入口检查

- H5 页面是否能在 PC 微信内打开：
- 普通浏览器访问 `http://127.0.0.1:9222/json/list` 是否返回 targets：
- targets 中是否有当前 H5 页面 URL：
- targets 中是否包含 `devtoolsFrontendUrl`：
- targets 中是否包含 `webSocketDebuggerUrl`：
- 右键菜单是否有“检查”或 DevTools 入口：
- F12 是否有反应：
- 是否出现独立 DevTools 窗口：
- DevTools 是否能看到 Console：
- DevTools 是否能看到 Network：

## 失败现象

- 页面现象：
- 终端现象：
- 微信进程现象：
- 截图或日志文件路径：

## 结论

- 当前版本是否可用：
- 如果不可用，判断原因：
- 下一步建议：

## 关联记录

- 普通浏览器取证报告：`../../h5-url-debug/report.md`
- 本目录说明：`../README.md`
