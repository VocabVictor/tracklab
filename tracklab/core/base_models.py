"""Base models and enums for TrackLab data types.

This module contains the fundamental building blocks for all TrackLab data structures.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import json
import uuid as uuid_lib


class RecordType(Enum):
    """Record types matching protobuf definitions."""
    RUN = "run"
    HISTORY = "history"
    CONFIG = "config"
    SUMMARY = "summary"
    OUTPUT = "output"
    STATS = "stats"
    # ARTIFACT removed for local-only mode
    METRIC = "metric"
    FILES = "files"
    TELEMETRY = "telemetry"
    ALERT = "alert"
    FINAL = "final"
    HEADER = "header"
    FOOTER = "footer"
    EXIT = "exit"
    SYSTEM_METRICS = "system_metrics"


class StatsType(Enum):
    """Stats types."""
    SYSTEM = "system"
    GPU = "gpu"
    CPU = "cpu"
    MEMORY = "memory"
    NETWORK = "network"
    DISK = "disk"


class OutputType(Enum):
    """Output types."""
    STDOUT = "stdout"
    STDERR = "stderr"


@dataclass
class BaseModel:
    """Base class for all data models with JSON serialization."""
    
    def to_dict(self) -> dict:
        """Convert to dictionary, handling nested objects."""
        def convert(obj):
            if hasattr(obj, 'to_dict'):
                return obj.to_dict()
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [convert(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert(v) for k, v in obj.items()}
            elif isinstance(obj, datetime):
                return obj.isoformat()
            else:
                return obj
        
        data = {}
        for key, value in asdict(self).items():
            if value is not None:  # Skip None values
                data[key] = convert(value)
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str):
        """Create instance from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create instance from dictionary."""
        # Import here to avoid circular imports
        from .core_records import (
            RunRecord, HistoryRecord, SummaryRecord, ConfigRecord,
            OutputRecord, StatsRecord, MetricRecord, FilesRecord, FilesItem,
            HistoryStep, HistoryItem, ConfigItem, SummaryItem, StatsItem,
            MetricOptions, MetricControl,
            GitRepoRecord, TelemetryRecord, SettingsRecord, SettingsItem
        )
        from .request_response import Request, Response
        
        # Handle nested objects properly
        kwargs = {}
        for key, value in data.items():
            if key == 'record_type' and isinstance(value, str):
                kwargs[key] = RecordType(value)
            elif key == 'output_type' and isinstance(value, str):
                kwargs[key] = OutputType(value)
            elif key == 'stats_type' and isinstance(value, str):
                kwargs[key] = StatsType(value)
            elif key == 'control' and isinstance(value, dict):
                kwargs[key] = Control.from_dict(value)
            elif key == '_info' and isinstance(value, dict):
                kwargs[key] = RecordInfo.from_dict(value)
            elif key == 'run' and isinstance(value, dict):
                kwargs[key] = RunRecord.from_dict(value)
            elif key == 'history' and isinstance(value, dict):
                kwargs[key] = HistoryRecord.from_dict(value)
            elif key == 'config' and isinstance(value, dict):
                kwargs[key] = ConfigRecord.from_dict(value)
            elif key == 'summary' and isinstance(value, dict):
                kwargs[key] = SummaryRecord.from_dict(value)
            elif key == 'output' and isinstance(value, dict):
                kwargs[key] = OutputRecord.from_dict(value)
            elif key == 'stats' and isinstance(value, dict):
                kwargs[key] = StatsRecord.from_dict(value)
            elif key == 'artifact' and isinstance(value, dict):
                kwargs[key] = ArtifactRecord.from_dict(value)
            elif key == 'metric' and isinstance(value, dict):
                kwargs[key] = MetricRecord.from_dict(value)
            elif key == 'step' and isinstance(value, dict):
                kwargs[key] = HistoryStep.from_dict(value)
            elif key == 'options' and isinstance(value, dict):
                kwargs[key] = MetricOptions.from_dict(value)
            elif key == '_control' and isinstance(value, dict):
                kwargs[key] = MetricControl.from_dict(value)
            elif key == 'manifest' and isinstance(value, dict):
                kwargs[key] = ArtifactManifest.from_dict(value)
            elif key == 'git' and isinstance(value, dict):
                kwargs[key] = GitRepoRecord.from_dict(value)
            elif key == 'telemetry' and isinstance(value, dict):
                kwargs[key] = TelemetryRecord.from_dict(value)
            elif key == 'settings' and isinstance(value, dict):
                kwargs[key] = SettingsRecord.from_dict(value)
            elif key == 'item' and isinstance(value, list):
                # Handle lists of items
                if cls.__name__ == 'HistoryRecord':
                    kwargs[key] = [HistoryItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                elif cls.__name__ == 'ConfigRecord':
                    kwargs[key] = [ConfigItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                elif cls.__name__ == 'SummaryRecord':
                    kwargs[key] = [SummaryItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                elif cls.__name__ == 'StatsRecord':
                    kwargs[key] = [StatsItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                elif cls.__name__ == 'SettingsRecord':
                    kwargs[key] = [SettingsItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                else:
                    kwargs[key] = value
            elif key == 'update' and isinstance(value, list):
                # Handle update lists
                if cls.__name__ == 'ConfigRecord':
                    kwargs[key] = [ConfigItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                elif cls.__name__ == 'SummaryRecord':
                    kwargs[key] = [SummaryItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                else:
                    kwargs[key] = value
            elif key == 'remove' and isinstance(value, list):
                # Handle remove lists
                if cls.__name__ == 'ConfigRecord':
                    kwargs[key] = [ConfigItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                elif cls.__name__ == 'SummaryRecord':
                    kwargs[key] = [SummaryItem.from_dict(i) if isinstance(i, dict) else i for i in value]
                else:
                    kwargs[key] = value
            elif key == 'contents' and isinstance(value, list):
                # Handle artifact manifest contents
                kwargs[key] = [ArtifactManifestEntry.from_dict(i) if isinstance(i, dict) else i for i in value]
            else:
                kwargs[key] = value
        return cls(**kwargs)


@dataclass
class RecordInfo(BaseModel):
    """Replaces _RecordInfo."""
    stream_id: str = ""
    _tracelog_id: str = ""


@dataclass
class Control(BaseModel):
    """Control information for records."""
    req_resp: bool = False
    local: bool = False  
    relay_id: str = ""
    mailbox_slot: str = ""
    always_send: bool = False
    flow_control: bool = False
    end_offset: int = 0
    connection_id: str = ""