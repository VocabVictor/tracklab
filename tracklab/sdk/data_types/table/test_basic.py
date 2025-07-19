"""Basic test to verify table module structure."""

def test_imports():
    """Test that all table classes can be imported correctly."""
    from .core import Table
    from .key_types import _TableKey, _TableIndex, _TableLinkMixin
    from .partitioned import PartitionedTable
    from .joined import JoinedTable
    from .type_system import _TableType, _JoinedTableType, _PartitionedTableType
    from .utils import _get_data_from_increments, _process_table_row
    
    # Test that imports work
    assert Table is not None
    assert _TableKey is not None
    assert _TableIndex is not None
    assert _TableLinkMixin is not None
    assert PartitionedTable is not None
    assert JoinedTable is not None
    assert _TableType is not None
    assert _JoinedTableType is not None
    assert _PartitionedTableType is not None
    assert _get_data_from_increments is not None
    assert _process_table_row is not None
    
    print("All imports successful!")


def test_basic_table():
    """Test basic table functionality."""
    from .core import Table
    
    # Test creating a basic table
    table = Table(
        columns=["name", "age", "city"],
        data=[
            ["Alice", 30, "New York"],
            ["Bob", 25, "San Francisco"],
            ["Charlie", 35, "Chicago"]
        ]
    )
    
    assert len(table) == 3
    assert table.columns == ["name", "age", "city"]
    assert table[0] == ["Alice", 30, "New York"]
    assert table["name"] == ["Alice", "Bob", "Charlie"]
    
    # Test adding data
    table.add_data("David", 28, "Boston")
    assert len(table) == 4
    assert table[3] == ["David", 28, "Boston"]
    
    # Test adding column
    table.add_column("country", ["USA", "USA", "USA", "USA"])
    assert "country" in table.columns
    assert table["country"] == ["USA", "USA", "USA", "USA"]
    
    print("Basic table functionality works!")


def test_package_import():
    """Test importing from the package."""
    from . import Table, PartitionedTable, JoinedTable
    
    # Test that package imports work
    assert Table is not None
    assert PartitionedTable is not None
    assert JoinedTable is not None
    
    print("Package imports successful!")


if __name__ == "__main__":
    test_imports()
    test_basic_table()
    test_package_import()
    print("All tests passed!")