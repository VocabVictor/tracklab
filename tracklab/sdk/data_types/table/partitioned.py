"""PartitionedTable implementation."""
from typing import TYPE_CHECKING, Iterator, Tuple, Any, List

import tracklab
from ..base_types.media import Media

if TYPE_CHECKING:
    from tracklab import sdk


class _PartitionTablePartEntry:
    """Helper class for PartitionTable to track its parts."""

    def __init__(self, entry, source_artifact):
        self.entry = entry
        self.source_artifact = source_artifact
        self._part = None

    def get_part(self):
        """Get the table part, loading it if necessary."""
        if self._part is None:
            self._part = self.source_artifact.get(self.entry.path)
        return self._part

    def free(self):
        """Free the cached part to save memory."""
        self._part = None


class PartitionedTable(Media):
    """A table which is composed of multiple sub-tables.

    Currently, PartitionedTable is designed to point to a directory within an
    artifact.
    """

    _log_type = "partitioned-table"

    def __init__(self, parts_path: str):
        """Initialize a PartitionedTable.

        Args:
            parts_path: path to a directory of tables in the artifact.
        """
        super().__init__()
        self.parts_path = parts_path
        self._loaded_part_entries = {}

    def to_json(self, artifact_or_run):
        """Convert to JSON representation."""
        json_obj = {
            "_type": PartitionedTable._log_type,
        }
        if isinstance(artifact_or_run, tracklab.sdk.run.Run):
            artifact_entry_url = self._get_artifact_entry_ref_url()
            if artifact_entry_url is None:
                raise ValueError(
                    "PartitionedTables must first be added to an Artifact before logging to a Run"
                )
            json_obj["artifact_path"] = artifact_entry_url
        else:
            json_obj["parts_path"] = self.parts_path
        return json_obj

    @classmethod
    def from_json(cls, json_obj, source_artifact):
        """Create PartitionedTable from JSON representation."""
        instance = cls(json_obj["parts_path"])
        entries = source_artifact.manifest.get_entries_in_directory(
            json_obj["parts_path"]
        )
        for entry in entries:
            instance._add_part_entry(entry, source_artifact)
        return instance

    def iterrows(self) -> Iterator[Tuple[int, List[Any]]]:
        """Iterate over rows as (ndx, row).

        Yields:
            Tuple of (index, row) where:
                - index (int): The index of the row.
                - row (List[any]): The data of the row.
        """
        columns = None
        ndx = 0
        for entry_path in self._loaded_part_entries:
            part = self._loaded_part_entries[entry_path].get_part()
            if columns is None:
                columns = part.columns
            elif columns != part.columns:
                raise ValueError(
                    f"Table parts have non-matching columns. {columns} != {part.columns}"
                )
            for _, row in part.iterrows():
                yield ndx, row
                ndx += 1

            self._loaded_part_entries[entry_path].free()

    def _add_part_entry(self, entry, source_artifact):
        """Add a part entry to the table."""
        self._loaded_part_entries[entry.path] = _PartitionTablePartEntry(
            entry, source_artifact
        )

    def __ne__(self, other):
        """Check inequality."""
        return not self.__eq__(other)

    def __eq__(self, other):
        """Check equality."""
        return isinstance(other, self.__class__) and self.parts_path == other.parts_path

    def bind_to_run(self, *args, **kwargs):
        """Binding to run is not supported for PartitionedTables."""
        raise ValueError("PartitionedTables cannot be bound to runs")

    def __repr__(self):
        """String representation."""
        return f"PartitionedTable(parts_path='{self.parts_path}')"