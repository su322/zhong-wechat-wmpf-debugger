# Third-Party Components

This project contains or is derived from the following upstream work.

## 1. WeChatOpenDevTools-Python

- Upstream: `JaveleyQAQ/WeChatOpenDevTools-Python`
- URL: <https://github.com/JaveleyQAQ/WeChatOpenDevTools-Python>
- Role here: original Python project base and legacy workflow inspiration

Important note:

- The upstream repository does not appear to include a clear top-level license file in the checked public tree.
- If you plan to publish this fork publicly, verify upstream licensing status yourself before claiming an overall repository license.

## 2. WMPFDebugger

- Upstream: `evi0s/WMPFDebugger`
- URL: <https://github.com/evi0s/WMPFDebugger>
- Observed upstream package license: `GPL-2.0-only`
- Role here: bundled WMPF bridge logic and Frida configuration for modern runtimes

Files derived from or based on that upstream are located under:

- `vendor/wmpfdebugger/`

## 3. Tencent-derived remote debug files

The bundled WMPF debugger upstream explicitly states that code in:

- `vendor/wmpfdebugger/src/third-party/`

is extracted from `wechatdevtools` and is copyrighted by Tencent Holdings Ltd.

That provenance should be reviewed carefully before any public redistribution strategy is finalized.

## 4. npm dependencies

Runtime bridge dependencies are installed into:

- `vendor/wmpfdebugger/node_modules/`

Those files are ignored by `.gitignore` and should not be committed for a clean public repository.

## Recommendation

Before making the repository public, review:

1. upstream licensing status of the original Python base
2. GPL obligations from the bundled WMPFDebugger code
3. redistribution implications of the Tencent-derived files in `vendor/wmpfdebugger/src/third-party/`
