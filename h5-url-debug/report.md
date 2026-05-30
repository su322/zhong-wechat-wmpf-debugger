# H5 URL 调试报告

## 测试范围

- 目标 URL：`http://banaa.zongshen165.cn/pubhw/authormain?adminid=1d4674b8a6944a4084fad468aeff32b5_hw&svapid=wxf352a1aeb850f5fd`
- 测试方式：普通桌面浏览器访问，记录页面跳转、页面文本、console、network。
- 不做的事情：不绕过微信限制、不伪造微信登录、不复用登录态。

## 初始观察

用户截图显示普通浏览器打开后进入：

```text
buoeeaab.fmvxb.cn/pubhw/tipspub
```

页面顶部显示：

```text
请在微信APP里打开页面
```

## 浏览器测试记录

- 使用普通桌面浏览器打开原始 URL。
- 原始 HTTP 域名跳转到 HTTPS 域名：

```text
https://buoeeaab.fmvvxb.cn/pubhw/authormain?adminid=1d4674b8a6944a4084fad468aeff32b5_hw&svapid=wxf352a1aeb850f5fd&time=1777566321633
```

- 页面随后进入提示页：

```text
https://buoeeaab.fmvvxb.cn/pubhw/tipspub
```

- 页面可见文本：

```text
请在微信APP里打开页面
返回
```

- 页面脚本：
  - `http://res.wx.qq.com/open/js/jweixin-1.4.0.js`
  - `https://buoeeaab.fmvvxb.cn/pubhw/static8/js/app.4e8fe4a5.js`
  - `https://buoeeaab.fmvvxb.cn/pubhw/static8/js/main.465839fd.js`
- 页面存储键名观察：
  - `localStorage`: `appid`
  - `sessionStorage`: `readerAdminid`

## 控制台记录

- 普通浏览器 console 只看到 Mixed Content 错误：

```text
The page was loaded over HTTPS, but requested an insecure script 'http://res.wx.qq.com/open/js/jweixin-1.4.0.js'. This request has been blocked; the content must be served over HTTPS.
```

- 未发现能在普通浏览器 console 里直接进入真实页面或打开微信登录态页面的可用调试入口。
- 当前看到的是非微信环境下的提示页状态，不是微信内置浏览器真实运行态。

## 网络请求记录

- 普通浏览器请求的 UA：

```text
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36
```

- `jweixin-1.4.0.js` 使用 HTTP 地址，在 HTTPS 页面下被浏览器拦截。
- 页面加载期间能看到大量 `static8/css` 和 `static8/js` 前端构建资源请求。
- 页面加载期间出现接口请求，例如：
  - `https://bpiil.zhishijingling.com/hongliaowang/fsb/glBook/advanceInfo`
  - `https://bpiil.zhishijingling.com/hongliaowang/fsb/admin/getTik`
- 没有记录或复用任何响应体中的敏感字段。
- 对两个主 JS 文件做了关键词级检查：
  - `app.4e8fe4a5.js` 包含 `weixin`、`tipspub`、`userAgent`、`navigator`、`wx.`、`authormain` 等关键词。
  - `main.465839fd.js` 包含 `userAgent`、`navigator` 等关键词。
- 以上说明普通浏览器下很可能由前端运行环境检测或页面路由逻辑进入 `tipspub` 提示页。未在报告中记录可用于绕过限制的具体代码。

## 静态线索

只做关键词级分析，未保存完整混淆源码，未记录可用于绕过限制的具体分支代码。

### 主前端包

- `https://buoeeaab.fmvvxb.cn/pubhw/static8/js/app.4e8fe4a5.js`
  - 大小约 `656605` 字符。
  - 未发现 `sourceMappingURL`，说明线上包没有公开 sourcemap。
  - 命中关键词：
    - `MicroMessenger` / `micromessenger`
    - `WeChat`
    - `weixin`
    - `wx.`
    - `jweixin`
    - `tipspub`
    - `/tipspub`
    - `authormain`
    - `/authormain`
    - `userAgent`
    - `navigator`
    - `openid`
    - `appid`
    - `svapid`
    - `adminid`
    - `oauth`
    - `connect/oauth2/authorize`
  - 未命中 `vConsole`、`eruda`，未看到内置移动端调试面板。

- `https://buoeeaab.fmvvxb.cn/pubhw/static8/js/main.465839fd.js`
  - 大小约 `101806` 字符。
  - 未发现 `sourceMappingURL`。
  - 命中 `userAgent`、`navigator`、`code` 等通用关键词。

### 路由和接口类型

主前端包中能看到以下类型的路径，说明这是完整 H5 应用包，不只是提示页：

- 页面/业务路由：`/mainLiao`、`/fabrication`、`/center`、`/authormain`、`/tipspub`
- 用户/作者相关：`/admin/getOauth`、`/admin/getAdminInfo`、`/admin/getAdminInfoLogin`、`/admin/getAutorInfo`
- 内容相关：`/glBook/list`、`/glBook/pubDetail`、`/glBook/detailLiao`、`/glBook/advanceInfo`
- 支付/订单相关：`/hwPay/wxPay`、`/order/getOrderNo`
- 微信登录/授权相关：`https://open.weixin.qq.com/connect/oauth2/authorize?...`

这些线索说明页面依赖微信网页授权和微信运行环境。普通浏览器里只能看到被重定向后的提示页状态，无法自然得到微信内置浏览器里的登录态和完整页面 console。

## 结论

- 该 URL 是微信内置浏览器 H5 页面，不是当前项目支持的小程序/WMPF 调试对象。
- 普通桌面浏览器可以看到提示页的 console 和 network，但看不到微信内真实登录后的页面控制台。
- 当前证据显示页面有前端环境检测和提示页路由，普通浏览器最终停在 `tipspub`。
- 线上 JS 没有 sourcemap，也没有内置 `vConsole` / `eruda` 调试入口。
- 关键线索是 `MicroMessenger` / `userAgent` / `navigator` / `tipspub` / 微信 OAuth / `jweixin`，说明限制主要围绕微信内置浏览器环境和网页授权。
- 不建议把这件事描述成“破解只能微信打开”。如果这是客户自己的系统，应由客户在页面源代码中加入授权调试入口。

## 合规调试建议

如果这是客户自己的 H5 页面，可以由页面开发方加入受控调试入口：

- 测试环境或测试域名自动加载 `vConsole` / `eruda`。
- 生产环境只对白名单账号或后台开关加载调试面板。
- 日志只保留必要字段，避免输出用户 token、openid、手机号等敏感信息。
