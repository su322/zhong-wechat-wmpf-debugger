from argparse import RawTextHelpFormatter
import argparse

from utils.colors import Color
from utils.commons import Commons


def build_parser():
    help_text = """
    请选择要执行的方法：
                        [+] python main.py -h        查看帮助
                        [+] python main.py -x        开启小程序 F12
                        [+] python main.py -c        开启内置浏览器 F12
                        [+] python main.py -all      同时开启内置浏览器 F12 与小程序 F12
                        [+] python main.py --check   检查当前运行时是否内置支持
                        [+] python main.py -x --debug  开启小程序 F12（显示详细调试日志）
    """
    parser = argparse.ArgumentParser(
        description=help_text,
        formatter_class=RawTextHelpFormatter,
    )
    parser.add_argument("-x", action="store_true", help="开启小程序 F12")
    parser.add_argument("-c", action="store_true", help="开启内置浏览器 F12")
    parser.add_argument("-all", action="store_true", help="同时开启内置浏览器 F12 与小程序 F12")
    parser.add_argument("--check", action="store_true", help="检查当前运行时是否内置支持")
    parser.add_argument("--debug", action="store_true", help="显示详细调试日志（含 Frida hook 输出）")
    return parser, help_text


def print_colored_message(message, color):
    print(color + message + Color.END)


def main(args=None):
    parser, help_text = build_parser()
    if args is None:
        args = parser.parse_args()

    if args.check:
        commons.print_runtime_check_status()
    elif args.x:
        commons.load_wechatEx_configs(debug_main=args.debug, debug_frida=args.debug)
    elif args.c:
        commons.load_wechatEXE_configs()
    elif args.all:
        commons.load_wechatEXE_and_wechatEx()
    else:
        print_colored_message(help_text, Color.RED)


if __name__ == "__main__":
    parser, _ = build_parser()
    parsed_args = parser.parse_args()
    commons = Commons()
    main(parsed_args)
