"""
    完整的 RAG 系统
"""

import os

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAIEmbeddings


load_dotenv()

# 1.准备向量数据库（假设已有）
embeddings = OpenAIEmbeddings(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
    check_embedding_ctx_length=False,
    model="text-embedding-v4"
)

# 加载.创建向量数据库
vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

# 2.创建检索器
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}  # 返回3条最相似的文档
)

# 3.创建提示词模板
prompt = ChatPromptTemplate.from_template(
    """

    你是一个问答助手。请基于以下上下文，回答问题。

    上下文：
    {context}

    问题：
    {question}

    要求：
    1.仅基于上下文回答，不要编造信息
    2.如果上下文没有相关信息，明确告诉用户
    3.回答要准确，简介

    答案：
    """
)


# 4.创建模型
model = init_chat_model(
    "qwen-plus",
    model_provider="openai",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
    temperature=0.0
)

# 5.构建RAG Chain
def format_docs(docs):
    """格式化检索到的文件"""
    return "\n\n".join([f"文档{i+1}:\n{doc.page_content}" for i, doc in enumerate(docs)])

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)

# 6.测试
question = "Hugging Face是什么？"
answer = rag_chain.invoke(question)

print(f"问题：{question}")
print(f"答案：{answer}")
