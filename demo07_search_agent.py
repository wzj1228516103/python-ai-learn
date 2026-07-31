import json
from typing import Optional

from langchain.agents import create_agent
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# 复用项目统一配置的 Qwen 模型。
from model_qwen import model
# 异步工具
# 对于I/O密集型的任务，使用异步工具可以提高性能。
import asyncio

# 复杂参数的工具
class SearchParams(BaseModel):
    """
    搜索参数
    """
    keyword: str = Field(description="搜索关键词")
    category: Optional[str] = Field(default=None, description="搜索分类")
    max_results: int = Field(default=5, description="最大结果数")

@tool
def advanced_search(params: SearchParams) -> str:
    """
    高级搜索

    支持关键词搜索、分类筛选、结果数量限制

    Args:
        params (SearchParams): 搜索参数对象
    """

    results = f"搜索 '{params.keyword}'"
    if params.category:
        results += f" 在分类 “{params.category}”"
    results += f"，最多返回 {params.max_results} 个结果"

    return results

# 返回结构化输出
@tool
def get_product_info(product_id: str) -> str:
    """
    获取产品信息

    Args：
        product_id (str): 产品ID

    Returns：
        JSON 格式的产品信息
    """
    product = {
        "P001": {
            "name": "iPhone 13 Pro",
            "price": 5999,
            "stock": 100,
            "rating": 4.5,
        },
        "P002": {
            "name": "MacBook Pro",
            "price": 23999,
            "stock": 50,
            "rating": 4.8,
        },
        "P003": {
            "name": "Samsung Galaxy S21 Ultra",
            "price": 8999,
            "stock": 30,
            "rating": 4.7,
        },
        "P004": {
            "name": "Google Pixel 6",
            "price": 4999,
            "stock": 60,
            "rating": 4.6,
        },
        "P005": {
            "name": "OnePlus Nord",
            "price": 2999,
            "stock": 80,
            "rating": 4.4,
        },
        "P006": {
            "name": "Xiaomi Redmi Note 10 Pro",
            "price": 1499,
            "stock": 90,
            "rating": 4.3,
        },
    }
    product = product.get(product_id, {"error": "产品不存在"})
    return json.dumps(product, ensure_ascii=False)

@tool
async def fetch_data_async(url: str) -> str:
    """
    异步获取网络数据

    Args：
        url (str): 目标 URL
    """

    # 模拟网络请求
    await asyncio.sleep(1)
    return f"从 {url} 获取数据成功"

# Agent 必须在调用 ainvoke 前创建；tools 列表决定模型可调用哪些 Python 函数。
agent = create_agent(
    model=model,
    tools=[advanced_search, get_product_info, fetch_data_async],
    system_prompt=(
        "你是一个产品搜索助手。需要搜索时调用 advanced_search，"
        "需要产品详情时调用 get_product_info，需要读取 URL 时调用 fetch_data_async。"
        "请始终使用中文回答。"
    ),
)


async def main():
    # 使用异步 Agent
    result = await agent.ainvoke({
        "messages": [{
            "role": "user",
            # fetch_data_async 需要 url 参数，示例问题必须提供实际目标地址。
            "content": "请获取 https://baidu.com 的产品数据以及联系方式,并输出给我"
        }]
    })


    # Agent 返回的 messages 是列表；最后一条通常是工具调用后的 AI 最终回答。
    print("=" * 60)
    print("=" * 60)
    print(f"{result}")

    print("=" * 60)
    print("=" * 60)

    answer = result["messages"][-1].content
    print(f"AI回答：{answer}")


if __name__ == "__main__":
    asyncio.run(main())
