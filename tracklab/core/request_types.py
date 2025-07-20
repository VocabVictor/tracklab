"""Additional request/response types for protobuf migration."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from .base_models import BaseModel


@dataclass 
class CancelRequest(BaseModel):
    """Cancel request."""
    cancel_slot: str = ""


@dataclass
class DeferRequest(BaseModel):
    """Defer request."""
    pass


@dataclass
class FinalRecord(BaseModel):
    """Final record."""
    pass


@dataclass
class FooterRecord(BaseModel):
    """Footer record."""
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
class ShutdownRequest(BaseModel):
    """Shutdown request."""
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
class PythonPackagesRequest(BaseModel):
    """Python packages request."""
    pass


# Re-export everything
__all__ = [
    'CancelRequest', 'DeferRequest', 'FinalRecord', 'FooterRecord',
    'SenderMarkRequest', 'SenderReadRequest', 'ShutdownRequest',
    'StatusReportRequest', 'SummaryRecordRequest', 'TelemetryRecordRequest',
    'PythonPackagesRequest'
]