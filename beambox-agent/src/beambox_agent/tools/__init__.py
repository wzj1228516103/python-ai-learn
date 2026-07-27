# 重导出常用工具类，让其他模块只依赖 beambox_agent.tools 这一稳定入口。
from .beambox_tool import BeamboxCompanyTool, BeamboxDocsTool, ToolRegistry

# BeamboxDocsTool 是旧名称兼容别名；新代码应优先使用 BeamboxCompanyTool。
__all__ = ["BeamboxCompanyTool", "BeamboxDocsTool", "ToolRegistry"]
