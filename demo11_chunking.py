import os

from dotenv import load_dotenv
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter, #递归分块
    CharacterTextSplitter, #字符分块
    TokenTextSplitter #Token分块
)

# 策略1：递归字符分块（推荐）
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500, #每块最大字符数
    chunk_overlap=100, #块之间重叠字符数
    separators=["\n\n", "\n", "(?<=\. )", " ", ""] #分隔符优先级
)

text = """
    第一段内容。
    第二段内容。
    第三段内容。
    第四段内容。
    第五段内容。
    第六段内容。
    第七段内容。
    第八段内容。
    第九段内容。
    第十段内容。
    第十一段内容。
    第十二段内容。
    第十三段内容。
    第十四段内容。
    第十五段内容。
    第十六段内容。

"""

chunks = splitter.split_text(text)
print(f"分成{len(chunks)}块")

# 策略2：分割文档对象
from langchain_core.documents import Document
docs = [
    Document(page_content="长文档内容...", metadata={"source": "doc1.txt"}),
    Document(page_content="另一个文档...", metadata={"source": "doc2.txt"})
]

split_docs = splitter.split_documents(docs)
print(f"分成{len(split_docs)}个文档块")

# 每个块保留原始元数据
for doc in split_docs[:3]:
    print(f"来源：{doc.metadata['source']}")
    print(f"内容：{doc.page_content[:50]}...\n")

# 中文专用分块器
chinese_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 500,
    chunk_overlap = 50,
    separators = [
        "\n\n", #段落
        "\n",   #换行符
        "。",   #中文句号
        "？",   #中文问号
        "；",   #中文分号
        "！",   #中文感叹号
        "，",   #中文逗号
        "  ",   #空格
        ""      #字符
    ],
    length_function = len   #使用字符数
)

# 短文本（FAQ、问答）
faq_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 200,
    chunk_overlap = 20
)

# 长文档（论文、报告）
report_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 1000,
    chunk_overlap = 100
)

# 代码文档
code_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 800,
    chunk_overlap = 50,
    separators=[
        "\n\nclass",    #类
        "\n\ndef",      #函数
        "\n\n",         #段落
        "\n",           #换行符
        "  "            #空格
    ]
)

"""
Embedding 示例
"""

from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_openai import OpenAIEmbeddings

load_dotenv()

embeddings = OpenAIEmbeddings(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
    check_embedding_ctx_length=False,
    model="text-embedding-v4"
)

# # 向量化单个文本
# text = "人工智能正在改变世界"
# vector = embeddings.embed_query(text)

# print(f"向量维度：{len(vector)}")
# print(f"向量前5个值：{vector[:5]}")

# # 批量向量化
# texts = [
#     "人工智能正在改变世界",
#     "机器学习是人工智能的一门分支",
#     "深度学习是机器学习的一个子分支",
#     "自然语言处理是深度学习的一个分支",
#     "计算机视觉是深度学习的一个分支",
#     "图神经网络是深度学习的一个分支",
#     "强化学习是深度学习的一个分支",
#     "概率图模型是深度学习的一个分支",
#     "GAN是深度学习的一个分支",
#     "RNN是深度学习的一个分支",
# ]

# vectors = embeddings.embed_documents(texts)
# print(f"向量数量：{len(vectors)}")

import numpy as np

def cosine_similarity(a, b):
    # 计算余弦相似度
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

vec1 = embeddings.embed_query("人工智能")
vec2 = embeddings.embed_query("奥里给")
vec3 = embeddings.embed_query("今天天气")
vec4 = embeddings.embed_query("AI agent")
vec5 = embeddings.embed_query("机器学习")
vec6 = embeddings.embed_query("深度学习")
vec7 = embeddings.embed_query("自然语言处理")
vec8 = embeddings.embed_query("计算机视觉")
vec9 = embeddings.embed_query("图神经网络")
vec10 = embeddings.embed_query("强化学习")
vec11 = embeddings.embed_query("概率图模型")
vec12 = embeddings.embed_query("AI技术")

print(f"\n相似度")
print(f"人工智能与奥里给：{cosine_similarity(vec1, vec2)}")
print(f"人工智能与今天天气：{cosine_similarity(vec1, vec3)}")
print(f"人工智能与AI agent：{cosine_similarity(vec1, vec4)}")
print(f"人工智能与机器学习：{cosine_similarity(vec1, vec5)}")
print(f"人工智能与深度学习：{cosine_similarity(vec1, vec6)}")
print(f"人工智能与自然语言处理：{cosine_similarity(vec1, vec7)}")
print(f"人工智能与计算机视觉：{cosine_similarity(vec1, vec8)}")
print(f"人工智能与图神经网络：{cosine_similarity(vec1, vec9)}")
print(f"人工智能与强化学习：{cosine_similarity(vec1, vec10)}")
print(f"人工智能与概率图模型：{cosine_similarity(vec1, vec11)}")
print(f"人工智能与AI技术：{cosine_similarity(vec1, vec12)}")