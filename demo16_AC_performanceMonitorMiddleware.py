from datetime import datetime, time
import json
from typing import Any, Callable

from langchain.agents import AgentState
from langchain_core.messages import ToolMessage
from langgraph.runtime import Runtime
from langchain.agents.middleware import ModelRequest, ModelResponse, ToolCallRequest
from langgraph.types import Command

class PerformanceMonitorMiddleware:
    """性能监控中间件"""
    def __init__(self, log_file: str = "agent_performance.json1"):
        self.log_file = log_file
        self.session_start = None
        self.model_call_count = 0
        self.tool_call_count = 0
        self.total_model_time = 0.0
        self.total_tool_time = 0.0

    def before_agent(
            self,
            state: AgentState,
            runtime: Runtime
    ) -> dict[str, dict] | None:
        """记录会话开始"""
        self.session_start = time.time()
        print(f"开始会话，当前消息数：{len(state['messages'])}，时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.session_start))}")
        return None

    def wrap_model_call(
            self,
            request: ModelRequest,
            handler: Callable[[ModelRequest], ModelResponse]
    ) -> ModelResponse:
        """监控模型调用"""
        start = time.time()
        self.model_call_count += 1

        try:
            response = handler(request)
            elapsed = time.time() - start
            self.total_model_time += elapsed

            print(f"模型调用{self.model_call_count}完成，耗时：{elapsed:.2f}秒，当前消息数：{len(request.messages)}")
            return response
        except Exception as e:
            elapsed = time.time() - start
            print(f"模型调用出错，耗时：{elapsed:.2f}秒")
            raise


    def wrap_tool_call(
            self,
            request: ToolCallRequest,
            handler: Callable[[ToolCallRequest], ToolMessage | Command]
    ) -> ToolMessage | Command:
        """监控工具调用"""
        start = time.time()
        self.tool_call_count += 1
        tool_name = request.tool_call["name"]

        try:
            result = handler(request)
            elapsed = time.time() - start
            self.total_tool_time += elapsed

            print(f"工具调用{self.tool_call_count}完成，耗时：{elapsed:.2f}秒，工具名称：{tool_name}")
            return result
        except Exception as e:
            elapsed = time.time() - start
            print(f"工具调用出错，耗时：{elapsed:.2f}秒，工具名称：{tool_name}")
            raise

    def after_agent(
            self,
            state: AgentState,
            runtime: Runtime
    ) -> dict[str, Any] | None:
        """输出性能统计"""
        total_time = time.time() - self.session_start

        stats = {
            "timestamp": datetime.now().isoformat(),
            "total_time": round(total_time, 2),
            "model_calls": self.model_call_count,
            "tool_calls": self.tool_call_count,
            "avg_model_time": round(self.total_model_time / max(self.model_call_count, 1), 2),
            "avg_tool_time": round(self.total_tool_time / max(self.tool_call_count, 1), 2),
        }

        print("\n"+"="*80)
        print("性能统计")
        print("="*80)
        print(f"总耗时：{stats['total_time']:.2f}秒")
        print(f"模型调用: {stats['model_calls']} 次，平均耗时：{stats['avg_model_time']:.2f}秒")
        print(f"工具调用: {stats['tool_calls']} 次，平均耗时：{stats['avg_tool_time']:.2f}秒")
        print(f"总耗时：{stats['total_time']:.2f}秒")
        print("="*80)

        # 写入日志文件
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(stats, ensure_ascii=False) + "\n")

        return None