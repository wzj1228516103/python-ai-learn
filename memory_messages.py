from model_qwen import model
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

def trim_messages(messages: list, max_messages: int = 20) -> list:
    """
    保留最近的N条消息

    Args:
        messages (list): 完整消息列表
        max_messages (int, optional): 保留的最大消息数
    """

    if len(messages) <= max_messages:
        return messages

    # 始终保留系统消息
    system_messages = [msg for msg in messages if msg.type == "system"]
    other_messages = [msg for msg in messages if msg.type != "system"]

    # 保留最近的消息
    recent_messages = other_messages[-max_messages:]

    return system_messages + recent_messages

# 摘要记忆
def summarize_old_messages(model, messages: list) -> str:
    """将旧消息总结为摘要"""
    # 提取旧对话
    old_conversation = "\n".join([[
        f"{"用户" if msg.type == "human" else "AI"}: {msg.content}"
        for msg in messages
    ]])

    # 生成摘要
    summary_prompt = f"""请总结以下对话的关键信息：
    {old_conversation}
    总结（包含用户信息、重要事实、代办事项）：
    """
    summary = model.invoke(summary_prompt).content
    return summary

# # 使用
# if len(messages) > 50:
#     # 总结前40条消息
#     summary = summarize_old_messages(model, messages[:40])

#     messages = [
#         SystemMessage(content=f"之前的对话摘要：\{summary}")
#     ] +messages[40:]