"""Table data types for TrackLab.

This module provides table functionality for logging and analyzing tabular data.
"""

from .core import Table, _SUPPORTED_LOGGING_MODES
from .key_types import (
    _TableKey,
    _TableIndex,
    _TableLinkMixin,
    _PrimaryKeyType,
    _ForeignKeyType,
    _ForeignIndexType,
)
from .utils import _get_data_from_increments, _process_table_row
from .partitioned import PartitionedTable, _PartitionTablePartEntry
from .joined import JoinedTable
from .type_system import (
    _TableType,
    _JoinedTableType,
    _PartitionedTableType,
    register_table_types,
)

# Register all table types with the type system
# TODO: Fix type registration issues
# register_table_types()

__all__ = [
    "Table",
    "_TableKey",
    "_TableIndex",
    "_TableLinkMixin",
    "_PrimaryKeyType",
    "_ForeignKeyType",
    "_ForeignIndexType",
    "_SUPPORTED_LOGGING_MODES",
    "_get_data_from_increments",
    "_process_table_row",
    "PartitionedTable",
    "_PartitionTablePartEntry",
    "JoinedTable",
    "_TableType",
    "_JoinedTableType",
    "_PartitionedTableType",
    "register_table_types",
]