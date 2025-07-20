"""TrackLab - 本地实验日志库

轻量级本地实验跟踪工具，专注于本地存储和实验管理。
"""

__version__ = "0.0.5"

# 核心接口
from tracklab.sdk.interface.interface import Interface, get_interface
from tracklab.core import DataStore, get_data_store

# 导出主要API
__all__ = [
    "Interface",
    "get_interface", 
    "DataStore",
    "get_data_store",
]

# 便捷的全局接口实例
interface = None
_current_run = None

# 便捷方法
def init(project: str = None, name: str = None, research_name: str = None, 
         experiment_name: str = None, **kwargs) -> "Run":
    """初始化TrackLab实验 (兼容 wandb API)
    
    Args:
        project: 项目名称 (wandb 兼容参数，映射到 research_name)
        name: 运行名称 (wandb 兼容参数，映射到 experiment_name)
        research_name: 研究项目名称 (TrackLab 原生参数)
        experiment_name: 实验名称 (TrackLab 原生参数)
        **kwargs: 其他参数
        
    Returns:
        Run 对象
    """
    global interface, _current_run, run, config, summary
    
    # 处理 wandb 风格的参数
    if project is not None:
        research_name = project
    if name is not None:
        experiment_name = name
        
    # 默认值
    if research_name is None:
        research_name = "default-project"
    if experiment_name is None:
        experiment_name = "default-experiment"
    
    # 如果之前的运行还在，先关闭它
    if interface is not None:
        try:
            interface.close()
        except:
            pass
    
    # 获取新的接口实例（强制创建新的以避免数据库关闭问题）
    interface = get_interface(force_new=True)
    
    from tracklab.core import RunRecord
    
    run_record = RunRecord(
        research_name=research_name,
        experiment_name=experiment_name,
        **kwargs
    )
    interface.publish_run(run_record)
    
    # 创建 Run 对象以兼容 wandb.run
    _current_run = Run(interface, research_name, experiment_name)
    run = _current_run
    
    # 创建 config 和 summary 对象以兼容 wandb.config/wandb.summary
    config = Config(interface)
    summary = Summary(interface)
    
    return _current_run

def log(data: dict, step: int = None) -> None:
    """记录指标数据"""
    if interface is None:
        raise RuntimeError("必须先调用 tracklab.init() 或 wandb.init()")
    interface.log_dict(data, step)

# config 和 summary 现在是对象，不是函数
# 保留旧的函数接口用于向后兼容
def update_config(data: dict) -> None:
    """设置配置（已废弃，请使用 tracklab.config.update()）"""
    if config is None:
        raise RuntimeError("必须先调用 tracklab.init()")
    config.update(data)

def update_summary(data: dict) -> None:
    """设置摘要（已废弃，请使用 tracklab.summary.update()）"""
    if summary is None:
        raise RuntimeError("必须先调用 tracklab.init()")
    summary.update(data)

def finish() -> None:
    """结束实验"""
    global interface, run, config, summary
    if interface is not None:
        interface.close()
        interface = None
        run = None
        config = None
        summary = None

def teardown() -> None:
    """清理TrackLab资源（测试兼容性）"""
    # For local-only TrackLab, teardown is a no-op
    pass

# Backward compatibility aliases
Settings = dict  # For test compatibility
termlog = lambda *args, **kwargs: None
termwarn = lambda *args, **kwargs: None  
termerror = lambda *args, **kwargs: None
termsetup = lambda *args, **kwargs: None

# Additional compatibility functions
save = lambda *args, **kwargs: None
watch = lambda *args, **kwargs: None
unwatch = lambda *args, **kwargs: None
define_metric = lambda *args, **kwargs: None
alert = lambda *args, **kwargs: None

# Add missing exceptions for test compatibility
class UsageError(Exception):
    """User error exception"""
    pass

class Error(Exception):
    """Base error exception"""
    pass

# Global variables for backwards compatibility
run = None
config = None
summary = None


class Run:
    """wandb.run 兼容对象"""
    def __init__(self, interface, project, name):
        self.interface = interface
        self.project = project
        self.name = name
        self.id = interface.run_id if hasattr(interface, 'run_id') else None
        
    def finish(self):
        """结束运行"""
        self.interface.close()


class Config:
    """wandb.config 兼容对象"""
    def __init__(self, interface):
        self._interface = interface
        self._data = {}
        
    def update(self, data: dict):
        """更新配置"""
        self._data.update(data)
        self._interface.update_config(data)
        
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self._interface.update_config({name: value})
            
    def __getattr__(self, name):
        return self._data.get(name)
        
    def __setitem__(self, key, value):
        self._data[key] = value
        self._interface.update_config({key: value})
        
    def __getitem__(self, key):
        return self._data[key]


class Summary:
    """wandb.summary 兼容对象"""
    def __init__(self, interface):
        self._interface = interface
        self._data = {}
        
    def update(self, data: dict):
        """更新摘要"""
        self._data.update(data)
        self._interface.update_summary(data)
        
    def __setattr__(self, name, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
            self._interface.update_summary({name: value})
            
    def __getattr__(self, name):
        return self._data.get(name)
        
    def __setitem__(self, key, value):
        self._data[key] = value
        self._interface.update_summary({key: value})
        
    def __getitem__(self, key):
        return self._data[key]