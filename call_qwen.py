import gradio as gr
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

def call_qwen(message, history):

    if not api_key:
        return "OPENAI_API_KEY environment variable not set"

    # 初始化OpenAI客户端
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )

    # 历史对话记录列表
    messages = []

    # 存在历史对话记录，添加到消息列表
    if history:
        try:
            for msg in history:
                if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                    messages.append(msg)
                elif isinstance(msg, (list, tuple)) and len(msg) == 2:
                    user_msg, assistant_msg = msg
                    messages.append({"role": "user", "content": user_msg})
                    messages.append({"role": "assistant", "content": assistant_msg})
        except Exception as e:
            print(f"处理历史对话记录时出错: {e}")
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.create(
            model="qwen-max",
            messages=messages,
            stream=False
        )

        return response.choices[0].message.content

    except Exception as e:
        return "Error: " + str(e)

demo = gr.ChatInterface(
    fn = call_qwen,
    title="通义千问-max",
    description="与通义千问-max模型进行对话",

    examples=[
        ["你好"],
        ["你的名字"],
        ["你是谁"],
    ]
)

if __name__ == "__main__":
    demo.launch()
