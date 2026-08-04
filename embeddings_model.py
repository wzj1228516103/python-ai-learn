import os

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

load_dotenv()

embeddings = OpenAIEmbeddings(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY"),
    check_embedding_ctx_length=False,
    model="text-embedding-v4"
)