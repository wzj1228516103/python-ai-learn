"""统一创建并导出供示例代码复用的 Qwen LangChain 模型。"""

# os：读取 API Key 和 OpenAI 兼容服务地址。
import os

# load_dotenv：把项目根目录 .env 中的配置载入当前进程环境变量。
from dotenv import load_dotenv
# init_chat_model：按 OpenAI 兼容协议创建 LangChain 聊天模型。
from langchain.chat_models import init_chat_model


load_dotenv()

# 显式检查密钥，避免后续由 SDK 抛出不够直观的 Missing credentials 错误。
api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError(
        "没有读取到 API Key。请在 D:\\AI agent\\.env 中设置 "
        "OPENAI_API_KEY 或 DASHSCOPE_API_KEY。"
    )

# 这个变量名是本模块公开的接口，其他脚本使用 `from model_qwen import model` 导入。
model = init_chat_model(
    model="qwen-plus",
    model_provider="openai",
    temperature=0.5,
    api_key=api_key,
    base_url=os.getenv(
        "OPENAI_BASE_URL",
        "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ),
)
