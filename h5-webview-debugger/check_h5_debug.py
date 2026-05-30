from dataclasses import dataclass
from pathlib import PureWindowsPath
from typing import Iterable, List, Optional
import urllib.error
import urllib.request

import psutil


WECHAT_PROCESS_NAMES = {
    "wechat.exe",
    "wechatappex.exe",
    "wechatweb.exe",
    "weixin.exe",
    "hd_weixin.exe",
    "xweb.exe",
}

INSPECT_KEYWORDS = (
    "--xweb-enable-inspect=1",
    "--xweb-enable-inspect",
    "--remote-debugging-port",
    "--remote-allow-origins",
    "devtools",
    "inspect",
)


@dataclass(frozen=True)
class ProcessSummary:
    pid: int
    name: str
    cmdline: List[str]
    matched_flags: List[str]
    error: Optional[str] = None


@dataclass(frozen=True)
class AnalysisResult:
    status: str
    processes: List[ProcessSummary]
    remote_debugging_ports: List[int]
    h5_status: str

    @property
    def has_wechat_process(self):
        return bool(self.processes)

    @property
    def has_inspect_flag(self):
        return any(process.matched_flags for process in self.processes)


def normalize_process_name(name):
    return (name or "").strip().lower()


def is_wechat_process(name, cmdline):
    normalized_name = normalize_process_name(name)
    if normalized_name in WECHAT_PROCESS_NAMES:
        return True

    if not cmdline:
        return False

    executable_name = normalize_process_name(PureWindowsPath(cmdline[0]).name)
    return executable_name in WECHAT_PROCESS_NAMES


def find_inspect_flags(cmdline):
    command_text = " ".join(cmdline or [])
    lower_command_text = command_text.lower()
    return [keyword for keyword in INSPECT_KEYWORDS if keyword in lower_command_text]


def find_remote_debugging_ports(cmdline):
    ports = []
    for item in cmdline or []:
        lower_item = item.lower()
        prefix = "--remote-debugging-port="
        if not lower_item.startswith(prefix):
            continue

        port_text = item[len(prefix) :]
        try:
            ports.append(int(port_text))
        except ValueError:
            continue
    return ports


def is_wxpublic_process(cmdline):
    command_text = " ".join(cmdline or [])
    return "--type=wxpublic" in command_text.lower()


def is_top_level_wechatappex_process(cmdline):
    command_text = " ".join(cmdline or [])
    lower_command_text = command_text.lower()
    return (
        "wechatappex.exe" in lower_command_text
        and "--helper-handle-value" in lower_command_text
        and "--type=" not in lower_command_text
    )


def command_has_flag(cmdline, flag):
    command_text = " ".join(cmdline or [])
    return flag.lower() in command_text.lower()


def get_h5_status(summaries):
    h5_processes = [
        summary
        for summary in summaries
        if is_wxpublic_process(summary.cmdline)
        or is_top_level_wechatappex_process(summary.cmdline)
    ]
    if not h5_processes:
        return "not_opened"

    for summary in h5_processes:
        ports = find_remote_debugging_ports(summary.cmdline)
        if command_has_flag(summary.cmdline, "--xweb-enable-inspect") and 9222 in ports:
            return "ready"

    return "partial"


def analyze_processes(processes):
    summaries = []
    unreadable_wechat_process = False

    for process in processes:
        name = process.get("name") or ""
        cmdline = process.get("cmdline")
        error = process.get("error")

        if cmdline is None:
            if is_wechat_process(name, []):
                unreadable_wechat_process = True
                summaries.append(
                    ProcessSummary(
                        pid=process.get("pid", 0),
                        name=name,
                        cmdline=[],
                        matched_flags=[],
                        error=error or "cmdline unavailable",
                    )
                )
            continue

        if not is_wechat_process(name, cmdline):
            continue

        summaries.append(
            ProcessSummary(
                pid=process.get("pid", 0),
                name=name,
                cmdline=list(cmdline),
                matched_flags=find_inspect_flags(cmdline),
                error=error,
            )
        )

    if any(summary.matched_flags for summary in summaries):
        status = "enabled"
    elif summaries and unreadable_wechat_process and not any(summary.cmdline for summary in summaries):
        status = "unknown"
    elif summaries:
        status = "disabled"
    else:
        status = "not_found"

    remote_debugging_ports = sorted(
        {
            port
            for summary in summaries
            for port in find_remote_debugging_ports(summary.cmdline)
        }
    )

    return AnalysisResult(
        status=status,
        processes=summaries,
        remote_debugging_ports=remote_debugging_ports,
        h5_status=get_h5_status(summaries),
    )


def probe_devtools_port(port, timeout=1.0):
    if port <= 0:
        return False, "动态端口无法直接探测"

    url = f"http://127.0.0.1:{port}/json/list"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return 200 <= response.status < 300, f"HTTP {response.status}"
    except urllib.error.URLError as exc:
        return False, str(exc.reason)
    except OSError as exc:
        return False, str(exc)


def iter_local_processes():
    for process in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            yield {
                "pid": process.info.get("pid"),
                "name": process.info.get("name") or "",
                "cmdline": process.info.get("cmdline") or [],
            }
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess) as exc:
            yield {
                "pid": getattr(process, "pid", 0),
                "name": "",
                "cmdline": None,
                "error": exc.__class__.__name__,
            }


def format_process_summary(process):
    flags = ", ".join(process.matched_flags) if process.matched_flags else "none"
    if process.error:
        return f"- PID {process.pid} {process.name}: unreadable ({process.error}), inspect flags: {flags}"

    command = " ".join(process.cmdline)
    if len(command) > 260:
        command = command[:257] + "..."
    return f"- PID {process.pid} {process.name}: inspect flags: {flags}; cmdline: {command}"


def print_result(result):
    print("H5 WebView debug inspection")

    if result.status == "not_found":
        print("Status: not_found")
        print("未检测到微信或 XWeb 相关进程。请先启动 PC 微信。")
        return

    if result.status == "enabled":
        print("Status: enabled")
        print("已检测到 XWeb/inspect 相关参数。可以继续在 PC 微信内打开目标 H5 页面并尝试检查入口。")
    elif result.status == "disabled":
        print("Status: disabled")
        print("检测到微信相关进程，但未发现 inspect 参数。请先关闭微信，再运行 run_h5_debug.ps1。")
    else:
        print("Status: unknown")
        print("检测到微信相关进程，但无法读取命令行参数。请用管理员权限重试，或手动记录现象。")

    print("")
    print("Process summary:")
    for process in result.processes:
        print(format_process_summary(process))

    print("")
    print(f"H5 wxpublic status: {result.h5_status}")
    if result.h5_status == "not_opened":
        print("未检测到公众号/H5 的 wxpublic 进程。请在 Hook 保持期间打开 H5 页面。")
    elif result.h5_status == "partial":
        print("检测到 wxpublic 进程，但 H5 调试参数不完整或仍是动态端口。请关闭微信后用新版脚本重启。")
    else:
        print("检测到 wxpublic 进程已带固定 DevTools 端口参数。")

    if result.remote_debugging_ports:
        print("")
        print("DevTools endpoint probe:")
        for port in result.remote_debugging_ports:
            ok, detail = probe_devtools_port(port)
            url = f"http://127.0.0.1:{port}/json/list"
            state = "reachable" if ok else "unreachable"
            print(f"- {url}: {state} ({detail})")


def main():
    result = analyze_processes(iter_local_processes())
    print_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
