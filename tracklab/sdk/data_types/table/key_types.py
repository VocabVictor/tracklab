"""Table key types and related classes."""
from typing import TYPE_CHECKING

from tracklab.sdk.lib import runid
from .. import _dtypes

if TYPE_CHECKING:
    from .core import Table


class _TableLinkMixin:
    """Base mixin for table-linked objects."""
    
    def set_table(self, table):
        self._table = table


class _TableKey(str, _TableLinkMixin):
    """Table key class for primary/foreign key references."""
    
    def set_table(self, table, col_name):
        assert col_name in table.columns
        self._table = table
        self._col_name = col_name


class _TableIndex(int, _TableLinkMixin):
    """Table index class for row references."""
    
    def get_row(self):
        row = {}
        if self._table:
            row = {
                c: self._table.data[self][i] for i, c in enumerate(self._table.columns)
            }
        return row


class _PrimaryKeyType(_dtypes.Type):
    """Type for primary key columns."""
    
    name = "primaryKey"
    legacy_names = ["tracklab.TablePrimaryKey"]

    def assign_type(self, wb_type=None):
        if isinstance(wb_type, _dtypes.StringType) or isinstance(
            wb_type, _PrimaryKeyType
        ):
            return self
        return _dtypes.InvalidType()

    @classmethod
    def from_obj(cls, py_obj):
        if not isinstance(py_obj, _TableKey):
            raise TypeError("py_obj must be a tracklab.Table")
        else:
            return cls()


class _ForeignKeyType(_dtypes.Type):
    """Type for foreign key columns."""
    
    name = "foreignKey"
    legacy_names = ["tracklab.TableForeignKey"]
    types = [_TableKey]

    def __init__(self, table, col_name):
        # Import here to avoid circular imports
        from .core import Table
        assert isinstance(table, Table)
        assert isinstance(col_name, str)
        assert col_name in table.columns
        self.params.update({"table": table, "col_name": col_name})

    def assign_type(self, wb_type=None):
        if isinstance(wb_type, _dtypes.StringType):
            return self
        elif (
            isinstance(wb_type, _ForeignKeyType)
            and id(self.params["table"]) == id(wb_type.params["table"])
            and self.params["col_name"] == wb_type.params["col_name"]
        ):
            return self

        return _dtypes.InvalidType()

    @classmethod
    def from_obj(cls, py_obj):
        if not isinstance(py_obj, _TableKey):
            raise TypeError("py_obj must be a _TableKey")
        else:
            return cls(py_obj._table, py_obj._col_name)

    def to_json(self, artifact=None):
        res = super().to_json(artifact)
        if artifact is not None:
            table_name = f"media/tables/t_{runid.generate_id()}"
            entry = artifact.add(self.params["table"], table_name)
            res["params"]["table"] = entry.path
        else:
            raise AssertionError(
                "_ForeignKeyType does not support serialization without an artifact"
            )
        return res

    @classmethod
    def from_json(
        cls,
        json_dict,
        artifact,
    ):
        table = None
        col_name = None
        if artifact is None:
            raise AssertionError(
                "_ForeignKeyType does not support deserialization without an artifact"
            )
        else:
            table = artifact.get(json_dict["params"]["table"])
            col_name = json_dict["params"]["col_name"]

        if table is None:
            raise AssertionError("Unable to deserialize referenced table")

        return cls(table, col_name)


class _ForeignIndexType(_dtypes.Type):
    """Type for foreign index columns."""
    
    name = "foreignIndex"
    legacy_names = ["tracklab.TableForeignIndex"]
    types = [_TableIndex]

    def __init__(self, table):
        # Import here to avoid circular imports
        from .core import Table
        assert isinstance(table, Table)
        self.params.update({"table": table})

    def assign_type(self, wb_type=None):
        if isinstance(wb_type, _dtypes.NumberType):
            return self
        elif isinstance(wb_type, _ForeignIndexType) and id(self.params["table"]) == id(
            wb_type.params["table"]
        ):
            return self

        return _dtypes.InvalidType()

    @classmethod
    def from_obj(cls, py_obj):
        if not isinstance(py_obj, _TableIndex):
            raise TypeError("py_obj must be a _TableIndex")
        else:
            return cls(py_obj._table)

    def to_json(self, artifact=None):
        res = super().to_json(artifact)
        if artifact is not None:
            table_name = f"media/tables/t_{runid.generate_id()}"
            entry = artifact.add(self.params["table"], table_name)
            res["params"]["table"] = entry.path
        else:
            raise AssertionError(
                "_ForeignIndexType does not support serialization without an artifact"
            )
        return res

    @classmethod
    def from_json(
        cls,
        json_dict,
        artifact,
    ):
        table = None
        if artifact is None:
            raise AssertionError(
                "_ForeignIndexType does not support deserialization without an artifact"
            )
        else:
            table = artifact.get(json_dict["params"]["table"])

        if table is None:
            raise AssertionError("Unable to deserialize referenced table")

        return cls(table)