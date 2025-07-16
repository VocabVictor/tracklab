"""System data models for TrackLab UI."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class GPUInfo(BaseModel):
    """GPU information model."""
    id: int
    name: str
    utilization: float
    memory: float
    temperature: float


class SystemMetrics(BaseModel):
    """System metrics model."""
    cpu: float
    memory: float
    disk: float
    gpu: Optional[List[GPUInfo]] = None
    timestamp: str


class SystemInfo(BaseModel):
    """System information model."""
    platform: str
    cpu: str
    memory: str
    storage: str
    gpu: str
    python: str
    tracklab_version: str


class SystemStatus(BaseModel):
    """System status model."""
    status: str
    datastore: str
    run_count: int
    version: str
    error: Optional[str] = None