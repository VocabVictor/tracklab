"""Request and response types for TrackLab communication.

This module contains the data structures used for internal communication
between different components of TrackLab.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from .base_models import BaseModel


@dataclass
class RequestInfo(BaseModel):
    """Replaces _RequestInfo.""" 
    stream_id: str = ""


@dataclass 
class ResultInfo(BaseModel):
    """Replaces _ResultInfo."""
    _tracelog_id: str = ""


@dataclass
class Request(BaseModel):
    """Generic request."""
    request_type: str = ""
    _info: Optional[RequestInfo] = None
    
    # Request fields (only one should be set)
    get_summary: Optional['GetSummaryRequest'] = None
    pause: Optional['PauseRequest'] = None
    resume: Optional['ResumeRequest'] = None
    status: Optional['StatusRequest'] = None
    stop_status: Optional['StopStatusRequest'] = None
    internal_messages: Optional['InternalMessagesRequest'] = None
    network_status: Optional['NetworkStatusRequest'] = None
    operations: Optional['OperationStatsRequest'] = None
    poll_exit: Optional['PollExitRequest'] = None
    partial_history: Optional['PartialHistoryRequest'] = None
    sampled_history: Optional['SampledHistoryRequest'] = None
    run_start: Optional['RunStartRequest'] = None
    check_version: Optional['CheckVersionRequest'] = None
    defer: Optional['DeferRequest'] = None
    attach: Optional['AttachRequest'] = None
    server_info: Optional['ServerInfoRequest'] = None
    keepalive: Optional['KeepaliveRequest'] = None
    run_status: Optional['RunStatusRequest'] = None
    sender_mark: Optional['SenderMarkRequest'] = None
    sender_read: Optional['SenderReadRequest'] = None
    cancel: Optional['CancelRequest'] = None
    status_report: Optional['StatusReportRequest'] = None
    summary_record: Optional['SummaryRecordRequest'] = None
    telemetry_record: Optional['TelemetryRecordRequest'] = None
    get_system_metrics: Optional['GetSystemMetricsRequest'] = None
    sync_finish: Optional['SyncFinishRequest'] = None
    python_packages: Optional['PythonPackagesRequest'] = None
    job_input: Optional['JobInputRequest'] = None
    run_finish_without_exit: Optional['RunFinishWithoutExitRequest'] = None
    shutdown: Optional['ShutdownRequest'] = None


@dataclass  
class Response(BaseModel):
    """Generic response."""
    response_type: str = ""
    _info: Optional[ResultInfo] = None
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Result(BaseModel):
    """Result type for responses."""
    pass


# Only include request/response types that are actually used
@dataclass
class StatusRequest(BaseModel):
    """Status request."""
    pass


@dataclass
class HeaderRecord(BaseModel):
    """Header record for run initialization."""
    pass


@dataclass
class CancelRequest(BaseModel):
    """Cancel request."""
    pass


@dataclass
class PartialHistoryRequest(BaseModel):
    """Partial history request."""
    pass


@dataclass
class TBRecord(BaseModel):
    """TensorBoard record."""
    pass


@dataclass
class RunPreemptingRecord(BaseModel):
    """Run preempting record."""
    pass


@dataclass
class EnvironmentRecord(BaseModel):
    """Environment record."""
    pass


@dataclass
class JobInputRequest(BaseModel):
    """Job input request."""
    pass


@dataclass
class GetSummaryRequest(BaseModel):
    """Get summary request."""
    pass


@dataclass
class PauseRequest(BaseModel):
    """Pause request."""
    pass


@dataclass
class ResumeRequest(BaseModel):
    """Resume request."""
    pass


@dataclass
class StopStatusRequest(BaseModel):
    """Stop status request."""
    pass


@dataclass
class InternalMessagesRequest(BaseModel):
    """Internal messages request."""
    pass


@dataclass
class NetworkStatusRequest(BaseModel):
    """Network status request."""
    pass


@dataclass
class OperationStatsRequest(BaseModel):
    """Operation stats request."""
    pass


@dataclass
class PollExitRequest(BaseModel):
    """Poll exit request."""
    pass


@dataclass
class SampledHistoryRequest(BaseModel):
    """Sampled history request."""
    pass


@dataclass
class RunStartRequest(BaseModel):
    """Run start request."""
    pass


@dataclass
class CheckVersionRequest(BaseModel):
    """Check version request."""
    pass




@dataclass
class DeferRequest(BaseModel):
    """Defer request."""
    pass


@dataclass
class AttachRequest(BaseModel):
    """Attach request."""
    pass


@dataclass
class ServerInfoRequest(BaseModel):
    """Server info request."""
    pass


@dataclass
class KeepaliveRequest(BaseModel):
    """Keepalive request."""
    pass


@dataclass
class RunStatusRequest(BaseModel):
    """Run status request."""
    pass


@dataclass
class SenderMarkRequest(BaseModel):
    """Sender mark request."""
    pass


@dataclass
class SenderReadRequest(BaseModel):
    """Sender read request."""
    pass


@dataclass
class SyncFinishRequest(BaseModel):
    """Sync finish request."""
    pass


@dataclass
class StatusReportRequest(BaseModel):
    """Status report request."""
    pass


@dataclass
class SummaryRecordRequest(BaseModel):
    """Summary record request."""
    pass


@dataclass
class TelemetryRecordRequest(BaseModel):
    """Telemetry record request."""
    pass


@dataclass
class GetSystemMetricsRequest(BaseModel):
    """Get system metrics request."""
    pass


@dataclass
class PythonPackagesRequest(BaseModel):
    """Python packages request."""
    pass


@dataclass
class RunFinishWithoutExitRequest(BaseModel):
    """Run finish without exit request."""
    pass


@dataclass
class ShutdownRequest(BaseModel):
    """Shutdown request."""
    pass


@dataclass
class RunExitRecord(BaseModel):
    """Run exit record."""
    pass


@dataclass
class AlertRecord(BaseModel):
    """Alert record."""
    pass


@dataclass
class FinalRecord(BaseModel):
    """Final record."""
    pass


@dataclass
class FooterRecord(BaseModel):
    """Footer record."""
    pass




