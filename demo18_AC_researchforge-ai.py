"""
    AC actual combat 实战
    生产级智能研究助手（LangChain 1.0）

    使用官方 Middleware API 包含：
    - 性能监控
    - 成本追踪
    - 错误重试
    - 结构化输出
    - 动态模型选择

"""


# ============ 数据模型 ====================

from datetime import datetime
import json
import os
import time
from typing import Any, Callable

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langchain.agents.middleware import (
    AgentMiddleware,
    AgentState,
    ModelCallLimitMiddleware,
    ModelRequest,
    ModelResponse,
    before_model,
    after_model,
    wrap_model_call,
)
from langgraph.runtime import Runtime
from openai import BaseModel
from pydantic import Field


# Load API configuration from the project .env file before creating the model.
load_dotenv()


class SubQuestion(BaseModel):
    """子问题"""
    question: str = Field(description="子问题内容")
    priority: int = Field(description="优先级1-5", ge=1, le=5)
    difficulty: str = Field(description="难度: easy/medium/hard")

class ResearchPlan(BaseModel):
    """研究计划"""
    main_question: str = Field(description="主问题")
    sub_questions: list[SubQuestion] = Field(description="子问题列表")
    approach: str = Field(description="研究方法")
    estimated_time: str = Field(description="预计耗时")

class ResearchFinding(BaseModel):
    """研究发现"""
    topic: str = Field(description="主题")
    key_points: list[str] = Field(description="关键要点")
    sources: list[str] = Field(description="信息来源")
    confidence: float = Field(description="置信度0-1", ge=0, le=1)

class  ResearchReport(BaseModel):
    """研究报告"""
    title: str = Field(description="报告标题")
    summary: str = Field(description="执行摘要")
    findings: list[ResearchFinding] = Field(description="研究发现")
    conclusions: str = Field(description="结论")
    recommendations: list[str] = Field(description="建议")
    generated_at: str = Field(description="生成时间")


#  ============ 工具定义 ====================

@tool
def search_information(query: str):
    """
    搜索信息（模拟知识库）

    Args：
        query (str): 搜索关键词
    """

    knowledge = {
        "LangChain": "LangChain 是一个开源的 LLM 应用开发框架，用于构建 LLM 应用。",
        "LLM": "LLM（Large Language Model） 是指基于深度学习的语言模型，如 GPT-3、GPT-4 等。",
        "Middleware API": "Middleware API 是一个用于构建 LLM 应用的 API，用于实现性能监控、错误重试、结构化输出、动态模型选择等功能。",
        "Research Assistant": "Research Assistant 是一个 LLM 应用，用于帮助用户进行研究。",
        "Research Report": "Research Report 是一个 LLM 应用，用于生成报告",
        "Agent": "Agent 是一个 LLM 应用，用于帮助用户进行任务代理。",
        "RAG": "RAG（Retrieval Augmented Generation）是一种 LLM 应用，用于帮助用户进行信息检索。",
    }

    results = []

    for key, value in knowledge.items():
        if query.lower() in key.lower() or key.lower() in query.lower():
            results.append(f"【{key}】: {value}")

    return "\n\n".join(results) if results else "未找到关于{query}信息"

@tool
def analyze_data(data: str) -> str:
    """
    分析数据

    Args：
        data (str): 需要分析的数据
    """
    word_count = len(data.split())
    char_count = len(data)

    return f"""
- 总字数：{word_count}
- 总字符数：{char_count}
- 信息完整性: {'高' if word_count > 50 else '中' if word_count > 20 else '低'}
 - 包含关键概念数：{sum(1 for k in ["LangChain", "Middleware", "RAG", "Agent"] if k in data)}
"""

# ============ Middleware 定义 ====================
class PerformanceMonitorMiddleware(AgentMiddleware):
    """性能监控中间件"""

    def __init__(self):
        self.session_start = None
        self.model_calls = []
        self.tool_calls = []

    def before_agent(
            self,
            state: AgentState,
            runtime: Runtime,
    ) -> dict[str, Any] | None:
        self.session_start = time.time()
        print(f"\n"+"="*80)
        print(f" 会话开始：{datetime.now().strftime('%H:%M:%S')}")
        return None

    def before_agent(
            self,
            state: AgentState,
            runtime: Runtime
    ) -> dict[str, Any] | None:
        self.session_start = time.time()
        print(f"\n"+"="*80)
        print(f" 会话开始：{datetime.now().strftime('%H:%M:%S')}")
        print(f"=="*80+"\n")

    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        start = time.time()
        model_name = getattr(
            request.model, "model_name", request.model.__class__.__name__
        )
        try:
            result = handler(request)
            elapsed = time.time() - start
            self.model_calls.append(elapsed)
            print(f"模型调用({model_name})：{elapsed:.2f}秒")
            return result
        except Exception as e:
            print(f"模型调用失败({model_name}: {e})")
            raise

    def after_agent(
            self,
            state: AgentState,
            runtime: Runtime
    ) -> dict[str, Any] | None:
        total_time = time.time() - self.session_start

        print(f"\n"+ "="*80)
        print(f"性能统计")
        print(f"="*80)
        print(f"总耗时：{total_time:.2f}秒")
        print(f"模型调用次数：{len(self.model_calls)}")

        if self.model_calls:
            print(f"-平均：{sum(self.model_calls)/len(self.model_calls):.2f}秒")
            print(f"-总计：{sum(self.model_calls):.2f}秒")

        print(f"工具模型调用：{len(self.tool_calls)} 次")
        if self.tool_calls:
            total_tool_time = sum(t[1] for t in self.tool_calls)
            print(f" - 总计：{total_tool_time:.2f}秒")
        print(f"="*80+"\n")
        return None

class CostTrackingMiddleware(AgentMiddleware):
    """成本追踪中间件"""

    def __init__(self, budget: float = 1.0):
        self.budget = budget
        self.total_cost = 0.0
        self.model_prices = {
            "gpt-3.5-turbo": 0.002,
            "gpt-4": 0.03,
            "text-davinci-003": 0.02,
            "text-davinci-002": 0.02,
            "text-curie-001": 0.002,
            "text-babbage-001": 0.0005,
            "text-ada-001": 0.0004,
        }

    def before_model(
        self,
        state: AgentState,
        runtime: Runtime,       
    ) -> dict[str, Any] | None:
        if self.total_cost >= self.budget:
            print(f"预算已用完(￥{self.budget})")
            return {
                "jump_to": "end",
                "message": [AIMessage(content="预算已用完，感谢使用！")],
            }
        return None

    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        response = handler(request)

        # 估算成本（简化版）
        model_name = "gpt-3.5-turbo"
        price = self.model_prices.get(model_name, 0.3)

        # 估算tokens（简化）
        input_tokens = sum(len(str(m.content)) for m in request.messages) * 1.5
        print(response)
        output_tokens = len(str(response.result[0].content)) * 1.5

        cost = (input_tokens + output_tokens) / 1_000_000 * price
        self.total_cost += cost
        print(f" 成本：￥{cost:.4f}（累计：￥{self.total_cost:.4f}/￥{self.budget}）")

        return response

class RetryMiddleware(AgentMiddleware):
    """重试中间件"""

    def __init__(self, max_retries: int = 2):
        self.max_retries = max_retries

    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        for attempt in range(self.max_retries + 1):
            try:
                return handler(request)
            except Exception as e:
                if attempt == self.max_retries:
                    print(f"重试{self.max_retries}次失败，抛出异常：{e}")
                    raise

                wait_time = 2 ** attempt
                print(f"重试中（{attempt + 1}/{self.max_retries}），{wait_time}秒后重试")
                time.sleep(wait_time)

# ============ 智能研究助手 ====================

class ResearchAssistant:
    """智能研究助手"""

    def __init__(self):
        # 创建模型
        self.model = init_chat_model(
            model="qwen-plus",
            model_provider="openai",
            base_url= "https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY"),
            temperature=0.0,
        )

        # 工具
        self.tools = [
            search_information, analyze_data
        ]

        # Middleware
        self.performance_monitor = PerformanceMonitorMiddleware()
        self.cost_tracker = CostTrackingMiddleware(budget=0.5)
        self.retry_handler = RetryMiddleware(max_retries=2)

        # 创建 Agent
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            middleware=[
                self.cost_tracker,                         #1.成本控制
                ModelCallLimitMiddleware(run_limit=15),    #2.模型调用限制
                self.retry_handler,                        #3.重试 
                self.performance_monitor,                  #4.性能监控
            ],
            system_prompt="""
            你是专业的研究助手
            
            职责：
            1.分解复杂问题为子问题
            2.使用工具搜索和分析信息
            3.生成结构化的研究报告

            工作流程：
            1.理解研究主题
            2.使用 search_information 搜索相关信息
            3.使用 analyze_data 分析数据
            4.综合信息生成结论
            """
        )

    def create_plan(self, question: str) -> ResearchPlan:
        """制定研究计划"""
        print(f"正在制定研究计划...\n")
        structured_model = self.model.with_structured_output(ResearchPlan)

        prompt = f"""
            请为以下研究问题制定详细计划：
            
            研究问题：{question}

            要求：
            1.分解为 3-4 个子问题
            2.设置优先级（1-5）
            3.评估难度（easy/medium/hard）
            4.说明研究方法
            5.估算所需时间

            """

        plan = structured_model.invoke(prompt)
        return plan

    def research(self, sub_question: str) -> str:
        """研究单个子问题"""
        print(f"\n正在研究子问题：{sub_question}\n")

        result = self.agent.invoke({
            "messages": [{
                "role": "user",
                "content": f"请搜索并分析关于“{sub_question}”的信息",
            }],
        })

        return result["messages"][-1].content

    def generate_report(
            self,
            question: str,
            findings: list[str]
    ) -> ResearchReport:
        """生成研究报告"""
        print(f"\n正在生成研究报告...\n")

        structured_model = self.model.with_structured_output(ResearchReport)

        findings_text = "\n\n".join([
            f"发现 {i+1}:\n{f}"
            for i, f in enumerate(findings)
        ])

        prompt = f"""
            请为以下研究问题生成结构化报告：

            研究问题：{question}

            发现：
            {findings_text}

            要求：
            1.撰写执行摘要
            2.整理关键发现（每个发现包含主题、要点、来源、置信度）
            3.得出结论
            4.提供建议
        """

        report = structured_model.invoke(prompt)
        report.generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return report

    def conduct_research(self, question: str) -> ResearchReport:
        """执行完整研究流程"""
        print(f"\n"+"="*80)
        print(f"正在进行研究：{question}")
        print(f"{"="*80}\n")

        # 1.制定计划
        plan = self.create_plan(question)

        print(f" 计划制定完成")
        print(f"研究方法：{plan.approach}")
        print(f"预计耗时：{plan.estimated_time}秒")
        print(f"\n子问题：")

        for i, sq in enumerate(plan.sub_questions, 1):
            print(f"{i}, [{sq.difficulty.upper()}] {sq.question}")

        # 2.逐个研究
        findings = []
        for i, sq in enumerate(plan.sub_questions, 1):
            print(f"\n {'='*80}")
            print(f"进度：{i}/{len(plan.sub_questions)}")
            print(f"{'='*80}")

            finding = self.research(sq.question)
            findings.append(finding)

        # 3.生成报告
        report = self.generate_report(question, findings)

        return report

def main():
    """主程序"""
    print("\n" + "=" * 80)
    print("智能研究助手（Langchain 1.0 Middleware）")
    print("=" * 80)

    assistant = ResearchAssistant()

    # 研究主题
    topic = "LangChain 1.0 Middleware 系统的核心特性和应用场景"

    # 执行研究
    report = assistant.conduct_research(topic)

    # 输出报告
    print("\n" + "=" * 80)
    print(f"研究报告：{report.generated_at}")
    print("=" * 80 + "\n")
    print(f"标题：{report.title}")
    print(f"\n摘要：\n{report.summary}")
    print("\n研究发现")
    for i, finding in enumerate(report.findings, 1):
        print(f"{i}. {finding.topic}")
        print(f"      置信度：{finding.confidence:.2f}")
        for point in finding.key_points:
            print(f"      · {point}")

    print(f"\n结论：\n{report.conclusions}")

    print("\n建议：")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"{i}. {rec}")

    print(f"\n生成时间：{report.generated_at}")

    # Windows file names cannot contain ':' characters.
    filename = f"research_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存为 {filename}\n")


if __name__ == "__main__":
    main()
