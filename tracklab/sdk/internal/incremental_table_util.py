from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tracklab import Table
    
    from ..tracklab_run import Run as LocalRun

ART_TYPE = "wandb-run-incremental-table"




#     """Initialize a new artifact for an incremental table.
#
#     Args:
#         run: The wandb run associated with this artifact
#         sanitized_key: Sanitized string key to identify the table
#
#     Returns:
#         A wandb Artifact configured for incremental table storage
#     """
#     
#         ART_TYPE,
#     )


def get_entry_name(incr_table: Table, key: str) -> str:
    """Generate a unique entry name for a table increment.

    Args:
        run: The wandb run associated with this table
        incr_table: The incremental table being updated
        key: String key for the table entry

    Returns:
        A unique string name for the table entry
    """
    epoch = time.time_ns() // 1_000_000
    return f"{incr_table._increment_num}-{epoch}.{key}"
