from datetime import datetime
import json
import os
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from model_qwen import model

class MemoryManager:
    """记忆管理器"""

    def __init__(self, storage_file: str = "conversation_memory.json"):
        self.storage_file = storage_file

    def save_conversation(self, session_id: str, messages: list):
        """保存对话到文件"""
        # 读取现有数据
        data = self.load_data()

        # 转换消息为可序列化格式
        serialized_messages = []
        for msg in messages:
            serialized_messages.append({
                "type": msg.type,
                "content": msg.content,
                "timestamp": datetime.now().isoformat()
            })

        # 保存
        data[session_id] = {
            "messages": serialized_messages,
            "update_at": datetime.now().isoformat()
        }

        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_conversation(self, session_id: str) -> list:
        """加载对话"""
        data = self.load_data()

        if session_id not in data:
            return []

        # 转换回消息对象
        messages = []
        for msg_data in data[session_id]["messages"]:
            if msg_data["type"] == "human":
                messages.append(HumanMessage(content=msg_data["content"]))
            if msg_data["type"] == "ai":
                messages.append(AIMessage(content=msg_data["content"]))

        return messages

    def load_data(self) -> dict:
        """加载数据文件"""
        if not os.path.exists(self.storage_file):
            return {}
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading data from {self.storage_file}: {e}")
            return {}

    def list_sessions(self) -> list:
        """列出所有会话"""
        data = self.load_data()
        return list(data.keys())

# 创建工具
@tool
def get_current_time() -> str:
    """获取当前时间"""
    return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

# 创建Agent
agent = create_agent(
    model=model,
    tools=[
        get_current_time,
    ],
    # memory=MemoryManager(),
    system_prompt="""
    你是一个智能助手，能记住用户之前的话
    """,
)

def main():
    memory = MemoryManager()

    print("持久化记忆助手")
    print("=="*80)

    # 选择或创建会话
    sessions = memory.list_sessions()
    if sessions:
        print(f"\n现有会话：{"，".join(sessions)}")
        session_id = input("输入会话ID(或者输入新ID创建)：").strip()
    else:
        session_id = input("输入新会话ID：").strip()

    # 加载历史对话
    messages = memory.load_conversation(session_id)

    if messages:
        print(f"\n 已加载 {len(messages)} 条历史记录")
        print("最近的对话：")
        for msg in messages[-4:]:
            role = "用户" if msg.type == "human" else "助手"
            print(f"{role}：{msg.content[:50]}...")
    else:
        print(f"\n 创建新会话：{session_id}")

    print("=="*80)
    print("\n输入quit退出")

    while True:
        user_input = input("\n你：")

        if user_input.lower() == "quit":
            # 保存对话
            memory.save_conversation(session_id, messages)
            print("\n 对话已保存到会话{session_id}")
            break

        if not user_input.strip():
            continue

        # 添加用户消息
        messages.append(HumanMessage(content=user_input))

        # 调用agent
        result = agent.invoke({"messages": messages})
        messages = result["messages"]

        # 显示回复
        ai_response = messages[-1].content
        print(f"\n助手：{ai_response}\n")

        # 自动保存
        memory.save_conversation(session_id, messages)

if __name__ == "__main__":
    main()
