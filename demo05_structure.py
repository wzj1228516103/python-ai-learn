from model_qwen import model
from pydantic import BaseModel, Field
from typing import List

class Aspect(BaseModel):
    """评价维度"""
    name: str = Field(description="维度名称，如质量、价格、服务")
    score: int = Field(description="评分，1-5")
    comment: str = Field(description="具体评价")

class ProductReview(BaseModel):
    """产品评论分析"""
    overall_sentiment: str = Field(description="整体情感：positive/negative/neutral")
    overall_score: int = Field(description="整体评分，1-5")
    aspects: List[Aspect] = Field(description="各维度评价")
    summary: str = Field(description="一句话总结")

# 创建结构化模型
structured_model = model.with_structured_output(ProductReview)
# 测试
review_text = "这个手机质量很好，价格也便宜，服务态度不错"

result = structured_model.invoke(
    f"请对以下产品评价进行结构化分析：\n{review_text}"
)

print(f"整体情感：{result.overall_sentiment}")
print(f"整体评分：{result.overall_score}")
print(f"评价维度：{result.aspects}")
for aspect in result.aspects:
    print(f"{aspect.name}：{aspect.score}/5——{aspect.comment}")
print(f"总结：{result.summary}")