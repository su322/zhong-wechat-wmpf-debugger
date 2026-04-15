# WeChat 4.x WMPF Debugger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `python main.py -x` support modern WeChat 4.x miniapp runtimes by detecting WMPF bundles and starting a remote-debug bridge, while preserving the legacy 3.x path.

**Architecture:** Extend runtime detection to distinguish legacy and WMPF processes, keep the existing legacy injector unchanged, and add a separate WMPF bridge launcher that reuses bundled remote-debug assets. The CLI remains stable and only the internal execution path changes.

**Tech Stack:** Python 3, `unittest`, Frida, psutil, Node.js, bundled WMPFDebugger assets

---

### Task 1: Add runtime classification tests

**Files:**
- Create: `tests/test_wechatutils.py`
- Modify: `utils/wechatutils.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from utils.wechatutils import WechatUtils


class RuntimeDetectionTests(unittest.TestCase):
    def test_extracts_legacy_version_from_cmdline(self):
        utils = WechatUtils()
        version = utils.extract_legacy_version_number(
            [
                "C:\\\\WeChatAppEx.exe",
                "--foo=bar",
                '{"version":9129}',
            ]
        )
        self.assertEqual(version, 9129)

    def test_extracts_wmpf_version_from_runtime_path(self):
        utils = WechatUtils()
        version = utils.extract_wmpf_version_from_path(
            "C:\\\\Users\\\\me\\\\AppData\\\\Roaming\\\\Tencent\\\\xwechat\\\\xplugin\\\\plugins\\\\RadiumWMPF\\\\19027\\\\extracted\\\\runtime\\\\WeChatAppEx.exe"
        )
        self.assertEqual(version, 19027)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_wechatutils -v`
Expected: FAIL with missing methods such as `extract_legacy_version_number`

- [ ] **Step 3: Write minimal implementation**

```python
def extract_legacy_version_number(self, cmdline):
    text = " ".join(cmdline)
    match = re.search(r'"version":(\d+)', text)
    return int(match.group(1)) if match else None

def extract_wmpf_version_from_path(self, process_path):
    match = re.search(r"RadiumWMPF[\\\\/](\d+)[\\\\/]", process_path or "")
    return int(match.group(1)) if match else None
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_wechatutils -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wechatutils.py utils/wechatutils.py
git commit -m "test: cover runtime version parsing"
```

### Task 2: Add runtime mode selection tests

**Files:**
- Modify: `tests/test_wechatutils.py`
- Modify: `utils/wechatutils.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_classifies_wmpf_runtime(self):
        utils = WechatUtils()
        runtime = utils.build_runtime_info(
            pid=1234,
            process_path="C:\\\\Users\\\\me\\\\AppData\\\\Roaming\\\\Tencent\\\\xwechat\\\\xplugin\\\\plugins\\\\RadiumWMPF\\\\19027\\\\extracted\\\\runtime\\\\WeChatAppEx.exe",
            cmdline=[
                "C:\\\\Users\\\\me\\\\AppData\\\\Roaming\\\\Tencent\\\\xwechat\\\\xplugin\\\\plugins\\\\RadiumWMPF\\\\19027\\\\extracted\\\\runtime\\\\WeChatAppEx.exe",
                "--client_version=4065597243",
            ],
        )
        self.assertEqual(runtime["mode"], "wmpf")
        self.assertEqual(runtime["version"], 19027)

    def test_classifies_legacy_runtime(self):
        utils = WechatUtils()
        runtime = utils.build_runtime_info(
            pid=5678,
            process_path="C:\\\\legacy\\\\WeChatAppEx.exe",
            cmdline=["C:\\\\legacy\\\\WeChatAppEx.exe", '{"version":9129}'],
        )
        self.assertEqual(runtime["mode"], "legacy")
        self.assertEqual(runtime["version"], 9129)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_wechatutils -v`
Expected: FAIL with missing `build_runtime_info`

- [ ] **Step 3: Write minimal implementation**

```python
def build_runtime_info(self, pid, process_path, cmdline):
    wmpf_version = self.extract_wmpf_version_from_path(process_path)
    if wmpf_version:
        return {
            "pid": pid,
            "mode": "wmpf",
            "version": wmpf_version,
            "path": process_path,
            "cmdline": cmdline,
        }

    legacy_version = self.extract_legacy_version_number(cmdline)
    return {
        "pid": pid,
        "mode": "legacy",
        "version": legacy_version,
        "path": process_path,
        "cmdline": cmdline,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_wechatutils -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wechatutils.py utils/wechatutils.py
git commit -m "test: classify legacy and wmpf runtimes"
```

### Task 3: Add WMPF bridge launcher tests

**Files:**
- Create: `tests/test_wmpfdebugger.py`
- Create: `utils/wmpfdebugger.py`

- [ ] **Step 1: Write the failing test**

```python
import unittest

from utils.wmpfdebugger import build_wmpf_bridge_command


class WMPFBridgeCommandTests(unittest.TestCase):
    def test_builds_expected_node_command(self):
        command = build_wmpf_bridge_command(
            vendor_root="D:\\\\repo\\\\vendor\\\\wmpfdebugger",
            debug_port=9421,
            cdp_port=62000,
        )
        self.assertEqual(
            command,
            [
                "node",
                "src/index.js",
                "--debug-port",
                "9421",
                "--cdp-port",
                "62000",
            ],
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_wmpfdebugger -v`
Expected: FAIL with missing module or function

- [ ] **Step 3: Write minimal implementation**

```python
def build_wmpf_bridge_command(vendor_root, debug_port, cdp_port):
    return [
        "node",
        "src/index.js",
        "--debug-port",
        str(debug_port),
        "--cdp-port",
        str(cdp_port),
    ]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_wmpfdebugger -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_wmpfdebugger.py utils/wmpfdebugger.py
git commit -m "test: cover wmpf bridge command generation"
```

### Task 4: Implement WMPF runtime discovery and selection

**Files:**
- Modify: `utils/wechatutils.py`

- [ ] **Step 1: Write the failing test**

```python
    def test_filters_supported_wmpf_runtime_by_available_config(self):
        utils = WechatUtils()
        runtime = {
            "pid": 1234,
            "mode": "wmpf",
            "version": 19027,
            "path": "C:\\\\Users\\\\me\\\\AppData\\\\Roaming\\\\Tencent\\\\xwechat\\\\xplugin\\\\plugins\\\\RadiumWMPF\\\\19027\\\\extracted\\\\runtime\\\\WeChatAppEx.exe",
            "cmdline": [],
        }
        self.assertTrue(utils.is_supported_runtime(runtime, {19027}))
        self.assertFalse(utils.is_supported_runtime(runtime, {19201}))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_wechatutils -v`
Expected: FAIL with missing `is_supported_runtime`

- [ ] **Step 3: Write minimal implementation**

```python
def is_supported_runtime(self, runtime, supported_versions):
    return runtime.get("version") in supported_versions
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m unittest tests.test_wechatutils -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add utils/wechatutils.py tests/test_wechatutils.py
git commit -m "feat: add supported runtime checks"
```

### Task 5: Bundle WMPF debugger assets

**Files:**
- Create: `vendor/wmpfdebugger/package.json`
- Create: `vendor/wmpfdebugger/src/index.js`
- Create: `vendor/wmpfdebugger/src/cli.js`
- Create: `vendor/wmpfdebugger/src/logger.js`
- Create: `vendor/wmpfdebugger/src/third-party/RemoteDebugCodex.js`
- Create: `vendor/wmpfdebugger/src/third-party/RemoteDebugConstants.js`
- Create: `vendor/wmpfdebugger/src/third-party/RemoteDebugUtils.js`
- Create: `vendor/wmpfdebugger/src/third-party/WARemoteDebugProtobuf.js`
- Create: `vendor/wmpfdebugger/frida/hook.js`
- Create: `vendor/wmpfdebugger/frida/config/addresses.19027.json`
- Create: `vendor/wmpfdebugger/LICENSE`

- [ ] **Step 1: Copy the required runtime assets**

Copy the proven upstream bridge assets into `vendor/wmpfdebugger/` and keep the version config for `19027`.

- [ ] **Step 2: Run a smoke check on the vendor tree**

Run: `python - <<'PY'\nfrom pathlib import Path\nrequired = [\n    Path('vendor/wmpfdebugger/src/index.js'),\n    Path('vendor/wmpfdebugger/frida/hook.js'),\n    Path('vendor/wmpfdebugger/frida/config/addresses.19027.json'),\n]\nfor item in required:\n    assert item.exists(), item\nprint('vendor assets ready')\nPY`
Expected: `vendor assets ready`

- [ ] **Step 3: Commit**

```bash
git add vendor/wmpfdebugger
git commit -m "feat: vendor wmpf debugger assets"
```

### Task 6: Implement the Python WMPF bridge launcher

**Files:**
- Modify: `utils/wmpfdebugger.py`
- Modify: `requirements.txt`

- [ ] **Step 1: Write the failing test**

```python
    def test_missing_node_modules_requires_bootstrap(self):
        from utils.wmpfdebugger import node_modules_ready

        self.assertFalse(
            node_modules_ready("D:\\\\repo\\\\vendor\\\\wmpfdebugger")
        )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_wmpfdebugger -v`
Expected: FAIL with missing `node_modules_ready`

- [ ] **Step 3: Write minimal implementation**

```python
from pathlib import Path

def node_modules_ready(vendor_root):
    return Path(vendor_root, "node_modules", "frida").exists()
```

- [ ] **Step 4: Expand to the full launcher**

Implement:

```python
def ensure_wmpf_dependencies(vendor_root):
    if node_modules_ready(vendor_root):
        return
    subprocess.run(
        ["npm.cmd", "install", "--no-fund", "--no-audit"],
        cwd=vendor_root,
        check=True,
    )

def launch_wmpf_bridge(vendor_root, debug_port=9421, cdp_port=62000):
    ensure_wmpf_dependencies(vendor_root)
    command = build_wmpf_bridge_command(vendor_root, debug_port, cdp_port)
    return subprocess.Popen(
        command,
        cwd=vendor_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m unittest tests.test_wmpfdebugger -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add utils/wmpfdebugger.py tests/test_wmpfdebugger.py requirements.txt
git commit -m "feat: add wmpf bridge launcher"
```

### Task 7: Wire the WMPF path into the CLI

**Files:**
- Modify: `utils/commons.py`
- Modify: `main.py`

- [ ] **Step 1: Write the failing test**

Add a testable helper in `utils/commons.py`:

```python
def choose_debug_mode(runtime):
    return runtime["mode"]
```

Then verify:

```python
import unittest

from utils.commons import choose_debug_mode


class CommonsModeTests(unittest.TestCase):
    def test_choose_debug_mode_returns_wmpf(self):
        self.assertEqual(choose_debug_mode({"mode": "wmpf"}), "wmpf")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m unittest tests.test_wmpfdebugger -v`
Expected: FAIL with missing helper

- [ ] **Step 3: Write minimal implementation**

```python
def choose_debug_mode(runtime):
    return runtime["mode"]
```

- [ ] **Step 4: Expand to the full flow**

Inside `load_wechatEx_configs()`:

```python
runtime = self.wechatutils_instance.get_preferred_runtime()
if runtime and runtime["mode"] == "wmpf":
    process = launch_wmpf_bridge(self.wechatutils_instance.get_wmpf_vendor_path())
    self.stream_bridge_output(process)
    return
```

Keep the old legacy injection branch as the fallback.

- [ ] **Step 5: Run targeted tests**

Run: `python -m unittest tests.test_wechatutils tests.test_wmpfdebugger -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add utils/commons.py main.py tests/test_wechatutils.py tests/test_wmpfdebugger.py
git commit -m "feat: route main entrypoint to wmpf debugger on 4.x"
```

### Task 8: Verify end-to-end behavior

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document the new runtime split**

Add a short note in `README.md` that:

- legacy 3.x versions still use the old path
- 4.x WMPF versions use the remote-debug bridge
- Node.js is required for the 4.x path

- [ ] **Step 2: Run automated verification**

Run: `python -m unittest tests.test_wechatutils tests.test_wmpfdebugger -v`
Expected: PASS

- [ ] **Step 3: Run a local smoke check**

Run: `python main.py -x`
Expected: for WMPF `19027`, print a DevTools websocket URL instead of the old unsupported-version error

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: describe legacy and wmpf debugger flows"
```
