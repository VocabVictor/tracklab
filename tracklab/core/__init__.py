"""Core module for tracklab - replaces protobuf with simple Python models."""

# Import from new modular structure
from .base_models import (
    BaseModel, RecordType, StatsType, OutputType,
    RecordInfo, Control
)

from .core_records import (
    Record, RunRecord, HistoryRecord, SummaryRecord, ConfigRecord,
    OutputRecord, OutputRawRecord, StatsRecord, MetricRecord, FilesRecord, FilesItem,
    HistoryItem, HistoryStep, ConfigItem, SummaryItem, StatsItem,
    MetricOptions, MetricSummary, MetricControl,
    GitRepoRecord, TelemetryRecord, SettingsRecord, SettingsItem
)

from .request_response import (
    Request, Response, Result, StatusRequest, HeaderRecord,
    RequestInfo, ResultInfo, CancelRequest, PartialHistoryRequest,
    TBRecord, RunPreemptingRecord, EnvironmentRecord, JobInputRequest,
    GetSummaryRequest, PauseRequest, ResumeRequest, StopStatusRequest,
    InternalMessagesRequest, NetworkStatusRequest, OperationStatsRequest,
    PollExitRequest, SampledHistoryRequest, RunStartRequest, CheckVersionRequest,
    DeferRequest, AttachRequest, ServerInfoRequest, KeepaliveRequest,
    RunStatusRequest, SenderMarkRequest, SenderReadRequest, SyncFinishRequest,
    StatusReportRequest, SummaryRecordRequest, TelemetryRecordRequest,
    GetSystemMetricsRequest, PythonPackagesRequest, RunFinishWithoutExitRequest,
    ShutdownRequest, RunExitRecord, AlertRecord, FinalRecord, FooterRecord,
)

# Import from other core modules
from .storage import *
from .interface import *
from .request_types import *
from .progress_types import *


# Import research/experiment management utilities
from .utils import (
    parse_research_path,
    list_researches,
    list_experiments,
    get_experiment_runs,
    find_latest_run,
    get_research_summary,
    validate_research_name,
    validate_experiment_name,
)

# Also import from the old data_types.py for backward compatibility
# (will be removed once fully migrated)
try:
    from .data_types import *
except ImportError:
    pass

__all__ = [
    # Base models and enums  
    'BaseModel', 'RecordType', 'StatsType', 'OutputType',
    'RecordInfo', 'Control',
    
    # Core records
    'Record', 'RunRecord', 'HistoryRecord', 'SummaryRecord', 'ConfigRecord',
    'OutputRecord', 'OutputRawRecord', 'StatsRecord', 'MetricRecord', 'FilesRecord', 'FilesItem',
    'HistoryItem', 'HistoryStep', 'ConfigItem', 'SummaryItem', 'StatsItem',
    'MetricOptions', 'MetricSummary', 'MetricControl',
    'GitRepoRecord', 'TelemetryRecord', 'SettingsRecord', 'SettingsItem',
    
    # Request/Response
    'Request', 'Response', 'Result', 'StatusRequest', 'HeaderRecord',
    'RequestInfo', 'ResultInfo', 'CancelRequest', 'PartialHistoryRequest',
    'TBRecord', 'RunPreemptingRecord', 'EnvironmentRecord', 'JobInputRequest',
    'GetSummaryRequest', 'PauseRequest', 'ResumeRequest', 'StopStatusRequest',
    'InternalMessagesRequest', 'NetworkStatusRequest', 'OperationStatsRequest',
    'PollExitRequest', 'SampledHistoryRequest', 'RunStartRequest', 'CheckVersionRequest',
    'DeferRequest', 'AttachRequest', 'ServerInfoRequest', 'KeepaliveRequest',
    'RunStatusRequest', 'SenderMarkRequest', 'SenderReadRequest', 'SyncFinishRequest',
    'StatusReportRequest', 'SummaryRecordRequest', 'TelemetryRecordRequest',
    'GetSystemMetricsRequest', 'PythonPackagesRequest', 'RunFinishWithoutExitRequest',
    'ShutdownRequest', 'RunExitRecord', 'AlertRecord', 'FinalRecord', 'FooterRecord',
    
    # Storage
    "DataStore", "get_data_store",
    
    # Interface  
    "Interface", "MessageBus", "get_message_bus",
    
    # Research/experiment management
    "parse_research_path", "list_researches", "list_experiments",
    "get_experiment_runs", "find_latest_run", "get_research_summary",
    "validate_research_name", "validate_experiment_name",
]

# Interface is imported from storage and interface modules above