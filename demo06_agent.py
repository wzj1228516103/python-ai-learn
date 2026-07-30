from langchain.agents import create_agent

from model_qwen import model
from tools import get_weather, calculator

# agent = create_agent(
#     model = model,
#     tools = search_product,
#     system_message = """
#     You are a helpful assistant.
#     """,
# )

# result = agent.invoke({
#     "message": [{"role": "user", "content": "有什么电脑推荐吗"}]
# })

# 创建agent
agent = create_agent(
    model = model,
    tools = [get_weather, calculator],
    # debug=True,
    system_prompt = """
    你是一个智能助手，可以查询天气和数学计算。

    当用户询问天气时，请使用get_weather工具。
    当用户进行数学计算时，请使用calculator工具。

    请始终用中文回答。
    """,
)

# print("agent test")
# # 天气查询测试
# print("=" * 60)
# print("【测试1】天气查询")
# print("=" * 60)

# question1 = "深圳今天天气怎么样"
# print(f"用户提问：{question1}\n")

# result1 = agent.invoke({
#     "messages": [{"role": "user", "content": question1}]
# })

# 获取最后一条消息（AI的回答）
# print("=" * 60)
# print("=" * 60)
# answer1 = result1["messages"][-1].content
# print(f"AI回答：{answer1}\n")

# 多轮对话
print("多轮对话 agent（输入quit退出）")

messages = []

while True:
    user_input = input("用户：")
    if user_input.lower() == "quit":
        break

    # 添加用户信息
    messages.append({"role": "user", "content": user_input})
    # 调用agent
    result = agent.invoke({"messages": messages})
    # 更新消息历史（包含所有中间步骤）
    messages = result["messages"]
    # 获取最后一条 AI 回复
    last_answer = messages[-1]
    if last_answer.type == "ai":
        print(f"AI：{last_answer.content}")