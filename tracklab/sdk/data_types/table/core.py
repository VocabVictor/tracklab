"""Core Table implementation."""
import base64
import binascii
import codecs
import datetime
import json
import logging
import os
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Set, Tuple

import tracklab
from tracklab import util
from tracklab.sdk.lib import runid

from .. import _dtypes
from .._private import MEDIA_TMP
from ..base_types.media import Media, _numpy_arrays_to_lists
from ..base_types.wb_value import WBValue
from ..table_decorators import (
    allow_incremental_logging_after_append,
    allow_relogging_after_mutation,
    ensure_not_incremental,
)
from ..utils import _json_helper
from .key_types import (
    _TableKey,
    _TableIndex,
    _TableLinkMixin,
    _ForeignKeyType,
    _ForeignIndexType,
    _PrimaryKeyType,
)
from .utils import _get_data_from_increments, _process_table_row

if TYPE_CHECKING:
    from ...tracklab_run import Run as LocalRun

# Constants
_SUPPORTED_LOGGING_MODES = ["IMMUTABLE", "MUTABLE", "INCREMENTAL"]


class Table(Media):
    """The Table class used to display and analyze tabular data.

    Unlike traditional spreadsheets, Tables support numerous types of data:
    scalar values, strings, numpy arrays, and most subclasses of `tracklab.data_types.Media`.
    This means you can embed `Images`, `Video`, `Audio`, and other sorts of rich, annotated media
    directly in Tables, alongside other traditional scalar values.

    This class is the primary class used to generate W&B Tables
    https://docs.tracklab.ai/guides/models/tables/.
    """

    MAX_ROWS = 10000
    MAX_ARTIFACT_ROWS = 200000
    _MAX_EMBEDDING_DIMENSIONS = 150
    _log_type = "table"

    def __init__(
        self,
        columns=None,
        data=None,
        rows=None,
        dataframe=None,
        dtype=None,
        optional=True,
        allow_mixed_types=False,
        log_mode: Optional[
            Literal["IMMUTABLE", "MUTABLE", "INCREMENTAL"]
        ] = "IMMUTABLE",
    ):
        """Initializes a Table object.

        The rows is available for legacy reasons and should not be used.
        The Table class uses data to mimic the Pandas API.

        Args:
            columns: (List[str]) Names of the columns in the table.
                Defaults to ["Input", "Output", "Expected"].
            data: (List[List[any]]) 2D row-oriented array of values.
            dataframe: (pandas.DataFrame) DataFrame object used to create the table.
                When set, `data` and `columns` arguments are ignored.
            rows: (List[List[any]]) 2D row-oriented array of values.
            optional: (Union[bool,List[bool]]) Determines if `None` values are allowed.
                - If a singular bool value, then the optionality is enforced for all
                columns specified at construction time
                - If a list of bool values, then the optionality is applied to each
                column - should be the same length as `columns`
            allow_mixed_types: (bool) Determines if columns are allowed to have mixed types
                (disables type validation). Defaults to False
            log_mode: Optional[str] Controls how the Table is logged when mutations occur.
                Options:
                - "IMMUTABLE" (default): Table can only be logged once; subsequent
                logging attempts after the table has been mutated will be no-ops.
                - "MUTABLE": Table can be re-logged after mutations, creating
                a new artifact version each time it's logged.
                - "INCREMENTAL": Table data is logged incrementally, with each log creating
                a new artifact entry containing the new data since the last log.
        """
        super().__init__()
        self._validate_log_mode(log_mode)
        self.log_mode = log_mode
        
        # Initialize incremental logging state
        if self.log_mode == "INCREMENTAL":
            self._increment_num: int | None = None
            self._last_logged_idx: int | None = None
            self._previous_increments_paths: list[str] | None = None
            self._run_target_for_increments: LocalRun | None = None
            
        # Initialize key column tracking
        self._pk_col = None
        self._fk_cols: set[str] = set()
        
        # Handle mixed types
        if allow_mixed_types:
            dtype = _dtypes.AnyType

        # Default columns for legacy compatibility
        if columns is None:
            columns = ["Input", "Output", "Expected"]

        # Initialize from different data sources
        if dataframe is not None:
            self._init_from_dataframe(dataframe, columns, optional, dtype)
        else:
            if data is not None:
                if util.is_numpy_array(data):
                    self._init_from_ndarray(data, columns, optional, dtype)
                elif util.is_pandas_data_frame(data):
                    self._init_from_dataframe(data, columns, optional, dtype)
                else:
                    self._init_from_list(data, columns, optional, dtype)
            elif rows is not None:
                # Legacy support
                self._init_from_list(rows, columns, optional, dtype)
            else:
                # Default empty case
                self._init_from_list([], columns, optional, dtype)

    def _validate_log_mode(self, log_mode):
        """Validate the log mode."""
        assert log_mode in _SUPPORTED_LOGGING_MODES, (
            f"Invalid log_mode: {log_mode}. Must be one of {_SUPPORTED_LOGGING_MODES}"
        )

    @staticmethod
    def _assert_valid_columns(columns):
        """Validate column names."""
        valid_col_types = [str, int]
        assert isinstance(columns, list), "columns argument expects a `list` object"
        assert len(columns) == 0 or all(
            [type(col) in valid_col_types for col in columns]
        ), "columns argument expects list of strings or ints"

    def _init_from_list(self, data, columns, optional=True, dtype=None):
        """Initialize table from list data."""
        assert isinstance(data, list), "data argument expects a `list` object"
        self.data = []
        self._assert_valid_columns(columns)
        self.columns = columns
        self._make_column_types(dtype, optional)
        for row in data:
            self.add_data(*row)

    def _init_from_ndarray(self, ndarray, columns, optional=True, dtype=None):
        """Initialize table from numpy array."""
        assert util.is_numpy_array(ndarray), (
            "ndarray argument expects a `numpy.ndarray` object"
        )
        self.data = []
        self._assert_valid_columns(columns)
        self.columns = columns
        self._make_column_types(dtype, optional)
        for row in ndarray:
            self.add_data(*row)

    def _init_from_dataframe(self, dataframe, columns, optional=True, dtype=None):
        """Initialize table from pandas DataFrame."""
        assert util.is_pandas_data_frame(dataframe), (
            "dataframe argument expects a `pandas.core.frame.DataFrame` object"
        )
        self.data = []
        columns = list(dataframe.columns)
        self._assert_valid_columns(columns)
        self.columns = columns
        self._make_column_types(dtype, optional)
        for row in range(len(dataframe)):
            self.add_data(*tuple(dataframe[col].values[row] for col in self.columns))

    def _make_column_types(self, dtype=None, optional=True):
        """Initialize column types."""
        if dtype is None:
            dtype = _dtypes.UnknownType()

        if dtype.__class__ is not list:
            dtype = [dtype for _ in range(len(self.columns))]

        if optional.__class__ is not list:
            optional = [optional for _ in range(len(self.columns))]

        self._column_types = _dtypes.TypedDictType({})
        for col_name, opt, dt in zip(self.columns, optional, dtype):
            self.cast(col_name, dt, opt)

    def cast(self, col_name, dtype, optional=True):
        """Cast a column to a specific type."""
        if col_name not in self.columns:
            raise ValueError(f"Column '{col_name}' does not exist")
        
        # Create the type
        wbtype = _dtypes.TypeRegistry.type_from_dtype(dtype, optional)
        
        # Handle special key types
        is_pk = isinstance(wbtype, _PrimaryKeyType)
        is_fk = isinstance(wbtype, _ForeignKeyType)
        
        if is_fk:
            # Foreign key validation
            if id(wbtype.params["table"]) == id(self):
                raise AssertionError("Cannot set a foreign table reference to same table.")
            self._fk_cols.add(col_name)
        
        if is_pk:
            # Primary key validation
            assert self._pk_col is None, (
                f"Cannot have multiple primary keys - {self._pk_col} is already set as the primary key."
            )
            self._pk_col = col_name

        # Update the column type
        self._column_types.params["type_map"][col_name] = wbtype
        
        # Update key wrappers
        self._update_keys()
        return wbtype

    def _update_keys(self, force_last=False):
        """Update key wrapper objects."""
        # Implementation would update _TableKey and _TableIndex objects
        # This is a simplified version
        pass

    def __eq__(self, other):
        """Check equality with another table."""
        if not isinstance(other, Table):
            return False
        if len(self.data) != len(other.data):
            return False
        if self.columns != other.columns:
            return False
        if self._column_types != other._column_types:
            return False
        
        # Check data equality
        for row_idx in range(len(self.data)):
            for col_idx in range(len(self.data[row_idx])):
                if self.data[row_idx][col_idx] != other.data[row_idx][col_idx]:
                    return False
        return True

    def __ne__(self, other):
        """Check inequality with another table."""
        return not self.__eq__(other)

    @allow_relogging_after_mutation
    def add_row(self, *row):
        """Deprecated. Use `Table.add_data` method instead."""
        logging.warning("add_row is deprecated, use add_data")
        self.add_data(*row)

    @allow_relogging_after_mutation
    @allow_incremental_logging_after_append
    def add_data(self, *data):
        """Adds a new row of data to the table.

        The maximum amount of rows in a table is determined by
        `tracklab.Table.MAX_ARTIFACT_ROWS`.

        The length of the data should match the length of the table column.
        """
        if len(data) != len(self.columns):
            raise ValueError(
                f"This table expects {len(self.columns)} columns: {self.columns}, found {len(data)}"
            )

        # Special case to pre-emptively cast a column as a key
        for ndx, item in enumerate(data):
            if isinstance(item, _TableLinkMixin):
                self.cast(
                    self.columns[ndx],
                    _dtypes.TypeRegistry.type_of(item),
                    optional=False,
                )

        # Update the table's column types
        result_type = self._get_updated_result_type(data)
        self._column_types = result_type

        # Convert tuple to list for mutability
        if isinstance(data, tuple):
            data = list(data)
        
        # Add the new data
        self.data.append(data)

        # Update the wrapper values if needed
        self._update_keys(force_last=True)

    def _get_updated_result_type(self, row):
        """Returns the updated result type based on the inputted row."""
        incoming_row_dict = {
            col_key: row[ndx] for ndx, col_key in enumerate(self.columns)
        }
        current_type = self._column_types
        result_type = current_type.assign(incoming_row_dict)
        if isinstance(result_type, _dtypes.InvalidType):
            raise TypeError(
                f"Data row contained incompatible types:\n{current_type.explain(incoming_row_dict)}"
            )
        return result_type

    def add_column(self, name, data=None, optional=True):
        """Add a column to the table."""
        if name in self.columns:
            raise ValueError(f"Column '{name}' already exists")
            
        self.columns.append(name)
        
        # Add data to existing rows
        if data is not None:
            for i, row in enumerate(self.data):
                if i < len(data):
                    row.append(data[i])
                else:
                    row.append(None)
        else:
            # Add None to all existing rows
            for row in self.data:
                row.append(None)
        
        # Update column types
        self.cast(name, _dtypes.UnknownType(), optional)

    def get_column(self, name):
        """Get a column by name."""
        if name not in self.columns:
            raise ValueError(f"Column '{name}' does not exist")
            
        col_idx = self.columns.index(name)
        return [row[col_idx] for row in self.data]

    def __len__(self):
        """Get number of rows."""
        return len(self.data)

    def __getitem__(self, key):
        """Get row or column by index/name."""
        if isinstance(key, int):
            return self.data[key]
        elif isinstance(key, str):
            return self.get_column(key)
        else:
            raise TypeError("Key must be int or str")

    def _to_table_json(self, max_rows=None, warn=True):
        """Convert table to JSON format for logging."""
        if max_rows is None:
            max_rows = Table.MAX_ROWS
        
        n_rows = len(self.data)
        if n_rows > max_rows and warn:
            if tracklab.run and (
                tracklab.run.settings.table_raise_on_max_row_limit_exceeded
                or tracklab.run.settings.strict
            ):
                raise ValueError(
                    f"Table row limit exceeded: table has {n_rows} rows, limit is {max_rows}. "
                    f"To increase the maximum number of allowed rows in a tracklab.Table, override "
                    f"the limit with `tracklab.Table.MAX_ARTIFACT_ROWS = X` and try again. Note: "
                    f"this may cause slower queries in the W&B UI."
                )
            logging.warning(f"Truncating tracklab.Table object to {max_rows} rows.")

        if self.log_mode == "INCREMENTAL" and self._last_logged_idx is not None:
            return {
                "columns": self.columns,
                "data": self.data[
                    self._last_logged_idx + 1 : self._last_logged_idx + 1 + max_rows
                ],
            }
        else:
            return {"columns": self.columns, "data": self.data[:max_rows]}

    def to_json(self, artifact=None):
        """Convert table to JSON representation."""
        return {
            "_type": "table",
            "columns": self.columns,
            "data": self.data,
            "ncols": len(self.columns),
            "nrows": len(self.data),
        }

    @classmethod
    def from_json(cls, json_dict, source_artifact=None):
        """Create table from JSON representation."""
        columns = json_dict.get("columns", [])
        data = json_dict.get("data", [])
        
        # Handle incremental tables
        if "increment_num" in json_dict:
            data = _get_data_from_increments(json_dict, source_artifact)
        
        return cls(columns=columns, data=data)

    def __repr__(self):
        """String representation of the table."""
        return f"Table(columns={self.columns}, rows={len(self.data)})"