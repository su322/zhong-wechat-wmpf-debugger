import importlib.util
import sys
import unittest
from pathlib import Path

from utils.commons import build_h5_debug_spawn_argv


MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "h5-webview-debugger"
    / "check_h5_debug.py"
)
SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "h5-webview-debugger"
    / "run_h5_debug.ps1"
)
WECHATWIN_HOOK_PATH = (
    Path(__file__).resolve().parent.parent
    / "scripts"
    / "WechatWin.dll"
    / "hook.js"
)
COMMONS_PATH = Path(__file__).resolve().parent.parent / "utils" / "commons.py"


def load_h5_debug_module():
    spec = importlib.util.spec_from_file_location("h5_webview_check", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class H5WebviewDebuggerTests(unittest.TestCase):
    def setUp(self):
        self.module = load_h5_debug_module()

    def test_detects_enabled_xweb_inspect_flag(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1001,
                    "name": "WeChatAppEx.exe",
                    "cmdline": [
                        r"C:\Tencent\WeChatAppEx.exe",
                        "--log-level=0",
                        "--xweb-enable-inspect=1",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.status, "enabled")
        self.assertTrue(summaries.has_wechat_process)
        self.assertTrue(summaries.has_inspect_flag)
        self.assertIn("--xweb-enable-inspect=1", summaries.processes[0].matched_flags)

    def test_extracts_remote_debugging_port_value(self):
        self.assertEqual(
            self.module.find_remote_debugging_ports(
                [
                    r"D:\Tencent\weixin\Weixin.exe",
                    "--type=wxpublic",
                    "--remote-debugging-port=9222",
                ]
            ),
            [9222],
        )

    def test_prints_remote_debugging_port_probe_status(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1005,
                    "name": "Weixin.exe",
                    "cmdline": [
                        r"D:\Tencent\weixin\Weixin.exe",
                        "--type=wxpublic",
                        "--remote-debugging-port=9222",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.remote_debugging_ports, [9222])

    def test_reports_wechat_process_without_inspect_flag_as_disabled(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1002,
                    "name": "WeChatAppEx.exe",
                    "cmdline": [
                        r"C:\Tencent\WeChatAppEx.exe",
                        "--log-level=2",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.status, "disabled")
        self.assertTrue(summaries.has_wechat_process)
        self.assertFalse(summaries.has_inspect_flag)

    def test_reports_h5_status_not_opened_when_only_wmpf_inspect_exists(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1006,
                    "name": "WeChatAppEx.exe",
                    "cmdline": [
                        r"C:\Tencent\WeChatAppEx.exe",
                        "--xweb-enable-inspect=1",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.status, "enabled")
        self.assertEqual(summaries.h5_status, "not_opened")

    def test_reports_h5_status_partial_for_dynamic_or_incomplete_wxpublic_flags(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1007,
                    "name": "Weixin.exe",
                    "cmdline": [
                        r"D:\Tencent\weixin\Weixin.exe",
                        "--type=wxpublic",
                        "--remote-debugging-port=0",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.h5_status, "partial")

    def test_reports_h5_status_ready_for_fixed_port_wxpublic_inspect_flags(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1008,
                    "name": "Weixin.exe",
                    "cmdline": [
                        r"D:\Tencent\weixin\Weixin.exe",
                        "--type=wxpublic",
                        "--xweb-enable-inspect=1",
                        "--remote-debugging-port=9222",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.h5_status, "ready")
        self.assertEqual(summaries.remote_debugging_ports, [9222])

    def test_reports_h5_status_ready_for_top_level_wechatappex_window_host(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1009,
                    "name": "WeChatAppEx.exe",
                    "cmdline": [
                        r"C:\Users\me\AppData\Roaming\Tencent\xwechat\xplugin\plugins\RadiumWMPF\19481\extracted\runtime\WeChatAppEx.exe",
                        "--xweb-enable-inspect=1",
                        "--helper-handle-value=898255489",
                        "--remote-debugging-port=9222",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.h5_status, "ready")
        self.assertEqual(summaries.remote_debugging_ports, [9222])

    def test_detects_new_weixin_process_name(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1004,
                    "name": "Weixin.exe",
                    "cmdline": [
                        r"D:\Tencent\weixin\Weixin.exe",
                        "--user-lib-dir=D:\\Tencent\\weixin\\4.1.8.133",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.status, "disabled")
        self.assertTrue(summaries.has_wechat_process)

    def test_reports_missing_wechat_processes(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 2001,
                    "name": "chrome.exe",
                    "cmdline": ["chrome.exe"],
                }
            ]
        )

        self.assertEqual(summaries.status, "not_found")
        self.assertFalse(summaries.has_wechat_process)
        self.assertEqual(summaries.processes, [])

    def test_ignores_non_wechat_processes_with_xwechat_paths(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 2002,
                    "name": "crashpad_handler.exe",
                    "cmdline": [
                        r"D:\Tencent\weixin\4.1.8.133\crashpad_handler.exe",
                        r"--database=C:\Users\me\AppData\Roaming\Tencent\xwechat\crashinfo",
                    ],
                }
            ]
        )

        self.assertEqual(summaries.status, "not_found")
        self.assertFalse(summaries.has_wechat_process)
        self.assertEqual(summaries.processes, [])

    def test_reports_unknown_when_process_cmdline_is_unreadable(self):
        summaries = self.module.analyze_processes(
            [
                {
                    "pid": 1003,
                    "name": "WeChat.exe",
                    "cmdline": None,
                    "error": "AccessDenied",
                }
            ]
        )

        self.assertEqual(summaries.status, "unknown")
        self.assertTrue(summaries.has_wechat_process)
        self.assertFalse(summaries.has_inspect_flag)
        self.assertEqual(summaries.processes[0].error, "AccessDenied")

    def test_launcher_stops_when_main_script_fails(self):
        script = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("$LASTEXITCODE", script)
        self.assertIn("exit $LASTEXITCODE", script)

    def test_launcher_checks_new_weixin_process_name(self):
        script = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("Weixin", script)

    def test_launcher_tells_user_to_open_page_before_ending_hook(self):
        script = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("Do not press Enter", script)
        self.assertIn("127.0.0.1:9222/json/list", script)

    def test_launcher_checks_fixed_devtools_port_before_starting_wechat(self):
        script = SCRIPT_PATH.read_text(encoding="utf-8")

        self.assertIn("$devtoolsPort = 9222", script)
        self.assertIn("Get-NetTCPConnection", script)
        self.assertIn("already in use", script)

    def test_main_weixin_spawn_argv_includes_h5_devtools_flags(self):
        argv = build_h5_debug_spawn_argv(r"D:\Tencent\weixin\Weixin.exe")

        self.assertEqual(argv[0], r"D:\Tencent\weixin\Weixin.exe")
        self.assertIn("--xweb-enable-inspect=1", argv)
        self.assertIn("--remote-debugging-port=9222", argv)
        self.assertIn("--remote-debugging-address=127.0.0.1", argv)
        self.assertIn("--remote-allow-origins=*", argv)

    def test_commons_spawns_weixin_with_h5_debug_argv(self):
        source = COMMONS_PATH.read_text(encoding="utf-8")

        self.assertIn("build_h5_debug_spawn_argv(path)", source)
        self.assertNotIn("device.spawn(path)", source)

    def test_wechatwin_hook_uses_frida_export_api_compatible_with_current_runtime(self):
        script = WECHATWIN_HOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("Module.getGlobalExportByName", script)
        self.assertNotIn("Module.findExportByName(\"kernel32.dll\", \"CreateProcessW\")", script)

    def test_wechatwin_hook_avoids_replace_all_for_frida_runtime_compatibility(self):
        script = WECHATWIN_HOOK_PATH.read_text(encoding="utf-8")

        self.assertNotIn(".replaceAll(", script)
        self.assertIn(".replace(/--log-level=2/g", script)

    def test_wechatwin_hook_allocates_rewritten_command_line(self):
        script = WECHATWIN_HOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("Memory.allocUtf16String", script)
        self.assertIn("args[1] =", script)
        self.assertNotIn("writeUtf16String(aaa)", script)

    def test_wechatwin_hook_injects_inspect_for_wxpublic_processes(self):
        script = WECHATWIN_HOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("wxpublic", script)
        self.assertIn("--xweb-enable-inspect=1", script)
        self.assertIn("--remote-debugging-port=9222", script)
        self.assertIn("--remote-debugging-address=127.0.0.1", script)
        self.assertIn("--remote-allow-origins=*", script)
        self.assertNotIn("--remote-debugging-port=0", script)

    def test_wechatwin_hook_injects_remote_debugging_for_top_level_wechatappex(self):
        script = WECHATWIN_HOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("isTopLevelWeChatAppEx", script)
        self.assertIn("WeChatAppEx.exe", script)
        self.assertIn("--helper-handle-value", script)
        self.assertIn("--remote-debugging-port=9222", script)

    def test_commons_keeps_wechat_browser_hook_until_user_confirms(self):
        source = COMMONS_PATH.read_text(encoding="utf-8")

        self.assertIn("input(", source)
        self.assertNotIn("time.sleep(10)", source)

    def test_commons_prints_h5_devtools_endpoint_while_hook_is_active(self):
        source = COMMONS_PATH.read_text(encoding="utf-8")

        self.assertIn("http://127.0.0.1:9222/json/list", source)
        self.assertIn("F12", source)


if __name__ == "__main__":
    unittest.main()
