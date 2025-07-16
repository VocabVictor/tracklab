"""Run data models for TrackLab UI."""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RunConfig(BaseModel):
    """Run configuration model."""
    name: Optional[str] = None
    user: Optional[str] = None
    host: Optional[str] = None
    command: Optional[str] = None
    python_version: Optional[str] = None
    git_commit: Optional[str] = None
    git_remote: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    args: Optional[Dict[str, Any]] = None


class RunSummary(BaseModel):
    """Run summary statistics model."""
    state: str = "running"
    final_metric: Optional[float] = None
    best_metric: Optional[float] = None
    metrics: Optional[Dict[str, float]] = None


class MetricValue(BaseModel):
    """Single metric value."""
    step: int
    value: float
    timestamp: str


class Metric(BaseModel):
    """Metric data model."""
    name: str
    data: List[MetricValue]


class Artifact(BaseModel):
    """Artifact model."""
    id: str
    name: str
    type: str
    size: int
    path: str
    created_at: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class LogEntry(BaseModel):
    """Log entry model."""
    level: str
    title: str
    text: str
    timestamp: str


class Run(BaseModel):
    """Complete run model."""
    id: str
    name: str
    state: str = "running"
    project: str = "default"
    config: RunConfig = Field(default_factory=RunConfig)
    summary: RunSummary = Field(default_factory=RunSummary)
    notes: str = ""
    tags: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    duration: Optional[int] = None
    user: Optional[str] = None
    host: Optional[str] = None
    command: Optional[str] = None
    python_version: Optional[str] = None
    git_commit: Optional[str] = None
    git_remote: Optional[str] = None
    metrics: Dict[str, Metric] = Field(default_factory=dict)
    system_metrics: Dict[str, List[Any]] = Field(default_factory=dict)
    artifacts: List[Artifact] = Field(default_factory=list)
    logs: List[LogEntry] = Field(default_factory=list)


class RunListItem(BaseModel):
    """Simplified run model for list views."""
    id: str
    name: str
    state: str = "running"
    project: str = "default"
    created_at: str
    updated_at: str
    duration: Optional[int] = None
    user: Optional[str] = None
    host: Optional[str] = None
    summary: Dict[str, Any] = Field(default_factory=dict)