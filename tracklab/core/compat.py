"""Compatibility layer for gradual protobuf migration.

This module provides shims and converters to help migrate from protobuf
to the new JSON-based data models while maintaining backward compatibility.
"""

import json
from typing import Any, Dict, Optional, Union
import logging

from .core_records import (
    Record, RunRecord, HistoryRecord, ConfigRecord,
    SummaryRecord, ArtifactRecord, MetricRecord,
    StatsRecord, OutputRecord,
    HistoryItem, ConfigItem, SummaryItem,
    MetricOptions, MetricControl
)
from .base_models import (
    RecordType, StatsType, OutputType, Control, RecordInfo
)

logger = logging.getLogger(__name__)


class ProtobufCompat:
    """Compatibility layer for protobuf migration."""
    
    @staticmethod
    def record_from_protobuf(pb_record: Any) -> Record:
        """Convert a protobuf Record to our Record model.
        
        Args:
            pb_record: Protobuf record object
            
        Returns:
            Record instance
        """
        record = Record()
        
        # Copy basic fields
        if hasattr(pb_record, 'num'):
            record.num = pb_record.num
        if hasattr(pb_record, 'uuid'):
            record.uuid = pb_record.uuid
            
        # Copy control
        if hasattr(pb_record, 'control') and pb_record.control:
            record.control = Control(
                req_resp=pb_record.control.req_resp,
                local=pb_record.control.local,
                relay_id=pb_record.control.relay_id,
                mailbox_slot=pb_record.control.mailbox_slot,
                always_send=pb_record.control.always_send,
                flow_control=pb_record.control.flow_control,
                end_offset=pb_record.control.end_offset,
                connection_id=pb_record.control.connection_id
            )
            
        # Copy _info
        if hasattr(pb_record, '_info') and pb_record._info:
            record._info = RecordInfo(
                stream_id=pb_record._info.stream_id,
                _tracelog_id=pb_record._info._tracelog_id
            )
        
        # Determine record type and copy specific data
        if hasattr(pb_record, 'WhichOneof'):
            record_type = pb_record.WhichOneof('record_type')
            
            if record_type == 'run':
                record.record_type = RecordType.RUN
                record.run = ProtobufCompat._run_from_protobuf(pb_record.run)
            elif record_type == 'history':
                record.record_type = RecordType.HISTORY
                record.history = ProtobufCompat._history_from_protobuf(pb_record.history)
            elif record_type == 'config':
                record.record_type = RecordType.CONFIG
                record.config = ProtobufCompat._config_from_protobuf(pb_record.config)
            elif record_type == 'summary':
                record.record_type = RecordType.SUMMARY
                record.summary = ProtobufCompat._summary_from_protobuf(pb_record.summary)
            elif record_type == 'output':
                record.record_type = RecordType.OUTPUT
                record.output = ProtobufCompat._output_from_protobuf(pb_record.output)
            elif record_type == 'stats':
                record.record_type = RecordType.STATS
                record.stats = ProtobufCompat._stats_from_protobuf(pb_record.stats)
            elif record_type == 'artifact':
                record.record_type = RecordType.ARTIFACT
                record.artifact = ProtobufCompat._artifact_from_protobuf(pb_record.artifact)
            elif record_type == 'metric':
                record.record_type = RecordType.METRIC
                record.metric = ProtobufCompat._metric_from_protobuf(pb_record.metric)
        
        return record
    
    @staticmethod
    def _run_from_protobuf(pb_run: Any) -> RunRecord:
        """Convert protobuf RunRecord."""
        run = RunRecord()
        
        # Copy fields with mapping
        field_mapping = {
            'run_id': 'run_id',
            'project': 'research_name',  # Map project to research_name
            'run_group': 'experiment_name',  # Map run_group to experiment_name
            'display_name': 'display_name',
            'notes': 'notes',
            'host': 'host',
            'storage_id': 'storage_id'
        }
        
        for pb_field, new_field in field_mapping.items():
            if hasattr(pb_run, pb_field):
                setattr(run, new_field, getattr(pb_run, pb_field))
        
        if hasattr(pb_run, 'tags'):
            run.tags = list(pb_run.tags)
        if hasattr(pb_run, 'starting_step'):
            run.starting_step = pb_run.starting_step
        if hasattr(pb_run, 'resumed'):
            run.resumed = pb_run.resumed
        if hasattr(pb_run, 'runtime'):
            run.runtime = pb_run.runtime
        if hasattr(pb_run, 'forked'):
            run.forked = pb_run.forked
            
        return run
    
    @staticmethod
    def _history_from_protobuf(pb_history: Any) -> HistoryRecord:
        """Convert protobuf HistoryRecord."""
        history = HistoryRecord()
        
        if hasattr(pb_history, 'step') and pb_history.step:
            from .core_records import HistoryStep
            history.step = HistoryStep(num=pb_history.step.num)
        
        if hasattr(pb_history, 'item'):
            for pb_item in pb_history.item:
                item = HistoryItem(
                    key=pb_item.key,
                    nested_key=list(pb_item.nested_key) if hasattr(pb_item, 'nested_key') else []
                )
                if hasattr(pb_item, 'value_json'):
                    item.value_json = pb_item.value_json
                history.item.append(item)
        
        return history
    
    @staticmethod
    def _config_from_protobuf(pb_config: Any) -> ConfigRecord:
        """Convert protobuf ConfigRecord."""
        config = ConfigRecord()
        
        if hasattr(pb_config, 'update'):
            for pb_item in pb_config.update:
                item = ConfigItem(
                    key=pb_item.key,
                    nested_key=list(pb_item.nested_key) if hasattr(pb_item, 'nested_key') else []
                )
                if hasattr(pb_item, 'value_json'):
                    item.value_json = pb_item.value_json
                config.update.append(item)
        
        if hasattr(pb_config, 'remove'):
            for pb_item in pb_config.remove:
                item = ConfigItem(
                    key=pb_item.key,
                    nested_key=list(pb_item.nested_key) if hasattr(pb_item, 'nested_key') else []
                )
                config.remove.append(item)
        
        return config
    
    @staticmethod
    def _summary_from_protobuf(pb_summary: Any) -> SummaryRecord:
        """Convert protobuf SummaryRecord."""
        summary = SummaryRecord()
        
        if hasattr(pb_summary, 'update'):
            for pb_item in pb_summary.update:
                item = SummaryItem(
                    key=pb_item.key,
                    nested_key=list(pb_item.nested_key) if hasattr(pb_item, 'nested_key') else []
                )
                if hasattr(pb_item, 'value_json'):
                    item.value_json = pb_item.value_json
                summary.update.append(item)
        
        if hasattr(pb_summary, 'remove'):
            for pb_item in pb_summary.remove:
                item = SummaryItem(
                    key=pb_item.key,
                    nested_key=list(pb_item.nested_key) if hasattr(pb_item, 'nested_key') else []
                )
                summary.remove.append(item)
        
        return summary
    
    @staticmethod
    def _output_from_protobuf(pb_output: Any) -> OutputRecord:
        """Convert protobuf OutputRecord."""
        output = OutputRecord()
        
        if hasattr(pb_output, 'line'):
            output.line = pb_output.line
            
        if hasattr(pb_output, 'output_type'):
            if pb_output.output_type == 1:  # STDERR
                output.output_type = OutputType.STDERR
            else:
                output.output_type = OutputType.STDOUT
        
        return output
    
    @staticmethod
    def _stats_from_protobuf(pb_stats: Any) -> StatsRecord:
        """Convert protobuf StatsRecord."""
        stats = StatsRecord()
        
        if hasattr(pb_stats, 'stats_type'):
            # Map protobuf enum to our enum
            stats.stats_type = StatsType.SYSTEM  # Default
        
        if hasattr(pb_stats, 'item'):
            from .core_records import StatsItem
            for pb_item in pb_stats.item:
                item = StatsItem(key=pb_item.key)
                if hasattr(pb_item, 'value_json'):
                    item.value_json = pb_item.value_json
                stats.item.append(item)
        
        return stats
    
    @staticmethod
    def _artifact_from_protobuf(pb_artifact: Any) -> ArtifactRecord:
        """Convert protobuf ArtifactRecord."""
        artifact = ArtifactRecord()
        
        # Copy all string fields
        for field in ['run_id', 'project', 'entity', 'type', 'name', 
                     'digest', 'description', 'metadata', 'distributed_id',
                     'client_id', 'sequence_client_id', 'base_id']:
            if hasattr(pb_artifact, field):
                setattr(artifact, field, getattr(pb_artifact, field))
        
        # Copy boolean fields
        for field in ['user_created', 'use_after_commit', 'finalize']:
            if hasattr(pb_artifact, field):
                setattr(artifact, field, getattr(pb_artifact, field))
                
        # Copy lists
        if hasattr(pb_artifact, 'aliases'):
            artifact.aliases = list(pb_artifact.aliases)
        if hasattr(pb_artifact, 'tags'):
            artifact.tags = list(pb_artifact.tags)
            
        # Copy numeric fields
        if hasattr(pb_artifact, 'ttl_duration_seconds'):
            artifact.ttl_duration_seconds = pb_artifact.ttl_duration_seconds
        
        return artifact
    
    @staticmethod
    def _metric_from_protobuf(pb_metric: Any) -> MetricRecord:
        """Convert protobuf MetricRecord."""
        metric = MetricRecord(name=pb_metric.name if hasattr(pb_metric, 'name') else '')
        
        # Copy fields
        for field in ['glob_name', 'step_metric', 'goal']:
            if hasattr(pb_metric, field):
                setattr(metric, field, getattr(pb_metric, field))
                
        if hasattr(pb_metric, 'step_metric_index'):
            metric.step_metric_index = pb_metric.step_metric_index
            
        if hasattr(pb_metric, 'expanded_from_glob'):
            metric.expanded_from_glob = pb_metric.expanded_from_glob
            
        # Handle options
        if hasattr(pb_metric, 'options') and pb_metric.options:
            metric.options = MetricOptions(
                step_sync=pb_metric.options.step_sync if hasattr(pb_metric.options, 'step_sync') else True,
                hidden=pb_metric.options.hidden if hasattr(pb_metric.options, 'hidden') else False,
                defined=pb_metric.options.defined if hasattr(pb_metric.options, 'defined') else False
            )
            
        # Handle control
        if hasattr(pb_metric, '_control') and pb_metric._control:
            metric._control = MetricControl(
                overwrite=pb_metric._control.overwrite if hasattr(pb_metric._control, 'overwrite') else False
            )
        
        return metric
    
    @staticmethod
    def parse_record_from_string(data: bytes) -> Optional[Record]:
        """Parse a record from bytes (protobuf or JSON).
        
        Args:
            data: Bytes to parse
            
        Returns:
            Record instance or None if parsing fails
        """
        # Try JSON first (new format)
        try:
            json_data = json.loads(data.decode('utf-8'))
            return Record.from_dict(json_data)
        except:
            pass
        
        # Try protobuf (old format)
        try:
            # Import here to avoid circular dependency
            from tracklab.proto import tracklab_internal_pb2
            
            pb_record = tracklab_internal_pb2.Record()
            pb_record.ParseFromString(data)
            return ProtobufCompat.record_from_protobuf(pb_record)
        except Exception as e:
            logger.error(f"Failed to parse record: {e}")
            return None
    
    @staticmethod
    def serialize_record_to_string(record: Record) -> bytes:
        """Serialize a record to bytes (JSON format).
        
        Args:
            record: Record to serialize
            
        Returns:
            Serialized bytes
        """
        return record.to_json().encode('utf-8')