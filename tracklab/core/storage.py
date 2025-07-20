"""Storage layer using LevelDB to replace protobuf-based storage."""

import json
import os
import plyvel
import time
import threading
from typing import Dict, Any, Optional, List, Iterator, Union
from pathlib import Path
from contextlib import contextmanager
import logging

from .core_records import (
    Record, RunRecord, HistoryRecord, ConfigRecord,
    SummaryRecord, MetricRecord,
    StatsRecord, OutputRecord, HistoryStep,
    ConfigItem, SummaryItem
)
from .base_models import RecordType

logger = logging.getLogger(__name__)


class DataStore:
    """Data store using LevelDB for persistence."""
    
    def __init__(self, db_path: str = "./tracklab_data"):
        """Initialize data store.
        
        Args:
            db_path: Path to LevelDB database directory
        """
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Main database for records
        self.db = plyvel.DB(str(self.db_path / "records"), create_if_missing=True)
        
        # Metadata database
        self.meta_db = plyvel.DB(str(self.db_path / "metadata"), create_if_missing=True)
        
        self._lock = threading.Lock()
        self._write_seq = 0
        
    def write_record(self, record: Record) -> str:
        """Write a record to storage.
        
        Args:
            record: Record to write
            
        Returns:
            Record key
        """
        with self._lock:
            self._write_seq += 1
            
            # Generate key based on record type and sequence
            if record.record_type == RecordType.HISTORY:
                # History records use step number as part of key
                step = record.history.step.num if record.history and record.history.step else 0
                key = f"history:{record.num}:{step}:{self._write_seq}"
            else:
                key = f"{record.record_type.value}:{record.num}:{self._write_seq}"
            
            # Write to database
            value = record.to_json()
            self.db.put(key.encode(), value.encode())
            
            # Update indices
            self._update_indices(record, key)
            
            return key
    
    def read_record(self, key: str) -> Optional[Record]:
        """Read a record by key.
        
        Args:
            key: Record key
            
        Returns:
            Record or None if not found
        """
        try:
            value = self.db.get(key.encode())
            data = json.loads(value.decode())
            return Record.from_dict(data)
        except KeyError:
            return None
        except Exception as e:
            logger.error(f"Error reading record {key}: {e}")
            return None
    
    def scan_records(self, 
                    record_type: Optional[RecordType] = None,
                    start_key: str = "",
                    limit: int = 1000) -> Iterator[Record]:
        """Scan records by type.
        
        Args:
            record_type: Type of records to scan
            start_key: Start scanning from this key
            limit: Maximum number of records to return
            
        Yields:
            Records matching criteria
        """
        prefix = f"{record_type.value}:" if record_type else ""
        start = (prefix + start_key).encode()
        
        count = 0
        for key, value in self.db.iterator(start=start):
            key_str = key.decode()
            
            # Check prefix
            if prefix and not key_str.startswith(prefix):
                break
                
            if count >= limit:
                break
                
            try:
                data = json.loads(value.decode())
                record = Record.from_dict(data)
                yield record
                count += 1
            except Exception as e:
                logger.error(f"Error reading record {key_str}: {e}")
    
    def write_run_record(self, run: RunRecord) -> str:
        """Write a run record.
        
        Args:
            run: Run record to write
            
        Returns:
            Record key
        """
        record = Record(
            num=0,
            record_type=RecordType.RUN,
            run=run
        )
        return self.write_record(record)
    
    def get_run_record(self, run_id: str) -> Optional[RunRecord]:
        """Get run record by ID.
        
        Args:
            run_id: Run ID
            
        Returns:
            Run record or None
        """
        # Check index
        try:
            key_bytes = self.meta_db.get(f"run:{run_id}".encode())
            if key_bytes:
                key = key_bytes.decode()
            else:
                raise KeyError()
            record = self.read_record(key)
            return record.run if record else None
        except KeyError:
            # Scan for run
            for record in self.scan_records(RecordType.RUN):
                if record.run and record.run.run_id == run_id:
                    return record.run
            return None
    
    def write_history(self, 
                     run_id: str,
                     step: int,
                     items: Dict[str, Any]) -> str:
        """Write history (metrics) for a step.
        
        Args:
            run_id: Run ID
            step: Step number
            items: Dictionary of metric names to values
            
        Returns:
            Record key
        """
        history = HistoryRecord()
        history.step = HistoryStep(num=step)
        
        for key, value in items.items():
            history.add_item(key, value)
        
        record = Record(
            num=step,
            record_type=RecordType.HISTORY,
            history=history
        )
        
        key = self.write_record(record)
        
        # Update run index
        self._add_to_run_index(run_id, key)
        
        return key
    
    def get_history(self, 
                   run_id: str,
                   min_step: int = 0,
                   max_step: int = None) -> List[HistoryRecord]:
        """Get history records for a run.
        
        Args:
            run_id: Run ID
            min_step: Minimum step (inclusive)
            max_step: Maximum step (inclusive)
            
        Returns:
            List of history records
        """
        history_records = []
        
        # Get records from run index
        run_keys = self._get_run_records(run_id)
        
        for key in run_keys:
            if not key.startswith("history:"):
                continue
                
            record = self.read_record(key)
            if record and record.history:
                step = record.history.step.num if record.history.step else 0
                if step >= min_step and (max_step is None or step <= max_step):
                    history_records.append(record.history)
        
        # Sort by step
        history_records.sort(key=lambda h: h.step.num if h.step else 0)
        
        return history_records
    
    def write_config(self, run_id: str, config: Dict[str, Any]) -> str:
        """Write configuration.
        
        Args:
            run_id: Run ID
            config: Configuration dictionary
            
        Returns:
            Record key
        """
        config_record = ConfigRecord()
        
        for key, value in config.items():
            item = ConfigItem(key=key)
            item.set_value(value)
            config_record.update.append(item)
        
        record = Record(
            num=0,
            record_type=RecordType.CONFIG,
            config=config_record
        )
        
        key = self.write_record(record)
        self._add_to_run_index(run_id, key)
        
        return key
    
    def write_summary(self, run_id: str, summary: Dict[str, Any]) -> str:
        """Write summary.
        
        Args:
            run_id: Run ID
            summary: Summary dictionary
            
        Returns:
            Record key
        """
        summary_record = SummaryRecord()
        
        for key, value in summary.items():
            item = SummaryItem(key=key)
            item.set_value(value)
            summary_record.update.append(item)
        
        record = Record(
            num=0,
            record_type=RecordType.SUMMARY,
            summary=summary_record
        )
        
        key = self.write_record(record)
        self._add_to_run_index(run_id, key)
        
        return key
    
    def _update_indices(self, record: Record, key: str):
        """Update indices for a record."""
        # Index runs by ID
        if record.record_type == RecordType.RUN and record.run:
            self.meta_db.put(
                f"run:{record.run.run_id}".encode(),
                key.encode()
            )
    
    def _add_to_run_index(self, run_id: str, record_key: str):
        """Add a record to run index."""
        index_key = f"run_records:{run_id}"
        
        try:
            existing_bytes = self.meta_db.get(index_key.encode())
            if existing_bytes:
                existing = existing_bytes.decode()
            else:
                raise KeyError()
            keys = json.loads(existing)
        except KeyError:
            keys = []
        
        keys.append(record_key)
        self.meta_db.put(index_key.encode(), json.dumps(keys).encode())
    
    def _get_run_records(self, run_id: str) -> List[str]:
        """Get all record keys for a run."""
        index_key = f"run_records:{run_id}"
        
        try:
            data_bytes = self.meta_db.get(index_key.encode())
            if data_bytes:
                data = data_bytes.decode()
            else:
                raise KeyError()
            return json.loads(data)
        except KeyError:
            return []
    
    def close(self):
        """Close the data store."""
        self.db.close()
        self.meta_db.close()


# Global data store instance
_global_data_store: Optional[DataStore] = None
_data_store_lock = threading.Lock()


def get_data_store(db_path: str = None, force_new: bool = False) -> DataStore:
    """Get or create global data store instance.
    
    Args:
        db_path: Path to database directory. If None, uses ~/.tracklab
        force_new: Force create new instance
        
    Returns:
        DataStore instance
    """
    global _global_data_store
    
    # 如果没有指定路径，检查环境变量或使用默认的 ~/.tracklab
    if db_path is None:
        db_path = os.environ.get("TRACKLAB_DATA_DIR", os.path.expanduser("~/.tracklab"))
    
    if force_new:
        with _data_store_lock:
            if _global_data_store is not None:
                try:
                    _global_data_store.close()
                except:
                    pass
            _global_data_store = DataStore(db_path)
    elif _global_data_store is None:
        with _data_store_lock:
            if _global_data_store is None:
                _global_data_store = DataStore(db_path)
    
    return _global_data_store


@contextmanager
def data_store_context(db_path: str = None):
    """Context manager for data store.
    
    Args:
        db_path: Path to database directory. If None, uses ~/.tracklab
        
    Yields:
        DataStore instance
    """
    if db_path is None:
        db_path = os.environ.get("TRACKLAB_DATA_DIR", os.path.expanduser("~/.tracklab"))
    store = DataStore(db_path)
    try:
        yield store
    finally:
        store.close()