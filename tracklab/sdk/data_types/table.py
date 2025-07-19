"""Backward compatibility module for table imports.

This module re-exports all table-related classes from the new modular structure
to maintain backward compatibility with existing code that imports from table.py.
"""

# Re-export everything from the new table package
from .table import *

# Import specific classes that might be used directly
from .table import (
    Table,
    PartitionedTable,
    JoinedTable,
    _TableKey,
    _TableIndex,
    _TableLinkMixin,
    _PrimaryKeyType,
    _ForeignKeyType,
    _ForeignIndexType,
    _SUPPORTED_LOGGING_MODES,
    _get_data_from_increments,
    _process_table_row,
)

# This maintains backward compatibility while the new structure is being developed
# Once all functionality is moved to the new structure, this file can be removed
# and the table package can be used directly.