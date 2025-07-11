"""
Table data type for TrackLab
"""

import json
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from .base import WBValue, register_data_type
from ..util.logging import get_logger

logger = get_logger(__name__)

@register_data_type("table")
class Table(WBValue):
    """
    Table data type for logging structured data
    
    Supports pandas DataFrames, lists of dictionaries, and other tabular data formats
    """
    
    def __init__(
        self,
        data: Union[pd.DataFrame, List[Dict[str, Any]], List[List[Any]], str],
        columns: Optional[List[str]] = None,
        optional: bool = True,
        allow_mixed_types: bool = True,
        cast: bool = True
    ):
        """
        Initialize table
        
        Args:
            data: Table data (DataFrame, list of dicts, list of lists, etc.)
            columns: Column names (if not provided in data)
            optional: Whether columns are optional
            allow_mixed_types: Whether to allow mixed types in columns
            cast: Whether to cast types automatically
        """
        super().__init__()
        
        self.columns = columns or []
        self.optional = optional
        self.allow_mixed_types = allow_mixed_types
        self.cast = cast
        
        # Convert data to standard format
        self._process_data(data)
    
    def _process_data(self, data: Any) -> None:
        """Process input data into standard format"""
        
        if isinstance(data, pd.DataFrame):
            self._process_dataframe(data)
        
        elif isinstance(data, list):
            if len(data) > 0:
                if isinstance(data[0], dict):
                    self._process_dict_list(data)
                elif isinstance(data[0], list):
                    self._process_list_list(data)
                else:
                    raise ValueError("List data must contain dictionaries or lists")
            else:
                self._data = []
                self._metadata = {"rows": 0, "columns": len(self.columns)}
        
        elif isinstance(data, str):
            self._process_string(data)
        
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    def _process_dataframe(self, df: pd.DataFrame) -> None:
        """Process pandas DataFrame"""
        
        # Extract columns if not provided
        if not self.columns:
            self.columns = df.columns.tolist()
        
        # Convert to list of dictionaries
        self._data = df.to_dict('records')
        
        # Store metadata
        self._metadata = {
            "rows": len(df),
            "columns": len(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "shape": df.shape
        }
        
        # Handle special data types
        self._process_special_types()
    
    def _process_dict_list(self, data: List[Dict[str, Any]]) -> None:
        """Process list of dictionaries"""
        
        # Extract columns if not provided
        if not self.columns:
            all_keys = set()
            for row in data:
                all_keys.update(row.keys())
            self.columns = sorted(all_keys)
        
        # Standardize rows
        self._data = []
        for row in data:
            standardized_row = {}
            for col in self.columns:
                value = row.get(col)
                standardized_row[col] = self._process_value(value)
            self._data.append(standardized_row)
        
        # Store metadata
        self._metadata = {
            "rows": len(data),
            "columns": len(self.columns),
            "column_types": self._infer_column_types()
        }
    
    def _process_list_list(self, data: List[List[Any]]) -> None:
        """Process list of lists"""
        
        if not data:
            self._data = []
            self._metadata = {"rows": 0, "columns": len(self.columns)}
            return
        
        # Use first row as header if columns not provided
        if not self.columns:
            if len(data) > 0:
                self.columns = [f"col_{i}" for i in range(len(data[0]))]
        
        # Convert to list of dictionaries
        self._data = []
        for row in data:
            if len(row) != len(self.columns):
                if self.optional:
                    # Pad or truncate row
                    row = row[:len(self.columns)] + [None] * (len(self.columns) - len(row))
                else:
                    raise ValueError(f"Row length {len(row)} doesn't match columns {len(self.columns)}")
            
            row_dict = {}
            for i, col in enumerate(self.columns):
                row_dict[col] = self._process_value(row[i])
            self._data.append(row_dict)
        
        # Store metadata
        self._metadata = {
            "rows": len(data),
            "columns": len(self.columns),
            "column_types": self._infer_column_types()
        }
    
    def _process_string(self, data: str) -> None:
        """Process string data (CSV, JSON, etc.)"""
        
        # Try to parse as JSON first
        try:
            json_data = json.loads(data)
            if isinstance(json_data, list):
                self._process_data(json_data)
                return
        except json.JSONDecodeError:
            pass
        
        # Try to parse as CSV
        try:
            import io
            import csv
            
            reader = csv.DictReader(io.StringIO(data))
            rows = list(reader)
            self._process_dict_list(rows)
            return
        except Exception:
            pass
        
        raise ValueError("Could not parse string data as table")
    
    def _process_value(self, value: Any) -> Any:
        """Process individual cell value"""
        
        if value is None:
            return None
        
        # Handle special TrackLab types
        if hasattr(value, '__tracklab_log__'):
            return value.__tracklab_log__()
        
        # Handle basic types
        if isinstance(value, (int, float, str, bool)):
            return value
        
        # Handle lists and dicts
        if isinstance(value, (list, dict)):
            return value
        
        # Convert other types to string
        if self.cast:
            try:
                return str(value)
            except Exception:
                return repr(value)
        
        return value
    
    def _process_special_types(self) -> None:
        """Process special data types in the table"""
        
        for i, row in enumerate(self._data):
            for col in self.columns:
                if col in row:
                    value = row[col]
                    
                    # Handle pandas-specific types
                    if str(type(value)).startswith('pandas'):
                        row[col] = self._convert_pandas_type(value)
                    
                    # Handle numpy types
                    elif str(type(value)).startswith('numpy'):
                        row[col] = self._convert_numpy_type(value)
                    
                    # Handle datetime types
                    elif hasattr(value, 'isoformat'):
                        row[col] = value.isoformat()
    
    def _convert_pandas_type(self, value: Any) -> Any:
        """Convert pandas-specific types"""
        
        # Handle Timestamp
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        
        # Handle NaN
        if pd.isna(value):
            return None
        
        # Handle Series (shouldn't happen in records, but just in case)
        if isinstance(value, pd.Series):
            return value.tolist()
        
        return value
    
    def _convert_numpy_type(self, value: Any) -> Any:
        """Convert numpy types to Python types"""
        
        try:
            import numpy as np
            
            if isinstance(value, np.integer):
                return int(value)
            elif isinstance(value, np.floating):
                return float(value)
            elif isinstance(value, np.ndarray):
                return value.tolist()
            elif isinstance(value, np.bool_):
                return bool(value)
            
        except ImportError:
            pass
        
        return value
    
    def _infer_column_types(self) -> Dict[str, str]:
        """Infer column types from data"""
        
        column_types = {}
        
        for col in self.columns:
            types = set()
            
            # Sample values to infer type
            for row in self._data[:100]:  # Sample first 100 rows
                value = row.get(col)
                if value is not None:
                    types.add(type(value).__name__)
            
            if not types:
                column_types[col] = "null"
            elif len(types) == 1:
                column_types[col] = types.pop()
            else:
                column_types[col] = "mixed"
        
        return column_types
    
    def to_json(self) -> Dict[str, Any]:
        """Convert to JSON"""
        return {
            "_type": "table",
            "columns": self.columns,
            "data": self._data,
            "metadata": self._metadata,
            "optional": self.optional,
            "allow_mixed_types": self.allow_mixed_types
        }
    
    def __tracklab_log__(self) -> Dict[str, Any]:
        """Return data for logging"""
        return self.to_json()
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame"""
        return pd.DataFrame(self._data)
    
    def add_row(self, row: Union[Dict[str, Any], List[Any]]) -> None:
        """Add a row to the table"""
        
        if isinstance(row, dict):
            processed_row = {}
            for col in self.columns:
                value = row.get(col)
                processed_row[col] = self._process_value(value)
            self._data.append(processed_row)
        
        elif isinstance(row, list):
            if len(row) != len(self.columns):
                if self.optional:
                    row = row[:len(self.columns)] + [None] * (len(self.columns) - len(row))
                else:
                    raise ValueError(f"Row length {len(row)} doesn't match columns {len(self.columns)}")
            
            row_dict = {}
            for i, col in enumerate(self.columns):
                row_dict[col] = self._process_value(row[i])
            self._data.append(row_dict)
        
        else:
            raise ValueError("Row must be dict or list")
        
        # Update metadata
        self._metadata["rows"] = len(self._data)
    
    def add_column(self, name: str, values: List[Any]) -> None:
        """Add a column to the table"""
        
        if len(values) != len(self._data):
            raise ValueError(f"Column length {len(values)} doesn't match table rows {len(self._data)}")
        
        # Add column to schema
        self.columns.append(name)
        
        # Add values to rows
        for i, row in enumerate(self._data):
            row[name] = self._process_value(values[i])
        
        # Update metadata
        self._metadata["columns"] = len(self.columns)
    
    def get_column(self, name: str) -> List[Any]:
        """Get column values"""
        return [row.get(name) for row in self._data]
    
    def get_row(self, index: int) -> Dict[str, Any]:
        """Get row by index"""
        if 0 <= index < len(self._data):
            return self._data[index]
        else:
            raise IndexError(f"Row index {index} out of range")
    
    def filter_rows(self, predicate: callable) -> "Table":
        """Filter rows based on predicate"""
        filtered_data = [row for row in self._data if predicate(row)]
        new_table = Table(filtered_data, columns=self.columns)
        return new_table
    
    def sort_rows(self, key: str, reverse: bool = False) -> "Table":
        """Sort rows by column"""
        sorted_data = sorted(self._data, key=lambda row: row.get(key), reverse=reverse)
        new_table = Table(sorted_data, columns=self.columns)
        return new_table
    
    def __len__(self) -> int:
        """Get number of rows"""
        return len(self._data)
    
    def __iter__(self):
        """Iterate over rows"""
        return iter(self._data)
    
    def __getitem__(self, key: Union[int, str]) -> Any:
        """Get row by index or column by name"""
        if isinstance(key, int):
            return self.get_row(key)
        elif isinstance(key, str):
            return self.get_column(key)
        else:
            raise TypeError("Key must be int or str")
    
    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "Table":
        """Create Table from JSON"""
        table = cls(
            data=data["data"],
            columns=data["columns"],
            optional=data.get("optional", True),
            allow_mixed_types=data.get("allow_mixed_types", True)
        )
        table._metadata = data.get("metadata", {})
        return table