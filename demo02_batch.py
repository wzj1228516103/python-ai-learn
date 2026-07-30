
import time
from langchain.chat_models import init_chat_model
import os
from dotenv import load_dotenv

load_dotenv()

model = init_chat_model(
    model="qwen-plus",
    model_provider="openai",
    temperature=0.5,
    base_url=os.getenv("OPENAI_BASE_URL",),
)

inputs = [
    "翻译成英文：春天来了",
    "翻译成英文：夏天热",
    "翻译成英文：秋天凉",
    "翻译成英文：冬天冷",
]

start_time = time.time()
response = model.batch(inputs)
batch_time = time.time() - start_time

print("批量调用结果：")
for i, response in enumerate(response):
    print(f"{i+1}. {response.content}")
print(f"批量调用耗时：{batch_time:.2f}秒")


# 循环调用（低效）
start_time = time.time()
loop_response = []
for input in inputs:
    response = model.invoke(input)
    loop_response.append(response)

end_time = time.time()
print(f"循环调用耗时：{end_time - start_time:.2f}秒")

print(f"批量调用节省时间：{(end_time - start_time) - batch_time:.2f}秒")
