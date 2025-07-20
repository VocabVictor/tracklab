"""TrackLab SDK module - 本地日志库精简版."""

__all__ = (
    "Interface",
    "get_interface",
)

# 导入核心接口
from .interface.interface import Interface, get_interface