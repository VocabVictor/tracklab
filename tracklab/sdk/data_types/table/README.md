# Table Module Structure

This directory contains the refactored table functionality for TrackLab, split from the original monolithic `table.py` file (1,461 lines) into a modular structure for better maintainability.

## File Structure

```
table/
├── __init__.py           # Package initialization and exports
├── core.py              # Core Table class (420 lines)
├── key_types.py         # Key type classes (150 lines)
├── partitioned.py       # PartitionedTable class (90 lines)
├── joined.py            # JoinedTable class (140 lines)
├── type_system.py       # Type system integration (80 lines)
├── utils.py             # Utility functions (90 lines)
├── test_basic.py        # Basic functionality tests
└── README.md            # This file
```

## Module Responsibilities

### `core.py`
- **Main class**: `Table`
- **Purpose**: Core table functionality including data storage, manipulation, and serialization
- **Key features**:
  - Data initialization from lists, numpy arrays, pandas DataFrames
  - Row and column operations (`add_data`, `add_column`, `get_column`)
  - Type casting and validation
  - JSON serialization/deserialization
  - Logging mode support (IMMUTABLE, MUTABLE, INCREMENTAL)

### `key_types.py`
- **Main classes**: `_TableKey`, `_TableIndex`, `_PrimaryKeyType`, `_ForeignKeyType`, `_ForeignIndexType`
- **Purpose**: Handle table relationships and key constraints
- **Key features**:
  - Primary key and foreign key relationships
  - Table index references
  - Type validation for key columns
  - Serialization of key relationships

### `partitioned.py`
- **Main class**: `PartitionedTable`
- **Purpose**: Support for tables composed of multiple sub-tables
- **Key features**:
  - Directory-based table partitioning
  - Lazy loading of table parts
  - Row iteration across all partitions
  - Memory-efficient part management

### `joined.py`
- **Main class**: `JoinedTable`
- **Purpose**: Support for joining two tables for visualization
- **Key features**:
  - Table joining with single or multiple keys
  - Artifact integration
  - Validation of join relationships
  - JSON serialization of join metadata

### `type_system.py`
- **Main classes**: `_TableType`, `_JoinedTableType`, `_PartitionedTableType`
- **Purpose**: Integration with TrackLab's type system
- **Key features**:
  - Type registration and validation
  - Column type management
  - Type compatibility checking
  - Object-to-type conversion

### `utils.py`
- **Main functions**: `_get_data_from_increments`, `_process_table_row`
- **Purpose**: Utility functions for table operations
- **Key features**:
  - Incremental table data processing
  - Row data type conversion
  - Timestamp and media object handling

## Usage

### Basic Usage
```python
from tracklab.sdk.data_types.table import Table

# Create a simple table
table = Table(
    columns=["name", "age", "city"],
    data=[
        ["Alice", 30, "New York"],
        ["Bob", 25, "San Francisco"]
    ]
)

# Add data
table.add_data("Charlie", 35, "Chicago")

# Add column
table.add_column("country", ["USA", "USA", "USA"])
```

### Advanced Usage
```python
from tracklab.sdk.data_types.table import Table, PartitionedTable, JoinedTable

# Create a partitioned table
partitioned = PartitionedTable("path/to/table/parts")

# Create a joined table
joined = JoinedTable(table1, table2, join_key="id")
```

### Backward Compatibility
The original `table.py` imports should continue to work:
```python
from tracklab.sdk.data_types.table_new import Table  # Still works
```

## Benefits of Refactoring

1. **Modularity**: Each file focuses on a specific aspect of table functionality
2. **Maintainability**: Smaller files are easier to understand and modify
3. **Testability**: Individual modules can be tested in isolation
4. **Performance**: Reduced import overhead for unused functionality
5. **Extensibility**: New table types can be added as separate modules

## Migration Notes

- All existing imports should continue to work through the `__init__.py` file
- The original `table.py` can be kept as `table_original.py` for reference
- Type registration is handled automatically when importing the table package
- No breaking changes to the public API

## Testing

Run the basic tests to verify the module structure:
```bash
python -m tracklab.sdk.data_types.table.test_basic
```

## Future Improvements

- Add more comprehensive tests for each module
- Implement performance optimizations for large tables
- Add support for additional table formats
- Improve error handling and validation
- Add documentation for advanced features