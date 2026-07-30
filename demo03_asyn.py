
import time
import asyncio
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

async def translate_async(text: str) -> str:
    """异步翻译"""
    response = await model.ainvoke(f"翻译成英文：{text}")
    return response.content

async def main():
    # 并发处理多个任务
    tasks = [
        translate_async("春天来了"),
        translate_async("夏天热"),
        translate_async("秋天凉"),
        translate_async("冬天冷"),
    ]
    start_time = time.time()

    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results, 1):
        print(f"{i}. {result}")

    print(f"耗时：{time.time() - start_time:.2f}秒")

# 运行异步代码
    # await main()
asyncio.run(main())
