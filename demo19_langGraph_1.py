
from typing import TypedDict
from pathlib import Path
import os

from langgraph.graph import END, StateGraph
from langchain_core.runnables.graph import MermaidDrawMethod


# 1.定义状态
class State(TypedDict):
    input: str
    step1_output: str
    step2_output: str
    final_output: str

# 2.定义节点函数
def step1(state: State) -> State:
    """步骤1：处理输入"""
    print("执行 Step 1...")
    state["step1_output"] = f"[Step1 处理] {state['input']}"
    return state

def step2(state: State) -> State:
    """第二步：进一步处理"""
    print("执行 Step 2...")
    state["step2_output"] = f"[Step2 处理] {state['step1_output']}"
    return state

def step3(state: State) -> State:
    """第三步：生成最终结果"""
    print("执行 Step 3...")
    state["final_output"] = f"[Step3 完成] {state['step2_output']}"
    return state

# 3.构建图
workflow  = StateGraph(State)

# 增加节点
workflow.add_node("step1", step1)
workflow.add_node("step2", step2)
workflow.add_node("step3", step3)

# 增加边
workflow.add_edge("step1", "step2")
workflow.add_edge("step2", "step3")
workflow.add_edge("step3", END)

# 设置入口
workflow.set_entry_point("step1")

# 编译
app = workflow.compile()

# 执行
print("开始执行工作流...\n")
result = app.invoke({"input": "Hello, World!"})

print(f"\n最终结果：\n{result['final_output']}\n")

# A PowerShell terminal cannot render IPython.display.Image. Save the graph as a
# PNG file and open it with the default Windows image viewer instead.
image_path = Path(__file__).with_name("demo19_langGraph_workflow.png")
image_path.write_bytes(
    app.get_graph(xray=True).draw_mermaid_png(draw_method=MermaidDrawMethod.API)
)
print(f"工作流图已保存到：{image_path}")
os.startfile(image_path)
