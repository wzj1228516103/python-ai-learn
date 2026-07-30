from pydantic import BaseModel, Field

from model_qwen import model

# 定义输出结构
class SentimentAnalysis(BaseModel):
    """情感分析结果"""
    sentiment: str = Field(description="情感倾向：【正面positive/负面negative/中性neutral】")
    confidence: float = Field(description="置信度,0-1之间的浮点数")
    keywords: list[str] = Field(description="关键词列表")

# v1.0: with_structured_output
structured_model = model.with_structured_output(SentimentAnalysis)

# 调用
text = "这个课程很有趣，我很喜欢"
response = structured_model.invoke(
    f"请对以下文本进行情感分析：\n{text}"
)

print(f"类型：{type(response)}")
print(f"情感:{response.sentiment}")
print(f"置信度:{response.confidence:.2f}")
print(f"关键词:{response.keywords}")
