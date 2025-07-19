from __future__ import annotations

__all__ = ("LocalAnalytics",)

import atexit
import functools
import json
import os
import pathlib
import sys
import time
import traceback
import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from types import TracebackType
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Literal, Optional, Tuple, Union

import tracklab
import tracklab.env
import tracklab.util
from tracklab.sdk.internal.datastore import DataStore

if TYPE_CHECKING:
    import tracklab.sdk.internal.settings_static

SessionStatus = Literal["ok", "exited", "crashed", "abnormal", "errored"]


def _safe_noop(func: Callable) -> Callable:
    """Decorator to ensure that analytics methods do nothing if disabled and don't raise."""

    @functools.wraps(func)
    def wrapper(self: "LocalAnalytics", *args: Any, **kwargs: Any) -> Any:
        if self._disabled:
            return None
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            # Avoid infinite recursion
            if func.__name__ != "exception":
                print(f"Error in analytics {func.__name__}: {e}")
            return None

    return wrapper


class AnalyticsRecord:
    """Simple analytics record without protobuf dependency."""
    
    def __init__(self, record_type: str, data: Dict[str, Any]):
        self.type = record_type
        self.timestamp = int(time.time() * 1000)
        self.id = str(uuid.uuid4())
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "timestamp": self.timestamp,
            "id": self.id,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AnalyticsRecord":
        record = cls(d["type"], d["data"])
        record.timestamp = d["timestamp"]
        record.id = d["id"]
        return record


class LocalAnalytics:
    """Local analytics system using LevelDB for error tracking and session management."""
    
    _disabled: bool
    
    def __init__(self, base_path: Optional[str] = None) -> None:
        self._disabled = not tracklab.env.error_reporting_enabled()
        self._sent_messages: set = set()
        
        # Set up analytics directory
        if base_path is None:
            wandb_dir = tracklab.env.get_dir() or os.path.expanduser("~/.tracklab")
            base_path = os.path.join(wandb_dir, "analytics")
        self.base_path = pathlib.Path(base_path).expanduser()
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self._current_session: Optional[Dict[str, Any]] = None
        self._datastore: Optional[DataStore] = None
        self._current_date: Optional[str] = None
        
        # Ensure we always end the session
        atexit.register(self.end_session)
    
    @property
    def environment(self) -> str:
        """Return the environment we're running in."""
        # Check if we're in a git repo
        is_git = pathlib.Path(__file__).parent.parent.parent.joinpath(".git").exists()
        return "development" if is_git else "production"
    
    def _get_datastore_path(self, date: Optional[datetime] = None) -> pathlib.Path:
        """Get the datastore path for a specific date."""
        if date is None:
            date = datetime.now()
        date_str = date.strftime("%Y%m%d")
        return self.base_path / f"analytics-{date_str}.db"
    
    def _ensure_datastore(self) -> DataStore:
        """Ensure we have a datastore for the current date."""
        date_str = datetime.now().strftime("%Y%m%d")
        
        if self._datastore is None or self._current_date != date_str:
            # Close previous datastore if exists
            if self._datastore is not None:
                self._datastore.close()
            
            # Open new datastore
            db_path = self._get_datastore_path()
            self._datastore = DataStore()
            self._datastore.open_for_write(str(db_path))
            self._current_date = date_str
        
        return self._datastore
    
    def _write_record(self, record: AnalyticsRecord) -> None:
        """Write a record to the datastore."""
        if self._disabled:
            return
        
        # Convert record to JSON bytes
        data = json.dumps(record.to_dict()).encode('utf-8')
        
        # Write to datastore
        datastore = self._ensure_datastore()
        datastore.write(data)
    
    @_safe_noop
    def setup(self) -> None:
        """Setup analytics system."""
        # Initialize the datastore
        self._ensure_datastore()
    
    @_safe_noop
    def message(self, message: str, level: str = "info", repeat: bool = True) -> str | None:
        """Record a message event."""
        if not repeat and message in self._sent_messages:
            return None
        self._sent_messages.add(message)
        
        record = AnalyticsRecord("message", {
            "message": message,
            "level": level,
            "environment": self.environment,
            "context": {}
        })
        
        self._write_record(record)
        return record.id
    
    @_safe_noop
    def exception(
        self,
        exc: str
        | BaseException
        | tuple[
            type[BaseException] | None,
            BaseException | None,
            TracebackType | None,
        ]
        | None,
        handled: bool = False,
        status: SessionStatus | None = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> str | None:
        """Log an exception to local analytics."""
        # Format exception info
        if isinstance(exc, str):
            exc_info = (Exception, Exception(exc), None)
        elif isinstance(exc, BaseException):
            exc_info = (type(exc), exc, exc.__traceback__)
        elif isinstance(exc, tuple):
            exc_info = exc
        else:
            exc_info = sys.exc_info()
        
        # Build error record
        error_data = {
            "exception_type": exc_info[0].__name__ if exc_info[0] else "Unknown",
            "message": str(exc_info[1]) if exc_info[1] else "",
            "traceback": ''.join(traceback.format_exception(*exc_info)) if all(exc_info) else "",
            "handled": handled,
            "environment": self.environment,
            "context": context or {},
            "process_context": ""
        }
        
        record = AnalyticsRecord("error", error_data)
        self._write_record(record)
        
        # Update session status if needed
        if status:
            self.mark_session(status=status)
        elif not handled:
            self.mark_session(status="crashed")
        else:
            self.mark_session(status="errored")
        
        return record.id
    
    def reraise(self, exc: Any) -> None:
        """Re-raise an exception after logging it."""
        self.exception(exc)
        raise exc
    
    @_safe_noop
    def start_session(self, tags: Optional[Dict[str, Any]] = None) -> None:
        """Start a new analytics session."""
        session_id = str(uuid.uuid4())
        self._current_session = {
            "session_id": session_id,
            "status": "ok",
            "start_time": int(time.time() * 1000),
            "end_time": None,
            "tags": tags or {},
            "environment": self.environment
        }
        
        record = AnalyticsRecord("session", self._current_session.copy())
        self._write_record(record)
    
    @_safe_noop
    def end_session(self) -> None:
        """End the current session."""
        if self._current_session is None:
            return
        
        self._current_session["end_time"] = int(time.time() * 1000)
        if self._current_session["status"] == "ok":
            self._current_session["status"] = "exited"
        
        record = AnalyticsRecord("session", self._current_session.copy())
        self._write_record(record)
        
        self._current_session = None
    
    @_safe_noop
    def mark_session(self, status: SessionStatus | None = None) -> None:
        """Mark the current session with a status."""
        if self._current_session is None or status is None:
            return
        
        self._current_session["status"] = status
        
        # Write updated session record
        record = AnalyticsRecord("session", self._current_session.copy())
        self._write_record(record)
    
    @_safe_noop
    def configure_scope(
        self,
        tags: dict[str, Any] | None = None,
        process_context: str | None = None,
    ) -> None:
        """Configure the analytics scope."""
        if self._current_session is None:
            self.start_session(tags=tags)
        elif tags:
            self._current_session["tags"].update(tags)
        
        if process_context:
            self._current_session["process_context"] = process_context
    
    def query_errors(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        error_type: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query errors from analytics database."""
        if self._disabled:
            return []
        
        results = []
        
        # Default to last 7 days
        if start_date is None:
            start_date = datetime.now() - timedelta(days=7)
        if end_date is None:
            end_date = datetime.now()
        
        # Iterate through date range
        current_date = start_date
        while current_date <= end_date:
            db_path = self._get_datastore_path(current_date)
            
            if db_path.exists():
                try:
                    datastore = DataStore()
                    datastore.open_for_scan(str(db_path))
                    
                    # Read all records
                    for data in datastore.scan_data():
                        try:
                            record_dict = json.loads(data.decode('utf-8'))
                            record = AnalyticsRecord.from_dict(record_dict)
                            
                            # Filter by type
                            if record.type != "error":
                                continue
                            
                            # Filter by error type if specified
                            if error_type and record.data.get("exception_type") != error_type:
                                continue
                            
                            results.append(record_dict)
                            
                            # Apply limit
                            if limit and len(results) >= limit:
                                datastore.close()
                                return results
                                
                        except Exception:
                            # Skip malformed records
                            continue
                    
                    datastore.close()
                    
                except Exception as e:
                    print(f"Error reading analytics file {db_path}: {e}")
            
            current_date += timedelta(days=1)
        
        return results
    
    def get_error_summary(self, days: int = 7) -> Dict[str, int]:
        """Get error summary for the last N days."""
        errors = self.query_errors(
            start_date=datetime.now() - timedelta(days=days)
        )
        
        # Group by exception type
        summary = defaultdict(int)
        for error in errors:
            exc_type = error["data"].get("exception_type", "Unknown")
            summary[exc_type] += 1
        
        return dict(summary)
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> int:
        """Clean up analytics data older than specified days."""
        if self._disabled:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        removed_count = 0
        
        # List all analytics files
        for db_file in self.base_path.glob("analytics-*.db"):
            try:
                # Parse date from filename
                date_str = db_file.stem.split("-")[1]
                file_date = datetime.strptime(date_str, "%Y%m%d")
                
                # Remove if older than cutoff
                if file_date < cutoff_date:
                    db_file.unlink()
                    removed_count += 1
                    
            except Exception as e:
                print(f"Error processing file {db_file}: {e}")
        
        return removed_count