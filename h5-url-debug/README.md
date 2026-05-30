# H5 URL 普通浏览器调试记录

目标 URL：

```text
http://banaa.zongshen165.cn/pubhw/authormain?adminid=1d4674b8a6944a4084fad468aeff32b5_hw&svapid=wxf352a1aeb850f5fd
```

本目录用于记录普通浏览器访问该微信站内 H5 页面时的现象、跳转、console 和 network 结果。

## 边界

- 只做普通浏览器下的取证式调试。
- 不伪造微信登录态。
- 不绕过站点“仅微信内打开”的访问限制。
- 不提取或复用用户 Cookie、Token、授权 code。
- 如果该页面属于客户自己维护，推荐在页面源码中加入受控调试模式，例如测试账号或白名单下加载 `vConsole` / `eruda`。

## 当前结论

当前项目的 WMPF 调试能力面向微信小程序运行时，不等同于微信内置浏览器 H5 页面。该 URL 是否可调试，需要单独看 H5 页面的运行环境检测、页面源码和客户是否拥有页面授权。

详细记录见 [report.md](report.md)。
