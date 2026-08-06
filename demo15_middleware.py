"""
最简单的 Middleware 示例
"""
from datetime import datetime, time
import hashlib
import json
import os
from typing import Any, Callable

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse, ToolCallRequest, before_model, after_model, AgentState, dynamic_prompt, wrap_model_call
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, SystemMessage
from langgraph.runtime import Runtime

# 1.定义 before_model 钩子
@before_model
def log_before(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """在每次调用模型前打印日志"""
    print(f"before model准备调用模型，当前消息数：{len(state['messages'])}")
    return None

# 2.定义 after_model 钩子
@after_model
def log_after(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """在每次调用模型后打印日志"""
    last_message = state["messages"][-1]
    print(f"after model调用模型响应：{last_message.content[:50]}...")
    return None

load_dotenv()

# 3.创建模型
model = init_chat_model(
    model="qwen-plus",
    model_provider="openai",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
)

# 4.创建Agent（添加middleware）
agent = create_agent(
    model=model,
    tools=[],
    middleware=[log_before, log_after] #添加中间件
)

# # 5.测试
# result = agent.invoke({"messages":[{"role": "user", "content": "你好！"}]})
# print(result)
# print(f"\n最终结果：{result['messages'][-1].content}")

"""
    示例1：消息数量限制
"""
@before_model(can_jump_to=["end"])  #声明可以跳转到"end"
def check_message_limit(
        state: AgentState,
        runtime: Runtime
) -> dict[str, Any] | None:
    """限制对话轮次，超过50轮自动结束"""
    if len(state["messages"]) >= 50:
        print("对话已达上限，自动结束")
        return {
            "message":[AIMessage(content="对话已达上限，感谢使用！")],
            "jump_to": "end" #跳转到结束节点
        }
    return None

"""
    示例2：统计Token使用
"""

class TokenCounter:
    """Token 计数器"""
    def __init__(self):
        self.token_counts = 0

    def create_hook(self):
        """创建钩子闭包"""
        @after_model
        def count_tokens(
            state: AgentState,
            runtime: Runtime
        ) -> dict[str, Any] | None:
            # 从模型响应中提取token使用情况
            last_message = state["messages"][-1]
            if hasattr(last_message, "token_usage"):
                usage = last_message.response_metadata.get("usage", {})
                tokens = usage.get("total_tokens", 0)
                self.total_tokens += tokens
                print(f"本次使用 {tokens} tokens,累计 {self.total_tokens} tokens")
            return None

"""

    @wrap_model_call包裹模型调用

"""


"""
    示例1：重试逻辑
"""
@wrap_model_call
def retry_model(
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """自动重试失败的模型调用"""
    max_retries = 3

    for attempt in range(max_retries):
        try:
            print(f"尝试调用模型，第 {attempt+1}/{max_retries} 次")
            return handler(request)
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"所有重试失败：{e}")
                raise

            # 指数退避
            wait_time = 2 ** attempt
            print(f"调用失败：{e}，{wait_time} 秒后重试...")
            time.sleep(wait_time)

"""
    示例2：响应缓存
"""
class ModelCache:
    """模型响应缓存"""
    def __init__(self):
        self.cache = {}

    def create_hook(self):
        """创建钩子闭包"""
        @wrap_model_call
        def cache_model(
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
        ) -> ModelResponse:
            
            # 生成缓存键
            cache_key = hashlib.md5(
                json.dumps({
                    "messages": [str(m) for m in request.messages],
                    "system": str(request.system_message)
                }).encode()
            ).hexdigest()

            # 检查缓存
            if cache_key in self.cache:
                print(f"缓存命中！！！命中缓存：{cache_key}")
                return self.cache[cache_key]

            # 调用模型
            print("缓存未命中，调用模型")
            response = handler(request)

            # 存入缓存
            self.cache[cache_key] = response
            return response

        return cache_model

"""
    示例3：修改系统提示
"""
@wrap_model_call
def add_context(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse]
) -> ModelResponse:
    """动态添加上下文信息到系统提示"""

    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 构建新的系统消息
    original_content = request.system_message.content if request.system_message else ""
    new_content = f"""
    {original_content}
    当前时间：{current_time}

    用户位置：中国
    语言偏好：中文
    """

    # 创建新的系统消息
    new_system_message = SystemMessage(content=new_content)

    # 使用override方法修改请求
    modified_request = request.override(system_message=new_system_message)

    return handler(modified_request)

"""
    @dynamic_prompt 动态系统提示
"""
@dynamic_prompt
def user_role_prompt(request: ModelRequest) -> str:
    """根据用户角色生成不同的系统提示"""

    # 从runtime context获取用户角色
    user_role = request.runtime.context.get("user_role", "user")

    base_prompt = "你是一个专业的AI助手"

    if user_role == "expert":
        return f"{base_prompt}\n请提供详细的技术解释，使用专业术语。"
    elif user_role == "beginner":
        return f"{base_prompt}\n请使用易懂的文字，适合初学者。"
    elif user_role == "child":
        return f"{base_prompt}\n请使用更简单的语言，适合儿童，使用比喻和故事。"
    else:
        return base_prompt

# 使用时传入 context
agent = create_agent(
    model=model,
    middleware=[user_role_prompt],
    tools=[]
)

# 调用时指定用户角色
result = agent.invoke(
    {"messages": [{"role": "user", "content": "什么是人工智能"}]},
    config=({"configurable": {"user_role": "child"}})
)

# 测试user_role_prompt
if __name__ == "__main__":
    print(user_role_prompt(None))

"""
    创建（类式）自定义Middleware
"""

class CustomMiddleware(AgentMiddleware):
    """自定义中间件基础模板"""

    def __init__(self, config: dict = None):
        """初始化配置"""
        self.config = config or {}

    def before_agent(
            self,
            state: AgentState,
            runtime: Runtime,
    ) -> dict[str, Any] | None:
        """Agent 开始前执行"""
        return None

    def before_model(
            self,
            state: AgentState,
            runtime: Runtime,
    ) -> dict[str, Any] | None:
        """模型调用前执行"""
        return None

    def modify_model_request(
            self,
            request: ModelRequest,
    ) -> ModelRequest:
        """修改模型请求"""
        return request

    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        """包裹模型调用"""
        return handler(request)

    def after_model(
            self,
            state: AgentState,
            runtime: Runtime,
    ) -> dict[str, Any] | None:
        """模型响应后执行"""
        return None

    def wrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest], ToolCallRequest]
    ) -> ToolCallRequest:
        """包裹工具调用"""
        return handler(request)

    def after_tool(
            self,
            state: AgentState,
            runtime: Runtime,
    ) -> dict[str, Any] | None:
        """Agent 结束后执行"""
        return None