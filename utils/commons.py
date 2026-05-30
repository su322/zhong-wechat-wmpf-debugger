from utils.colors import Color
from utils.wechatutils import WechatUtils
from utils.wmpfdebugger import (
    DEFAULT_CDP_PORT,
    DEFAULT_DEBUG_PORT,
    devtools_link,
    launch_wmpf_bridge,
)
import frida
import os
import time
import platform


def choose_debug_mode(runtime):
    return runtime["mode"]


def build_h5_debug_spawn_argv(path):
    return [
        path,
        "--xweb-enable-inspect=1",
        "--remote-debugging-port=9222",
        "--remote-debugging-address=127.0.0.1",
        "--remote-allow-origins=*",
    ]


class Commons:
    def __init__(self):
        self.wechatutils_instance = WechatUtils()
        self.device = None
        self.active_sessions = []

    def get_local_device(self):
        if self.device is None:
            self.device = frida.get_local_device()
        return self.device

    def onMessage(self, message, data):
        if message["type"] == "send":
            print(Color.GREEN + message["payload"], Color.END)
        elif message["type"] == "error":
            print(Color.RED + message["stack"], Color.END)

    def inject_wechatEx(self, pid, code):
        try:
            session = frida.attach(pid)
            script = session.create_script(code)
            script.on("message", self.onMessage)
            script.load()
            print(f"Successfully injected into WeChat PID: {pid}")
            return session
        except Exception as exc:
            print(f"Error injecting into WeChat PID {pid}: {exc}")
            return None

    def inject_wechatDLL(self, path, code):
        device = self.get_local_device()
        pid = device.spawn(build_h5_debug_spawn_argv(path))
        session = frida.attach(pid)
        script = session.create_script(code)
        script.on("message", self.onMessage)
        script.load()
        device.resume(pid)
        print(Color.GREEN + "[+] 微信已启动，Hook 保持中。" + Color.END)
        print(Color.GREEN + "[+] 请现在在 PC 微信内打开目标 H5/公众号页面。" + Color.END)
        print(Color.GREEN + "[+] F12 不一定会生效；打开页面后请访问 http://127.0.0.1:9222/json/list 检查 DevTools 目标。" + Color.END)
        input("打开页面并观察后，按 Enter 结束 Hook 并继续诊断...")
        session.detach()

    def stream_bridge_output(self, process):
        try:
            if process.stdout is None:
                return

            for line in iter(process.stdout.readline, ""):
                if not line:
                    break
                print(line.rstrip())
                if process.poll() is not None and process.stdout.closed:
                    break
        except KeyboardInterrupt:
            print(Color.YELLOW + "[!] Stopping WMPF debug bridge..." + Color.END)
            process.terminate()
        finally:
            return_code = process.poll()
            if return_code not in (None, 0):
                print(Color.RED + f"[-] WMPF debug bridge exited with code {return_code}" + Color.END)

    def load_wmpf_runtime(self, runtime, debug_main=False, debug_frida=False):
        version = runtime["version"]
        client_version = runtime.get("client_version")
        if client_version:
            print(
                Color.GREEN
                + f"[+] Detected WMPF runtime version {version} (client_version={client_version})"
                + Color.END
            )
        else:
            print(Color.GREEN + f"[+] Detected WMPF runtime version {version}" + Color.END)

        bridge_process = launch_wmpf_bridge(
            vendor_root=self.wechatutils_instance.get_wmpf_vendor_path(),
            debug_port=DEFAULT_DEBUG_PORT,
            cdp_port=DEFAULT_CDP_PORT,
            runtime_pid=runtime["pid"],
            runtime_version=runtime["version"],
            debug_main=debug_main,
            debug_frida=debug_frida,
        )
        print(Color.GREEN + f"[+] DevTools URL: {devtools_link(DEFAULT_CDP_PORT)}" + Color.END)
        print(Color.GREEN + "[+] Launch the miniapp first, then open the DevTools URL above." + Color.END)
        self.stream_bridge_output(bridge_process)

    def print_runtime_check_status(self):
        status = self.wechatutils_instance.get_runtime_check_status()
        print(self.wechatutils_instance.format_runtime_check_message(status))

    def load_legacy_runtime(self):
        path = self.wechatutils_instance.get_configs_path()
        wechat_instances = self.wechatutils_instance.get_wechat_pids_and_versions()
        if not wechat_instances:
            return False

        for pid, version in wechat_instances:
            try:
                wechatEx_hookcode = open(
                    os.path.join(path, "..", "scripts", "hook.js"), "r", encoding="utf-8"
                ).read()
                wechatEx_addresses = open(
                    os.path.join(path, f"address_{version}_x64.json")
                ).read()
                wechatEx_hookcode = "var address=" + wechatEx_addresses + wechatEx_hookcode
                session = self.inject_wechatEx(pid, wechatEx_hookcode)
                if session:
                    self.active_sessions.append(session)
                print(f"Injected into WeChat instance PID: {pid}, Version: {version}")
            except Exception as exc:
                print(f"Error injecting into WeChat PID {pid}: {exc}")

        while self.active_sessions:
            self.manage_sessions()
            time.sleep(5)
        return True

    def load_wechatEx_configs(self, debug_main=False, debug_frida=False):
        if get_cpu_architecture() == "MacOS x64":
            wechat_instances = self.wechatutils_instance.get_wechat_pids_and_versions_mac()
            if not wechat_instances:
                self.wechatutils_instance.print_process_not_found_message()
                return

            path = self.wechatutils_instance.get_configs_path()
            for pid, version in wechat_instances:
                try:
                    wechatEx_hookcode = open(
                        os.path.join(path, "..", "scripts", "hook.js"), "r", encoding="utf-8"
                    ).read()
                    wechatEx_addresses = open(
                        os.path.join(path, f"address_{version}_x64.json")
                    ).read()
                    wechatEx_hookcode = "var address=" + wechatEx_addresses + wechatEx_hookcode
                    session = self.inject_wechatEx(pid, wechatEx_hookcode)
                    if session:
                        self.active_sessions.append(session)
                    print(f"Injected into WeChat instance PID: {pid}, Version: {version}")
                except Exception as exc:
                    print(f"Error injecting into WeChat PID {pid}: {exc}")
            return

        runtime = self.wechatutils_instance.get_preferred_runtime()
        if runtime:
            if choose_debug_mode(runtime) == "wmpf":
                self.load_wmpf_runtime(runtime, debug_main=debug_main, debug_frida=debug_frida)
                return

            if self.load_legacy_runtime():
                return

        unsupported_wmpf = self.wechatutils_instance.get_unsupported_wmpf_runtime_infos()
        if unsupported_wmpf:
            self.wechatutils_instance.print_unsupported_wmpf_version_message(unsupported_wmpf)
            return

        self.wechatutils_instance.print_process_not_found_message()

    def load_wechatEXE_configs(self):
        wechat_instances = self.wechatutils_instance.get_wechat_runtime_infos()
        if wechat_instances:
            print(Color.RED + "[-] 请退出所有微信实例后再执行该命令" + Color.END)
            return 0

        wechatEXEpath = self.wechatutils_instance.find_installation_path("微信")
        if not wechatEXEpath:
            return 0
        path = self.wechatutils_instance.get_configs_path()
        wechatEXE_hookcode = open(
            os.path.join(path, "..", "scripts", "WechatWin.dll", "hook.js"),
            "r",
            encoding="utf-8",
        ).read()
        self.inject_wechatDLL(wechatEXEpath, wechatEXE_hookcode)

    def load_wechatEXE_and_wechatEx(self):
        wechat_instances = self.wechatutils_instance.get_wechat_runtime_infos()
        if wechat_instances:
            print(Color.RED + "[-] 请关闭所有微信实例后再执行该命令" + Color.END)
            return 0
        self.load_wechatEXE_configs()
        self.load_wechatEx_configs()

    def manage_sessions(self):
        for session in self.active_sessions[:]:
            if session.is_detached:
                print(f"Session {session} detached, removing from active sessions.")
                self.active_sessions.remove(session)


def get_cpu_architecture():
    try:
        cpu_arch = platform.platform().lower()
        if "64bit" in cpu_arch and "macos" in cpu_arch:
            return "MacOS x64"
        return "Windows"
    except Exception as exc:
        print(Color.RED, f"[-] Error detecting CPU architecture: {exc} ", Color.END)
        return "Windows"


if __name__ == "__main__":
    commons = Commons()
    commons.load_wechatEx_configs()
