import os
import pandas as ps
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable not set")

client = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def generate_responses(prompt, model="qwen-plus"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Error: " + str(e)

# prompt = f"""
#     根据下面的上下文回答问题。保持答案简短且准确。如果不确定答案，请回答"不确定答案"。

#     Teplizumab起源于一个位于新泽西的药品公司，名为Ortho Pharmaceutical。\
#     在那里，科学家们生成了一种早期版本的抗体，被称为OKT3。最初这种分子是从小鼠中提取的，\
#     能够结合到T细胞的表面，并限制它们的细胞杀伤潜力。在1986年，它被批准用于帮助预防肾脏移植后的\
#     器官排斥，成为首个被允许用于人类的治疗性抗体。


#     问题：0KT3最初是从什么来源提取的？
# """

# prompt = f"""
#     问题：OKT3最初是从什么来源提取的?
# """

instruction = """
根据下面的上下文回答问题。保持答案简短且准确。如果不确定答案，请回答"不确定答案”。

以Json格式输出:
{"具体问题":"答案"}

"""

context = """
Teplizumab起源于一个位于新泽西的药品公司，名为Ortho Pharmaceutical。\
在这里，科学家们生成了一种早期版本的抗体，被称为OKT3。最初这种分子是从小鼠中提取的，\
能够结合到T细胞的表面，并限制它们的细胞杀伤潜力。在1986年，它被批准用于帮助预防肾脏移植后的\
器官排斥，成为首个被允许用于人类的治疗性抗体。
"""

query = f"""
0KT3最初是从什么来源提取的？
"""

prompt = f"""

{instruction}

{context}

{query}

"""

response = generate_responses(prompt)
print(response)
