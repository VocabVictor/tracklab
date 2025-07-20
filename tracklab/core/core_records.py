"""Core record types for TrackLab data storage.

This module contains the main data structures used for tracking experiments,
metrics, configurations, and other core TrackLab functionality.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid as uuid_lib

from .base_models import BaseModel, RecordInfo, StatsType, OutputType, RecordType


@dataclass
class HistoryItem(BaseModel):
    """History item (metric value)."""
    key: str
    nested_key: List[str] = field(default_factory=list)
    value_json: str = ""
    
    def get_value(self) -> Any:
        """Get the actual value."""
        if self.value_json:
            return json.loads(self.value_json)
        return None
    
    def set_value(self, value: Any):
        """Set the value."""
        self.value_json = json.dumps(value)


@dataclass
class HistoryStep(BaseModel):
    """History step information."""
    num: int = 0


@dataclass
class HistoryRecord(BaseModel):
    """History record for metrics."""
    item: List[HistoryItem] = field(default_factory=list)
    step: Optional[HistoryStep] = None
    _info: Optional[RecordInfo] = None
    
    def add_item(self, key: str, value: Any, nested_key: List[str] = None):
        """Add a history item."""
        item = HistoryItem(key=key, nested_key=nested_key or [])
        item.set_value(value)
        self.item.append(item)


@dataclass
class ConfigItem(BaseModel):
    """Configuration item."""
    key: str
    nested_key: List[str] = field(default_factory=list) 
    value_json: str = ""
    
    def get_value(self) -> Any:
        """Get the actual value."""
        if self.value_json:
            return json.loads(self.value_json)
        return None
    
    def set_value(self, value: Any):
        """Set the value."""
        self.value_json = json.dumps(value)


@dataclass
class ConfigRecord(BaseModel):
    """Configuration record."""
    update: List[ConfigItem] = field(default_factory=list)
    remove: List[ConfigItem] = field(default_factory=list)
    _info: Optional[RecordInfo] = None


@dataclass
class SummaryItem(BaseModel):
    """Summary item."""
    key: str
    nested_key: List[str] = field(default_factory=list)
    value_json: str = ""
    
    def get_value(self) -> Any:
        """Get the actual value."""
        if self.value_json:
            return json.loads(self.value_json)
        return None
    
    def set_value(self, value: Any):
        """Set the value."""
        self.value_json = json.dumps(value)


@dataclass
class SummaryRecord(BaseModel):
    """Summary record."""
    update: List[SummaryItem] = field(default_factory=list)
    remove: List[SummaryItem] = field(default_factory=list)
    _info: Optional[RecordInfo] = None


@dataclass
class GitRepoRecord(BaseModel):
    """Git repository information."""
    remote_url: str = ""
    commit: str = ""


@dataclass
class TelemetryRecord(BaseModel):
    """Telemetry information."""
    cli_version: str = ""
    python_version: str = ""
    os_name: str = ""
    os_version: str = ""
    env: Dict[str, str] = field(default_factory=dict)


@dataclass
class SettingsItem(BaseModel):
    """Settings item."""
    key: str
    value_json: str = ""
    
    def get_value(self) -> Any:
        """Get the actual value."""
        if self.value_json:
            return json.loads(self.value_json)
        return None
    
    def set_value(self, value: Any):
        """Set the value."""
        self.value_json = json.dumps(value)


@dataclass
class SettingsRecord(BaseModel):
    """Settings record."""
    item: List[SettingsItem] = field(default_factory=list)
    _info: Optional[RecordInfo] = None


@dataclass
class RunRecord(BaseModel):
    """Run record for local experiment tracking."""
    run_id: str = ""
    research_name: str = ""  # Research/paper name (was project)
    experiment_name: str = ""  # Experiment name (was run_group)
    config: Optional[ConfigRecord] = None
    summary: Optional[SummaryRecord] = None
    display_name: str = ""  # Human-readable run name
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    settings: Optional[SettingsRecord] = None
    host: str = ""
    starting_step: int = 0
    storage_id: str = ""
    start_time: Optional[datetime] = None
    resumed: bool = False
    telemetry: Optional[TelemetryRecord] = None
    runtime: int = 0
    git: Optional[GitRepoRecord] = None
    forked: bool = False
    
    def __post_init__(self):
        if not self.run_id:
            self.run_id = str(uuid_lib.uuid4())[:8]
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary with datetime parsing."""
        # Handle datetime fields
        if 'start_time' in data:
            if isinstance(data['start_time'], str):
                try:
                    data['start_time'] = datetime.fromisoformat(data['start_time'])
                except:
                    data['start_time'] = None
        
        # Call parent from_dict
        return super().from_dict(data)


# Artifact classes removed for local-only TrackLab


@dataclass
class MetricOptions(BaseModel):
    """Metric options."""
    step_sync: bool = True
    hidden: bool = False
    defined: bool = False


@dataclass
class MetricSummary(BaseModel):
    """Metric summary."""
    min: float = 0.0
    max: float = 0.0
    mean: float = 0.0
    best: float = 0.0


@dataclass
class MetricControl(BaseModel):
    """Metric control."""
    overwrite: bool = False


@dataclass
class MetricRecord(BaseModel):
    """Metric record."""
    name: str
    glob_name: str = ""
    step_metric: str = ""
    step_metric_index: int = 0
    options: Optional[MetricOptions] = None
    summary: Optional[MetricSummary] = None
    goal: str = ""  # min/max/target
    _control: Optional[MetricControl] = None
    expanded_from_glob: bool = False


@dataclass
class StatsItem(BaseModel):
    """Stats item."""
    key: str
    value_json: str = ""
    
    def get_value(self) -> Any:
        """Get the actual value."""
        if self.value_json:
            return json.loads(self.value_json)
        return None
    
    def set_value(self, value: Any):
        """Set the value."""
        self.value_json = json.dumps(value)


@dataclass
class StatsRecord(BaseModel):
    """Stats record."""
    stats_type: StatsType = StatsType.SYSTEM
    timestamp: Optional[datetime] = None
    item: List[StatsItem] = field(default_factory=list)
    _info: Optional[RecordInfo] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class FilesItem(BaseModel):
    """Files item."""
    path: str = ""


@dataclass
class FilesRecord(BaseModel):
    """Files record."""
    files: List[FilesItem] = field(default_factory=list)


@dataclass
class OutputRecord(BaseModel):
    """Output record."""
    output_type: OutputType = OutputType.STDOUT
    timestamp: Optional[datetime] = None
    line: str = ""
    _info: Optional[RecordInfo] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


@dataclass
class OutputRawRecord(BaseModel):
    """Output raw record."""
    pass


@dataclass
class Record(BaseModel):
    """Main record wrapper."""
    num: int = 0
    record_type: Optional[RecordType] = None
    control: Optional['Control'] = None  # Forward reference
    uuid: str = ""
    _info: Optional[RecordInfo] = None
    
    # Actual record data (one of these will be set)
    run: Optional[RunRecord] = None
    history: Optional[HistoryRecord] = None
    config: Optional[ConfigRecord] = None
    summary: Optional[SummaryRecord] = None
    output: Optional[OutputRecord] = None
    output_raw: Optional[OutputRawRecord] = None
    stats: Optional[StatsRecord] = None
    metric: Optional[MetricRecord] = None
    files: Optional['FilesRecord'] = None
    
    # Request/response records
    request: Optional['Request'] = None
    
    # Additional record types
    exit: Optional['RunExitRecord'] = None
    alert: Optional['AlertRecord'] = None
    final: Optional['FinalRecord'] = None
    header: Optional['HeaderRecord'] = None
    footer: Optional['FooterRecord'] = None
    preempting: Optional['RunPreemptingRecord'] = None
    environment: Optional['EnvironmentRecord'] = None
    
    # Telemetry (from different module)
    telemetry: Optional['TelemetryRecord'] = None
    
    def __post_init__(self):
        if not self.uuid:
            self.uuid = str(uuid_lib.uuid4())
        
        # Auto-detect record type
        if not self.record_type:
            if self.run:
                self.record_type = RecordType.RUN
            elif self.history:
                self.record_type = RecordType.HISTORY
            elif self.config:
                self.record_type = RecordType.CONFIG
            elif self.summary:
                self.record_type = RecordType.SUMMARY
            elif self.output:
                self.record_type = RecordType.OUTPUT
            elif self.output_raw:
                self.record_type = RecordType.OUTPUT
            elif self.stats:
                self.record_type = RecordType.STATS
            elif self.metric:
                self.record_type = RecordType.METRIC
            elif self.files:
                self.record_type = RecordType.FILES
            elif self.exit:
                self.record_type = RecordType.EXIT
            elif self.alert:
                self.record_type = RecordType.ALERT
            elif self.final:
                self.record_type = RecordType.FINAL
            elif self.header:
                self.record_type = RecordType.HEADER
            elif self.footer:
                self.record_type = RecordType.FOOTER


# Import types here to resolve forward references
from .base_models import Control
from .request_response import Request, HeaderRecord, RunExitRecord, AlertRecord, FinalRecord, FooterRecord, RunPreemptingRecord, EnvironmentRecord

# Update annotations
Record.__annotations__['control'] = Optional[Control]
Record.__annotations__['request'] = Optional[Request]
Record.__annotations__['exit'] = Optional[RunExitRecord]
Record.__annotations__['alert'] = Optional[AlertRecord]
Record.__annotations__['final'] = Optional[FinalRecord]
Record.__annotations__['header'] = Optional[HeaderRecord]
Record.__annotations__['footer'] = Optional[FooterRecord]
Record.__annotations__['preempting'] = Optional[RunPreemptingRecord]
Record.__annotations__['environment'] = Optional[EnvironmentRecord]