"""
FAISS 向量数据库示例
"""

from embeddings_model import embeddings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_core.documents import Document

# 准备文档
docs = [
    Document(page_content="Langchain 是一个开源的 LLM 应用开发框架。", metadata={"source": "doc1.txt"}),
    Document(page_content="Python 是一种编程语言", metadata={"source": "doc2.txt"}),
    Document(page_content="Hugging Face 是一个开源的深度学习模型库。", metadata={"source": "doc3.txt"}),
    Document(page_content="深度学习是使用神经网络。", metadata={"source": "doc4.txt"}),
    Document(page_content="机器学习需要大量数据。", metadata={"source": "doc5.txt"}),
]

# 创建向量数据库
vectorstore = FAISS.from_documents(docs, embeddings)

print("向量数据库创建完成")
print("=="*80)

# 相似度搜索
query = "AI 开发工具"
results = vectorstore.similarity_search(query, k=3)

print(f"\n查询：{query}")
print(f"最相关的3个文件：\n")

for i, doc in enumerate(results, 1):
    print(f"{i}. {doc.page_content}")
    print(f"    来源：{doc.metadata['source']}\n")

# 带相似度分数的搜索
results_with_scores = vectorstore.similarity_search_with_score(query, k=3)

print(f"带分数的结果")
for doc, score in results_with_scores:
    print(f"分数 {score:.4f}: {doc.page_content}")

# 保存和加载
vectorstore.save_local("faiss_index")
print("向量数据库保存完成")

# 加载
load_vectorstore = FAISS.load_local(
    "faiss_index",
    embeddings,
    allow_dangerous_deserialization=True
)

print("向量数据库加载完成")