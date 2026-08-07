"""
    条件分支示例：根据输入选择不同路径
"""

import os
from pathlib import Path

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class State(TypedDict):
    input: str
    category: str
    result: str

def classify(state: State) -> State:
    """分类节点"""
    print("————分类中————")
    if "代码" in state["input"]:
        state["category"] = "code"
    elif "文章" in state["input"]:
        state["category"] = "article"
    else:
        state["category"] = "general"
    return state

def process_code(state: State) -> State:
    """处理代码请求"""
    print("处理代码.......")
    state["result"] = f"生成代码：{state['input']}"
    return state

def process_article(state: State) -> State:
    """处理文章请求"""
    print("处理文章.......")
    state["result"] = f"回答：{state['input']}"
    return state

def process_general(state: State) -> State:
    """处理一般请求"""
    print("处理一般请求.......")
    state["result"] = f"回答：{state['input']}"
    return state

# 条件路由函数
def route_by_category(state: State) -> Literal["code", "article", "general"]:
    """根据分类路由"""
    return state["category"]

# 构建图
workflow = StateGraph(State)

# 增加节点
workflow.add_node("classify", classify)
workflow.add_node("code", process_code)
workflow.add_node("article", process_article)
workflow.add_node("general", process_general)

# 设置入口
workflow.set_entry_point("classify")

# 添加条件边
workflow.add_conditional_edges(
    "classify",             # 从 classify 节点
    route_by_category,# 使用这个函数路由
    {
        "code": "code",     # 如果分类是 code，则到 code 节点
        "article": "article",  # 如果分类是 article，则到 article 节点
        "general": "general"   # 如果分类是 general，则到 general 节点
    }
)

# 所有路径都结束
workflow.add_edge("code", END)
workflow.add_edge("article", END)
workflow.add_edge("general", END)

# 编译
app = workflow.compile()

# 测试
test_inputs = [
    "写一个代码，冒泡排序",
    "写一个文章，关于机器学习",
    "今天天气"
]

# PowerShell cannot render an IPython image object. Save the graph as a PNG and
# open it with the default Windows image viewer.
image_path = Path(__file__).with_name("demo20_langGraph_workflow.png")
image_path.write_bytes(app.get_graph(xray=True).draw_mermaid_png())
print(f"工作流图已保存到：{image_path}")
os.startfile(image_path)

for inp in test_inputs:
    print(f"\n{'='*60}")
    print(f"输入：{inp}")
    result = app.invoke({"input": inp, "category": "", "result": ""})
    print(f"输出：{result['result']}")
