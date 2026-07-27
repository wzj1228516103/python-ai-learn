"""Gradio 网页入口：把 Agent 封装为支持流式响应的聊天界面。"""

from __future__ import annotations

# argparse：解析服务器参数；sys/Path：兼容直接运行脚本。
import argparse
import sys
from pathlib import Path
# Any：兼容 Gradio 多种消息格式；Iterator：声明流式返回类型。
from typing import Any, Iterator

# Gradio：快速创建聊天 UI、队列和本地 HTTP 服务。
import gradio as gr

# 同时兼容 python web.py 与 python -m beambox_agent.web 两种启动方式。
if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from beambox_agent.config import Settings
    from beambox_agent.crew import BeamboxAgent
    from beambox_agent.execution_logger import setup_logging
else:
    from .config import Settings
    from .crew import BeamboxAgent
    from .execution_logger import setup_logging


def _text_content(content: Any) -> str:
    """把 Gradio 的纯文本或多模态字典消息统一转换为文本。"""

    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        return str(content.get("text", ""))
    return ""


def _conversation_context(history: list[dict[str, Any]] | None) -> str:
    """提取最近 8 条对话，限制长度以控制模型上下文和调用成本。"""

    if not history:
        return ""

    lines: list[str] = []
    # 只接受 user/assistant 消息，忽略 Gradio 的其他内部事件。
    for message in history[-8:]:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = _text_content(message.get("content"))
        if role not in {"user", "assistant"} or not content:
            continue
        label = "用户" if role == "user" else "助手"
        lines.append(f"{label}：{content[:1500]}")
    return "\n".join(lines)


def chat(
    message: str,
    history: list[dict[str, Any]] | None,
) -> Iterator[str]:
    """处理一次网页提问，并不断 yield 已累计的答案供前端刷新。"""

    context = _conversation_context(history)
    question = message.strip()
    # 网页端每次创建独立 Agent，因此显式把 Gradio 历史拼入当前问题。
    if context:
        question = (
            "以下历史对话仅用于理解当前问题中的企业、品牌和上下文；仍须检索公开资料：\n"
            f"{context}\n\n当前问题：{question}"
        )

    try:
        agent = BeamboxAgent(settings=Settings.from_env())
        # ask_stream 返回增量片段；Gradio 需要每次收到完整的当前答案。
        answer = ""
        for delta in agent.ask_stream(question):
            answer += delta
            yield answer
    except ValueError as exc:
        yield f"配置错误：{exc}"
    except Exception as exc:
        yield f"查询失败：{exc}"


def build_demo() -> gr.ChatInterface:
    """声明聊天区、输入框、示例问题和 Gradio API 名称。"""

    chatbot = gr.Chatbot(
        label="Beambox 企业资料助手",
        height="65vh",
        layout="panel",
        buttons=["copy", "copy_all"],
        placeholder="查询深圳光胜人工智能科技及 Beambox 品牌公开资料",
    )
    textbox = gr.Textbox(
        placeholder="例如：Beambox 的品牌定位和主要产品是什么？",
        container=False,
        lines=1,
        max_lines=5,
        submit_btn="发送",
        stop_btn="停止",
    )
    return gr.ChatInterface(
        fn=chat,
        chatbot=chatbot,
        textbox=textbox,
        title="Beambox 企业资料助手",
        description="查询深圳光胜人工智能科技及旗下 Beambox 品牌公开信息，并保留来源链接。",
        examples=[
            "Beambox 的品牌定位和主要产品是什么？",
            "深圳光胜人工智能科技有哪些融资动态？",
            "Beambox 最近有哪些招聘岗位？",
        ],
        example_labels=["品牌与产品", "融资动态", "招聘信息"],
        flagging_mode="never",
        save_history=False,
        fill_height=True,
        api_name="beambox_chat",
    )


def build_parser() -> argparse.ArgumentParser:
    """定义网页服务的监听地址、端口和分享参数。"""

    parser = argparse.ArgumentParser(description="启动 Beambox 企业资料 Agent Gradio 界面")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="监听端口；默认从 7860 开始自动选择可用端口",
    )
    parser.add_argument("--share", action="store_true", help="创建 Gradio 临时公网链接")
    parser.add_argument("--inbrowser", action="store_true", help="启动后自动打开浏览器")
    parser.add_argument("--verbose", action="store_true", help="启用详细日志")
    return parser


def main() -> None:
    """启动 Gradio 队列和 Web 服务；启动前先校验 API Key。"""

    args = build_parser().parse_args()
    setup_logging(args.verbose)
    try:
        Settings.from_env()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    # 队列允许多个浏览器请求排队；单进程最多同时处理 4 个任务。
    demo = build_demo()
    demo.queue(default_concurrency_limit=4).launch(
        server_name=args.host,
        server_port=args.port,
        share=args.share,
        inbrowser=args.inbrowser,
        show_error=True,
    )


if __name__ == "__main__":
    main()
