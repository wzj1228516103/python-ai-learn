"""命令行入口：支持单次提问和保持上下文的交互式问答。"""

from __future__ import annotations

# argparse：解析问题与 --verbose 参数；json：格式化工具参数。
import argparse
import json
# sys：控制终端编码、标准输出和退出行为。
import sys
# Path：直接运行本文件时定位 src 目录。
from pathlib import Path

# 同时兼容两种启动方式：python main.py 与 python -m beambox_agent.main。
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from beambox_agent.config import Settings
    from beambox_agent.crew import BeamboxAgent
    from beambox_agent.execution_logger import setup_logging
else:
    from .config import Settings
    from .crew import BeamboxAgent
    from .execution_logger import setup_logging


def _configure_console_encoding() -> None:
    """统一使用 UTF-8，避免 Windows GBK 无法打印模型中的特殊字符。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def _tool_event(name: str, arguments: dict) -> None:
    """在 --verbose 模式下把工具名和参数写到 stderr。"""

    args = json.dumps(arguments, ensure_ascii=False)
    print(f"[工具] {name} {args}", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """定义命令行参数；独立函数便于测试 --help 和参数行为。"""

    parser = argparse.ArgumentParser(description="查询深圳光胜人工智能科技 Beambox 公开资料")
    parser.add_argument("question", nargs="?", help="要查询的企业或 Beambox 品牌问题")
    parser.add_argument("--verbose", action="store_true", help="显示工具调用")
    return parser


def main() -> None:
    """装配配置、日志和 Agent，并进入单次或交互模式。"""

    _configure_console_encoding()
    args = build_parser().parse_args()
    setup_logging(args.verbose)

    try:
        agent = BeamboxAgent(
            settings=Settings.from_env(),
            on_tool_event=_tool_event if args.verbose else None,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    # 命令后带问题时执行一次后退出，适合脚本或自动化调用。
    if args.question:
        print(agent.ask(args.question))
        return

    # 未带问题时保持同一个 Agent，使后续问题拥有对话上下文。
    print("Beambox 企业资料助手（输入 exit 退出，输入 reset 清空对话）")
    while True:
        try:
            question = input("\n你：").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if question.lower() in {"exit", "quit", "q"}:
            break
        if question.lower() == "reset":
            agent.reset()
            print("已清空对话。")
            continue
        if not question:
            continue
        try:
            print(f"\n助手：{agent.ask(question)}")
        except Exception as exc:  # Keep the interactive shell usable after API errors.
            print(f"请求失败：{exc}", file=sys.stderr)


if __name__ == "__main__":
    main()
