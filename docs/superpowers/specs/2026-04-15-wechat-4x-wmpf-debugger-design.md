# WeChat 4.x WMPF Debugger Design

## Goal

Keep `python main.py -x` as the user entrypoint, but make it work on modern WeChat 4.x miniapp runtimes by detecting the WMPF runtime version and switching from the legacy in-process F12 patch to a remote-debug bridge workflow.

## Problem Summary

The existing project only supports the legacy 3.x path:

- it detects miniapp runtimes by scanning for `"version":<number>` inside `WeChatAppEx.exe` command lines
- it maps that value to `configs/address_<version>_x64.json`
- it injects a Frida script that patches old `WeChatAppEx.exe` offsets

Modern WeChat 4.x changed all three assumptions:

- runtime processes expose `--client_version=<int>` instead of the old `"version":<number>` payload
- the runtime version that matters is the `RadiumWMPF/<version>` bundle version, such as `19027`
- the hook target moved to `flue.dll` for modern WMPF versions

Because of that, the current tool fails before injection and cannot support 4.x by adding one more legacy config file.

## Chosen Approach

Implement a dual-path debugger:

- Legacy path: keep the current 3.x behavior unchanged for old versions already supported by `configs/address_*_x64.json`
- WMPF 4.x path: detect `RadiumWMPF/<version>` runtimes, then launch a local remote-debug bridge based on the known `WMPFDebugger` workflow

The 4.x path will:

1. detect the active WMPF runtime version from the `WeChatAppEx.exe` path
2. check whether a remote-debug Frida config exists for that WMPF version
3. ensure the bundled Node-based bridge dependencies are installed
4. launch the local bridge process
5. print the Chrome DevTools URL for the user

## Architecture

### 1. Runtime Detection Layer

Extend `utils/wechatutils.py` so it can classify active runtimes into:

- `legacy`: old command line contains `"version":<number>` and matches an existing legacy config
- `wmpf`: path contains `RadiumWMPF/<version>/.../WeChatAppEx.exe`

The detection layer should expose structured runtime metadata instead of only `(pid, version)` tuples.

### 2. Legacy Injector Layer

Leave the current Frida injection flow in `utils/commons.py` intact for old runtimes. This avoids unnecessary risk for versions that already work.

### 3. WMPF Remote-Debug Layer

Add a new Python module responsible for:

- locating the bundled WMPF debugger assets
- checking `node` availability
- installing required Node packages on first use
- starting the bridge subprocess with the right working directory
- relaying stdout/stderr back to the user

The actual bridge logic will reuse the proven WMPFDebugger layout and offsets for 4.x runtimes, including `19027`.

### 4. Bundled Assets

Bundle the minimal WMPF debugger asset set inside this repo:

- Frida hook script
- WMPF address configs
- runtime Node sources required to start the bridge
- license file for the bundled upstream assets

This avoids making the tool depend on cloning another repo at runtime.

## User Experience

For `python main.py -x`:

- if a legacy runtime is detected, behavior stays the same
- if a WMPF runtime is detected, the tool starts the remote-debug bridge and prints a message like:
  - detected WMPF version
  - local debug server status
  - DevTools URL such as `devtools://devtools/bundled/inspector.html?ws=127.0.0.1:62000`

The user still opens the miniapp first and then opens the printed DevTools URL, matching the supported upstream workflow.

## Error Handling

The 4.x path must fail with actionable messages for:

- `node` missing
- dependency install failure
- unsupported WMPF version
- Frida attach failure
- bridge process exit

These errors must not be reported as the old misleading "wechat process not found or unsupported version" message.

## Testing Strategy

Add regression tests for:

- legacy version parsing still works
- WMPF version parsing from runtime path
- runtime-mode selection prefers WMPF when modern metadata is present
- unsupported WMPF versions produce a targeted error
- the bridge command builder uses the bundled assets and expected ports

The tests do not need to attach to a real WeChat process; they only need to validate detection and orchestration logic.

## Scope Boundaries

In scope:

- make `main.py -x` usable on WeChat 4.x WMPF runtimes
- keep legacy behavior
- add `19027` support through the remote-debug path

Out of scope:

- reimplement the WMPF remote-debug protocol in native Python
- redesign the CLI
- add new browser automation flows
- support all future WMPF versions automatically without config files

## Risks

- First-run dependency install adds latency
- Frida attach behavior on some WeChat builds may still be fragile
- `devtools://` URLs depend on a Chromium-based browser on the machine

These are acceptable because they are already part of the public upstream WMPFDebugger workflow and are materially more realistic than trying to preserve the obsolete old F12 patch model on 4.x.
