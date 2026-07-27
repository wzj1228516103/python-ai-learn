"""读取环境变量和 YAML 提示词配置，是整个项目的配置入口。"""

# 允许在 Python 3.10 中使用更现代的类型注解写法，并推迟注解求值。
from __future__ import annotations

# os：读取 API Key、模型名等操作系统环境变量。
import os
# dataclass：用声明式方式定义不可变配置对象，减少手写初始化代码。
from dataclasses import dataclass
# Path：跨平台拼接和读取配置文件路径。
from pathlib import Path

# PyYAML：把 agents.yaml、tasks.yaml 转换为 Python 字典。
import yaml
# python-dotenv：自动查找并加载 .env，避免把密钥写入源码。
from dotenv import find_dotenv, load_dotenv


@dataclass(frozen=True)
class Settings:
    """集中保存运行参数；frozen=True 防止配置在运行中被意外修改。"""

    # 调用大模型所需的密钥。
    api_key: str
    # OpenAI 兼容接口地址，默认指向阿里云 DashScope。
    base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    # 实际调用的模型名称，可由 MODEL_NAME 环境变量覆盖。
    model: str = "qwen3.7-flash-2026-07-15"
    # 搜索和读取网页时的 HTTP 超时时间。
    request_timeout: float = 20.0
    # 一次问答允许模型和工具往返的最大轮数，防止无限调用。
    max_tool_rounds: int = 6

    @classmethod
    def from_env(cls) -> "Settings":
        """从当前目录或父目录的 .env 构建并校验 Settings。"""

        # usecwd=True 从用户实际启动命令的目录开始向上寻找 .env。
        env_file = find_dotenv(usecwd=True)
        if env_file:
            load_dotenv(env_file)

        # 同时兼容项目通用变量名和 DashScope 官方变量名。
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
        if not api_key:
            raise ValueError(
                "未找到 API Key。请复制 .env.example 为 .env，并设置 "
                "OPENAI_API_KEY 或 DASHSCOPE_API_KEY。"
            )

        # 环境变量都是字符串；数值配置需显式转换，尽早暴露格式错误。
        return cls(
            api_key=api_key,
            base_url=os.getenv(
                "OPENAI_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            model=os.getenv("MODEL_NAME", "qwen-plus"),
            request_timeout=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20")),
            max_tool_rounds=int(os.getenv("MAX_TOOL_ROUNDS", "6")),
        )


def load_prompt_config(filename: str) -> dict:
    """读取包内 config/<filename>，并确保 YAML 根节点是映射对象。"""

    # with_name("config") 将当前 config.py 替换为同级 config 目录。
    config_path = Path(__file__).with_name("config") / filename
    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"配置文件格式错误: {config_path}")
    return data
