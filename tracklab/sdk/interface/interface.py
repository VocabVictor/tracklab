"""TrackLab 本地接口 - 直接操作本地数据存储"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Any, Dict

from tracklab.core import (
    DataStore, get_data_store,
    RunRecord, HistoryRecord, ConfigRecord, SummaryRecord, 
    MetricRecord, OutputRecord, StatsRecord, FilesRecord,
    HistoryItem, ConfigItem, SummaryItem, StatsItem, FilesItem,
    Record, RecordType
)
from datetime import datetime

if TYPE_CHECKING:
    from tracklab.sdk.run import Run

logger = logging.getLogger(__name__)


def get_staging_dir() -> str:
    """获取临时文件暂存目录"""
    staging_dir = Path.cwd() / ".tracklab" / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    return str(staging_dir)


class Interface:
    """TrackLab 本地接口
    
    直接操作本地数据存储，为本地日志库优化设计。
    架构：用户 → Interface → DataStore（本地）
    """
    
    def __init__(self, data_store: Optional[DataStore] = None, force_new: bool = False):
        """初始化接口
        
        Args:
            data_store: 数据存储实例，如果为None则使用默认存储
            force_new: 是否强制创建新的数据存储
        """
        self.data_store = data_store or get_data_store(force_new=force_new)
        self._current_run: Optional[RunRecord] = None
        
    def set_current_run(self, run: RunRecord) -> None:
        """设置当前运行"""
        self._current_run = run
        
    def get_current_run(self) -> Optional[RunRecord]:
        """获取当前运行"""
        return self._current_run
        
    # === 核心发布方法 ===
    
    def publish_run(self, run: RunRecord) -> None:
        """发布运行记录"""
        record = Record(run=run)
        self.data_store.write_record(record)
        self.set_current_run(run)
        logger.debug(f"Published run: {run.run_id}")
        
    def publish_config(self, key: str, value: Any, nested_key: Optional[list] = None) -> None:
        """发布配置"""
        config_item = ConfigItem(key=key, nested_key=nested_key or [])
        config_item.set_value(value)
        
        config_record = ConfigRecord(update=[config_item])
        record = Record(config=config_record)
        self.data_store.write_record(record)
        logger.debug(f"Published config: {key} = {value}")
        
    def publish_metric(self, name: str, value: Any, step: Optional[int] = None) -> None:
        """发布指标"""
        # 记录历史数据
        history_item = HistoryItem(key=name)
        history_item.set_value(value)
        
        history_record = HistoryRecord(item=[history_item])
        if step is not None:
            from tracklab.core.core_records import HistoryStep
            history_record.step = HistoryStep(num=step)
            
        record = Record(history=history_record)
        self.data_store.write_record(record)
        logger.debug(f"Published metric: {name} = {value} (step={step})")
        
    def publish_summary(self, key: str, value: Any, nested_key: Optional[list] = None) -> None:
        """发布摘要数据"""
        summary_item = SummaryItem(key=key, nested_key=nested_key or [])
        summary_item.set_value(value)
        
        summary_record = SummaryRecord(update=[summary_item])
        record = Record(summary=summary_record)
        self.data_store.write_record(record)
        logger.debug(f"Published summary: {key} = {value}")
        
    def publish_output(self, line: str, output_type: str = "stdout") -> None:
        """发布输出"""
        from tracklab.core.base_models import OutputType
        
        output_type_enum = OutputType.STDOUT if output_type == "stdout" else OutputType.STDERR
        output_record = OutputRecord(line=line, output_type=output_type_enum)
        record = Record(output=output_record)
        self.data_store.write_record(record)
        logger.debug(f"Published output [{output_type}]: {line[:100]}...")
        
    def publish_stats(self, stats_dict: Dict[str, Any], stats_type: str = "system") -> None:
        """发布统计信息"""
        from tracklab.core.base_models import StatsType
        
        stats_type_enum = getattr(StatsType, stats_type.upper(), StatsType.SYSTEM)
        
        items = []
        for key, value in stats_dict.items():
            item = StatsItem(key=key)
            item.set_value(value)
            items.append(item)
            
        stats_record = StatsRecord(stats_type=stats_type_enum, item=items)
        record = Record(stats=stats_record)
        self.data_store.write_record(record)
        logger.debug(f"Published stats: {len(stats_dict)} items")
        
    def publish_files(self, file_paths: list) -> None:
        """发布文件列表"""
        files = [FilesItem(path=path) for path in file_paths]
        files_record = FilesRecord(files=files)
        record = Record(files=files_record)
        self.data_store.write_record(record)
        logger.debug(f"Published files: {len(file_paths)} files")
        
    # === 便捷方法（兼容旧接口） ===
    
    def publish_history(self, data: Dict[str, Any], step: Optional[int] = None) -> None:
        """发布历史数据（批量指标）"""
        for key, value in data.items():
            self.publish_metric(key, value, step)
            
    def publish_alert(self, title: str, text: str, level: str = "INFO") -> None:
        """发布警告"""
        self.log(f"ALERT [{level}] {title}: {text}")
        logger.warning(f"Alert [{level}] {title}: {text}")
        
    def log(self, message: str) -> None:
        """记录日志消息"""
        self.publish_output(f"[{datetime.now().isoformat()}] {message}")
        
    def log_dict(self, data: Dict[str, Any], step: Optional[int] = None) -> None:
        """批量记录指标字典"""
        for key, value in data.items():
            self.publish_metric(key, value, step)
            
    def update_config(self, config_dict: Dict[str, Any]) -> None:
        """批量更新配置"""
        for key, value in config_dict.items():
            self.publish_config(key, value)
            
    def update_summary(self, summary_dict: Dict[str, Any]) -> None:
        """批量更新摘要"""
        for key, value in summary_dict.items():
            self.publish_summary(key, value)
            
    def publish_tbdata(self, log_dir: str, save: bool, root_logdir: str = "") -> None:
        """发布 TensorBoard 数据（本地模式简化版）"""
        self.log(f"TensorBoard: {log_dir} (save={save}, root={root_logdir})")
        
    def publish_preempting(self) -> None:
        """发布抢占信号（本地模式无操作）"""
        pass
        
    # === 查询方法 ===
    
    def get_run_history(self, run_id: Optional[str] = None) -> list:
        """获取运行历史"""
        if run_id is None and self._current_run:
            run_id = self._current_run.run_id
            
        records = []
        for record in self.data_store.scan_records(RecordType.HISTORY):
            # 这里可以添加过滤逻辑
            records.append(record)
        return records
        
    def get_latest_metrics(self) -> Dict[str, Any]:
        """获取最新指标"""
        metrics = {}
        for record in self.data_store.scan_records(RecordType.HISTORY):
            if record.history:
                for item in record.history.item:
                    metrics[item.key] = item.get_value()
        return metrics
        
    def close(self) -> None:
        """关闭接口"""
        if hasattr(self.data_store, 'close'):
            self.data_store.close()
        logger.debug("Interface closed")


# 全局实例
_interface: Optional[Interface] = None


def get_interface(force_new: bool = False) -> Interface:
    """获取接口实例
    
    Args:
        force_new: 是否强制创建新实例
    """
    global _interface
    if force_new or _interface is None:
        if _interface is not None:
            try:
                _interface.close()
            except:
                pass
        _interface = Interface(force_new=force_new)
    return _interface


def set_interface(interface: Interface) -> None:
    """设置全局接口实例"""
    global _interface
    _interface = interface


# 向后兼容的别名
InterfaceBase = Interface