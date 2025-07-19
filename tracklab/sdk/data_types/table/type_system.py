"""Type system integration for table classes."""
from typing import TYPE_CHECKING

from .. import _dtypes

if TYPE_CHECKING:
    from .core import Table
    from .joined import JoinedTable
    from .partitioned import PartitionedTable


class _TableType(_dtypes.Type):
    """Type class for tracklab.Table."""
    
    name = "table"
    legacy_names = ["tracklab.Table"]

    def __init__(self, column_types=None):
        """Initialize table type with column types."""
        if column_types is None:
            column_types = _dtypes.UnknownType()
        if isinstance(column_types, dict):
            column_types = _dtypes.TypedDictType(column_types)
        elif not (
            isinstance(column_types, _dtypes.TypedDictType)
            or isinstance(column_types, _dtypes.UnknownType)
        ):
            raise TypeError("column_types must be a dict or TypedDictType")

        self.params.update({"column_types": column_types})

    def assign_type(self, wb_type=None):
        """Assign/merge with another table type."""
        if isinstance(wb_type, _TableType):
            column_types = self.params["column_types"].assign_type(
                wb_type.params["column_types"]
            )
            if not isinstance(column_types, _dtypes.InvalidType):
                return _TableType(column_types)

        return _dtypes.InvalidType()

    @classmethod
    def from_obj(cls, py_obj):
        """Create table type from Table object."""
        # Import here to avoid circular imports
        from .core import Table
        
        if not isinstance(py_obj, Table):
            raise TypeError("py_obj must be a tracklab.Table")
        else:
            return cls(py_obj._column_types)

    @property
    def types(self):
        """Get the types this handles."""
        # Import here to avoid circular imports
        from .core import Table
        return (Table,)


class _JoinedTableType(_dtypes.Type):
    """Type class for JoinedTable."""
    
    name = "joined-table"
    
    @property
    def types(self):
        """Get the types this handles."""
        # Import here to avoid circular imports
        from .joined import JoinedTable
        return (JoinedTable,)


class _PartitionedTableType(_dtypes.Type):
    """Type class for PartitionedTable."""
    
    name = "partitioned-table"
    
    @property
    def types(self):
        """Get the types this handles."""
        # Import here to avoid circular imports
        from .partitioned import PartitionedTable
        return (PartitionedTable,)


def register_table_types():
    """Register all table types with the type system."""
    # Import key types to register them
    from .key_types import _ForeignKeyType, _PrimaryKeyType, _ForeignIndexType
    
    # Register table types
    _dtypes.TypeRegistry.add(_TableType)
    _dtypes.TypeRegistry.add(_JoinedTableType)
    _dtypes.TypeRegistry.add(_PartitionedTableType)
    
    # Register key types
    _dtypes.TypeRegistry.add(_ForeignKeyType)
    _dtypes.TypeRegistry.add(_PrimaryKeyType)
    _dtypes.TypeRegistry.add(_ForeignIndexType)