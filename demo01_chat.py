from email import message
import os

from langchain.chat_models import init_chat_model
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

model = init_chat_model(
    model="qwen-plus",
    model_provider="openai",
    temperature=0.5,
    base_url=os.getenv("OPENAI_BASE_URL",),
)

# response = model.invoke("你好")
# print(response.content)

# for chunk in model.stream("你好"):
#     print(chunk.content, end="")

message = [
    HumanMessage(content="你好"),
    AIMessage(content="你好，有什么我可以帮助你的吗？"),
    HumanMessage(content="我想知道你是什么模型"),
]
response = model.invoke(message)
print(response.content)
