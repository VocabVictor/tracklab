"""Utility functions for table operations."""
import datetime
import json
from typing import Any, Dict, List, Set, Tuple, TYPE_CHECKING

import tracklab
from .. import _dtypes
from ..base_types.wb_value import WBValue

if TYPE_CHECKING:
    from tracklab import artifact


def _get_data_from_increments(
    json_obj: Dict[str, Any], source_artifact: "artifact.Artifact"
) -> List[Any]:
    """Get data from incremental table artifacts.

    Args:
        json_obj: The JSON object containing table metadata.
        source_artifact: The source artifact containing the table data.

    Returns:
        List of table rows from all increments.
    """
    if "latest" not in source_artifact.aliases:
        tracklab.termwarn(
            (
                "It is recommended to use the latest version of the "
                "incremental table artifact for ordering guarantees."
            ),
            repeat=False,
        )
    data: List[Any] = []
    increment_num = json_obj.get("increment_num", None)
    if increment_num is None:
        return data

    # Sort by increment number first, then by timestamp if present
    # Format of name is: "{incr_num}-{timestamp_ms}.{key}.table.json"
    def get_sort_key(key: str) -> Tuple[int, int]:
        try:
            parts = key.split(".")
            increment_parts = parts[0].split("-")
            increment_num = int(increment_parts[0])
            # If there's a timestamp part, use it for secondary sorting
            timestamp = int(increment_parts[1]) if len(increment_parts) > 1 else 0
        except (ValueError, IndexError):
            tracklab.termwarn(
                (
                    f"Could not parse artifact entry for increment {key}."
                    " The entry name does not follow the naming convention"
                    " <increment_number>-<timestamp>.<key>.table.json"
                    " The data in the table will be out of order."
                ),
                repeat=False,
            )
            return (0, 0)

        return (increment_num, timestamp)

    sorted_increment_keys = []
    for entry_key in source_artifact.manifest.entries:
        if entry_key.endswith(".table.json"):
            sorted_increment_keys.append(entry_key)

    sorted_increment_keys.sort(key=get_sort_key)

    for entry_key in sorted_increment_keys:
        try:
            with open(source_artifact.manifest.entries[entry_key].download()) as f:
                table_data = json.load(f)
            data.extend(table_data["data"])
        except (json.JSONDecodeError, KeyError) as e:
            raise tracklab.Error(f"Invalid table file {entry_key}") from e
    return data


def _process_table_row(
    row: List[Any],
    timestamp_column_indices: Set[_dtypes.TimestampType],
    np_deserialized_columns: Dict[int, Any],
    source_artifact: "artifact.Artifact",
    row_idx: int,
) -> List[Any]:
    """Convert special columns in a table row to Python types.

    Processes a single row of table data by converting timestamp values to
    datetime objects, replacing np typed cells with numpy array data,
    and initializing media objects from their json value.


    Args:
        row: The row data to process.
        timestamp_column_indices: Set of column indices containing timestamps.
        np_deserialized_columns: Dictionary mapping column indices to numpy arrays.
        source_artifact: The source artifact containing the table data.
        row_idx: The index of the current row.

    Returns:
        Processed row data.
    """
    row_data = []
    for c_ndx, item in enumerate(row):
        cell: Any
        if c_ndx in timestamp_column_indices and isinstance(item, (int, float)):
            cell = datetime.datetime.fromtimestamp(
                item / 1000, tz=datetime.timezone.utc
            )
        elif c_ndx in np_deserialized_columns:
            cell = np_deserialized_columns[c_ndx][row_idx]
        elif (
            isinstance(item, dict)
            and "_type" in item
            and (obj := WBValue.init_from_json(item, source_artifact))
        ):
            cell = obj
        else:
            cell = item
        row_data.append(cell)
    return row_data