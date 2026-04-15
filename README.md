# Zhong WeChat Miniapp F12 Enabler

[中文说明](README.zh-CN.md)

Force-enable F12 style debugging for Windows WeChat miniapps, with support for both legacy Python/Frida workflows and modern WMPF `4.x` runtimes.

![DevTools Preview](docs/images/demo2.png)

## What This Is

This project is a **WeChat miniapp F12 enabler** for Windows.

It is designed to:

- detect the current WeChat miniapp runtime
- tell you whether the runtime is supported
- start the local bridge required for modern WeChat `4.x` miniapp debugging
- keep older legacy support paths available where possible

## Current Verified Version

Verified working with:

- WeChat `4.1.8`
- WMPF `19481`

![Version Preview](docs/images/version.png)

Official WeChat download entry:

- <https://pc.weixin.qq.com/>

The official WeChat installer is **not** distributed with this repository.

## Highlights

- `python main.py --check` to verify whether the current runtime is supported
- `python main.py -x` to start miniapp debugging
- automatic handling for WMPF runtime reconnects
- current verified support for the latest tested `4.1.8 / 19481` runtime path

## Requirements

- Windows
- Python 3.10+
- Node.js
- A runnable WeChat miniapp window

Install Python dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### Step 1. Check support first

```bash
python main.py --check
```

Example output:

```text
当前 WMPF 版本 19481：支持
```

### Step 2. Start the local debugging bridge

```bash
python main.py -x
```

When startup succeeds, the tool prints a `devtools://...` URL.

### Step 3. Open the target miniapp in WeChat

Recommended order:

1. Start the script
2. Open the miniapp in WeChat
3. Wait until the miniapp page is actually loaded
4. Open the printed `devtools://...` URL in a Chromium-based browser

### Step 4. Open the DevTools page in the browser

Use the printed URL, for example:

```text
devtools://devtools/bundled/inspector.html?ws=127.0.0.1:62000
```

![Debug Page Preview](docs/images/image1.png)

## Recommended Usage Order

The recommended order is:

1. Run `python main.py --check`
2. Run `python main.py -x`
3. Open the target miniapp in WeChat
4. Open the printed DevTools URL in the browser

This order is the most stable one for WMPF runtimes.

## If The Browser Opens But Does Not Enter Debugging

If the DevTools page opens but does not show the current miniapp session:

1. Make sure the miniapp is already open and the page is loaded in WeChat
2. Refresh the DevTools page once
3. If it is still empty, close the browser DevTools tab and open the printed URL again
4. If it still does not attach, stop the current script process and run `python main.py -x` again

If ports `9421` or `62000` are already occupied, close the old bridge process first, then restart the script.

## Commands

- `python main.py --check`
  Check whether the currently running runtime is supported.
- `python main.py -x`
  Start the miniapp debugging flow.
- `python main.py -c`
  Start the embedded browser debugging flow.
- `python main.py -all`
  Run both startup flows.

## Support Model

Support is determined by the detected `RadiumWMPF/<version>` runtime, not just by the visible WeChat app version.

When WeChat updates to a new WMPF build, a new address file may be required.

The fastest way to verify support is always:

```bash
python main.py --check
```

## Project Structure

- [main.py](main.py)
- [utils/wechatutils.py](utils/wechatutils.py)
- [utils/commons.py](utils/commons.py)
- [utils/wmpfdebugger.py](utils/wmpfdebugger.py)
- [vendor/wmpfdebugger](vendor/wmpfdebugger)

## Additional Notes

- Public release notes: [PUBLIC_RELEASE.md](PUBLIC_RELEASE.md)
- Third-party notice: [THIRD_PARTY.md](THIRD_PARTY.md)

## Disclaimer

This project is not affiliated with Tencent or WeChat.

Use it only in environments and scenarios you are responsible for.
