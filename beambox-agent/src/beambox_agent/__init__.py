"""包级公开入口：外部代码可直接 from beambox_agent import BeamboxAgent。"""

# 只暴露主 Agent 类，调用方不必了解 crew.py 的内部模块路径。
from .crew import BeamboxAgent

# __all__ 控制 from beambox_agent import * 时可见的名字。
__all__ = ["BeamboxAgent"]
# 语义化版本号，便于打包和问题定位。
__version__ = "0.1.0"
