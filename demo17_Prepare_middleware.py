
import os
from typing import Any, NotRequired

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import FilesystemFileSearchMiddleware, HumanInTheLoopMiddleware, ModelCallLimitMiddleware, ModelRequest, ModelResponse, PIIMiddleware, Runtime, SummarizationMiddleware, ToolCallLimitMiddleware, ToolRetryMiddleware, before_model
from langchain.chat_models import init_chat_model
from langchain_core import messages
from langchain_core.messages import AIMessage


"""
    1.SummarizationMiddleware 对话历史总结
"""
agent = create_agent(
    model="qwen-plus",
    tools=[],
    middleware=[
        SummarizationMiddleware(
            model="qwen-plus",  #总结模型
            max_tokens_before_summary=400,
            messages_to_keep=5
        )
    ]
)

"""
    2.HumanInTheLoopMiddleware 人工审核
"""
agent = create_agent(
    model="qwen-plus",
    tools=[web_search, send_email], #敏感操作
    middleware=[
        HumanInTheLoopMiddleware(
            # 需要人工审核的工具
            tools_requiring_approval=["send_email"],
            # 或者所有工具都需要审核
            # require_approval_for_all_tools=True
        )
    ]
)

# 执行时会暂停等待人工确认
result = agent.invoke({"messages":[{"role": "user", "content": "你好！"}]})

"""
    3.ModelCallLimitMiddleware 模型调用限制
"""
limiter = ModelCallLimitMiddleware(
    thread_limit=20,                # 线程数限制 每个线程最多调用20次模型
    run_limit=10,                   # 运行数限制 每个运行最多调用10次模型
    exit_behavior="continue"        #达到限制后继续执行（不抛异常）
    )

agent = create_agent(
    model="qwen-plus",
    middleware=[limiter]
)

"""
    4.ToolCallLimitMiddleware 工具调用限制
"""
tool_limiter = ToolCallLimitMiddleware(
    tool_call_limit=50,              # 每个工具最多调用5次
    run_limit=20
)

agent = create_agent(
    model="qwen-plus",
    tools=[web_search, cakculator],
    middleware=[tool_limiter]
)

"""
    5.PIImiddleware 敏感信息保护

    策略：
        block：发现敏感信息后直接阻止请求或响应，不继续处理。适合身份证号、银行卡号、密钥等高风险数据。

        redact：删除敏感内容，通常替换为 [REDACTED]。例如：手机号是 [REDACTED]。

        mask：保留部分信息，其余用 * 隐藏，便于识别但不泄露完整值。例如：138****5678。

        hash：将敏感信息转换为固定的不可逆哈希值。相同原文会得到相同结果，适合去重、关联记录或审计，但不能直接恢复原始信息。
"""
pii_protector = PIIMiddleware(
    detection_model="qwen-plus",   # 敏感信息检测模型
    strategy="redact", # 策略：block，redact, mask, hash
    pii_type=["email", "phone", "ssn", "credit_card"]
)

agent = create_agent(
    model="qwen-plus",
    middleware=[pii_protector],
    tools=[]
)

# 输入包含敏感信息会自动处理
result = agent.invoke({
    "messages":[{
        "role": "user",
        "content": "我的邮箱是 user@example.com，手机号是 13812345678，身份证号是 123456789012345678"
        }]
    })


"""
    6.ModelFallbackMiddleware 模型降级
"""
primary_model = init_chat_model("openai", "gpt-3.5-turbo")
fallback_models = [
    init_chat_model("openai::gpt-3.5-turbo-0301"),
    init_chat_model("openai::gpt-3.5-turbo-0613"),
    init_chat_model("anthropic::claude-2.0-beta")
]

fallback = ModelCallLimitMiddleware(
    fallback_models=fallback_models
)

agent = create_agent(
    model=primary_model,
    middleware=[fallback],
    tools=[]
)

"""
    7.ToolRetryMiddleware 工具重试
    策略：
        retry_on_error：遇到错误时重试，直到成功或达到最大重试次数。

        retry_on_timeout：遇到超时错误时重试，直到成功或达到最大重试次数。

        retry_on_tool_error：遇到工具错误时重试，直到成功或达到最大重试次数。

        retry_on_tool_timeout：遇到工具超时错误时重试，直到成功或达到最大重试次数。

    自动重试失败的工具调用

    第一次重试（retry_number = 1）:等待~1.0(2.0**1)=2.0秒后重试
    第二次重试（retry_number = 2）:等待~2.0(2.0**2)=4.0秒后重试
    第三次重试（retry_number = 3）:等待~4.0(2.0**3)=8.0秒后重试
    第四次重试（retry_number = 4）:等待~8.0(2.0**4)=16.0秒后重试
    如果backoff_factor=0，就意味着不使用指数增长，重试之间始终用固定的initial_delay
"""
retry = ToolRetryMiddleware(
    max_retries=3,
    backoff_factor=2.0, #指数退避因子
    retry_on_exception=[ConnectionError, TimeoutError]
)

agent = create_agent(
    model="qwen-plus",
    tools=[web_search, api_call],
    middleware=[retry]
)

"""
    8.FilesystemFileSearchMiddleware 文件系统搜索
"""
file_search = FilesystemFileSearchMiddleware(
    root_dir="/workspace/project",          # 搜索根目录
    file_extensions=[".py", ".md", ",js"],   # 允许的文件类型
    max_results=50
)

agent = create_agent(
    model="qwen-plus",
    tools=[], #自动添加Glob和Grep工具
    middleware=[file_search]
)

# Agent 现在可以搜索文件
result = agent.invoke({
    "messages":[{
        "role": "user",
        "content": "搜索文件，包含关键字 'agent'"
        }]
    })

"""
    9.LLMToolSelectorMiddleware 智能工具筛选
"""


"""
    组合多个Middleware

    Middleware 可以叠加使用，执行顺序：
    进入：[MW1 before] -> [MW2 before] -> [MW3 before] -> 模型调用
    返回：[MW3 after] -> [MW2 after] -> [MW1 after]
"""
agent = create_agent(
    model="qwen-plus",
    tools=[web_search, calculator],
    middleware=[
        PIIMiddleware(strategy="redact"),                           #1.最先检查PII
        ModelCallLimitMiddleware(run_limit=10),                     #2.限制调用次数
        SummarizationMiddleware(max_tokens_before_summary=500),     #3.总结历史
        ToolRetryMiddleware(max_retries=3),                         #4.重试工具
    ]
    
)

"""高级Middleware模式"""

"""
    1.自定义状态（Custom State）
    扩展AgentState添加自定义字段
"""
# 1.定义自定义状态
class CustomState(AgentState):
    """扩展状态，添加自定义字段"""
    model_call_count: NotRequired[int]
    user_id: NotRequired[str]
    user_perferences: NotRequired[dict]

# 2.使用自定义状态
@before_model(state_schema=CustomState, can_jump_to=["end"])
def check_user_quota(
    state: CustomState,
    runtime: Runtime
) -> dict[str, Any] | None:
    """检查用户配额"""
    user_id = state.get("user_id", "anonymous")
    call_count = state.get("model_call_count", 0)

    # 假设用户有配额限制
    user_quota = 100

    if call_count >= user_quota:
        print(f"用户 {user_id} 的调用次数已超过限制，请升级会员")
        return {
            "jump_to": "end",
            "message": [AIMessage(content="您的配额已用完，请升级会员。")]
        }

    # 更新计数
    return {"model_call_count": call_count + 1}

# 3.创建Agent时指定状态 schema
agent = create_agent(
    model="qwen-plus",
    tools=[],
    middleware=[check_user_quota],
    state_schema=CustomState        #指定自定义状态
)

# 4.调用时传入自定义状态
result = agent.invoke({
    "messages":[{
        "role": "user",
        "content": "你好"
        }],

        "user_id": "user1123",
        "model_call_count": 95
    },
)

"""
    2.动态模型选择
"""

load_dotenv()

class DynamicModelSelector:
    """动态模型选择器"""

    def __init__(self):
        # 初始化不同级别的模型
        self.simple_model = init_chat_model(
            "qwen-plus",
            model_provider="openai",
            base_url=os.getenv(
                "OPENAI_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            api_key=os.getenv("OPENAI_API_KEY")or os.getenv("DASH_SCOPE_API_KEY"),
        )

        self.advanced_model = init_chat_model(
            "qwen-plus-pro",
            model_provider="openai",
            base_url=os.getenv(
                "OPENAI_BASE_URL",
                "https://dashscope.aliyuncs.com/compatible-mode/v1",
            ),
            api_key=os.getenv("OPENAI_API_KEY")or os.getenv("DASH_SCOPE_API_KEY"),  
        )

    def estimate_complexity(self, input: list) -> str:
        """估算查询复杂度"""
        if not messages:
            return "simple"

        last_message = str(messages[-1])

        # 简单规则判断
        complex_keywords = ["分析", "为什么", "如何", "原理", "详细", "复杂"]

        if any(kw in last_message for kw in complex_keywords):
            return "complex"

        # 消息长度判断
        if len(last_message) > 100:
            return "complex"

        return "simple"

    def create_hook(self):
        """创建动态选择钩子"""


"""
    4.Anthropic Prompt Caching
    利用Antropic的提示词缓存功能，大幅降低成本（适用于Claude模型）
"""
from langchain_anthropic import ChatAnthropic

def enable_prompt_caching(
        request: ModelRequest,
        handler: callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """
    为Anthropic模型启用Prompt Caching

    工作原理：
    1.在系统消息中添加缓存标记
    2.后续相同的系统消息会复用缓存
    3.可节省高达90%的输入token成本
    """

    # 只对 Anthropic 模型生效
    if isinstance(request.model, ChatAnthropic):
        # 修改系统消息，添加缓存标记
        if request.system_message:
            # 为系统消息的最后一个内容块添加缓存标记
            content_blocks = list(request.system_message.content_blocks)
            if content_blocks:
                content_blocks[-1]["cache_control"] = {"type": "ephemeral"}

                new_system_message = request.system_message.cope()
                new_system_message.content = content_blocks

                modified_request = request.override(system_message=new_system_message)
                return handler(modified_request)

    return handler(request)

anthropic_model = ChatAnthropic(
    model = "claude-3.5",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

agent = create_agent(
    model=anthropic_model,
    tools=[],
    middleware=[enable_prompt_caching],
)