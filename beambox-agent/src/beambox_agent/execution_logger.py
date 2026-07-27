"""创建带文件轮转的执行日志，记录工具调用但不记录 API Key。"""

from __future__ import annotations

# logging：Python 标准日志框架；RotatingFileHandler：限制单个日志文件大小。
import logging
from logging.handlers import RotatingFileHandler
# Path：以跨平台方式创建 logs 目录。
from pathlib import Path


def setup_logging(verbose: bool = False) -> logging.Logger:
    """初始化项目 logger；重复调用时复用已有 handler，避免日志重复写入。"""

    logger = logging.getLogger("beambox_agent")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    if logger.handlers:
        return logger

    # 日志放在启动目录下，便于命令行和 Gradio 使用同一套路径。
    log_dir = Path.cwd() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    # 单文件达到 1 MB 后轮转，最多保留 3 份旧日志。
    handler = RotatingFileHandler(
        log_dir / "execution.log",
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
    )
    logger.addHandler(handler)
    return logger
