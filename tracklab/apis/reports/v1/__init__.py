import tracklab

try:
    from tracklab_workspaces.reports.v1 import *  # noqa: F403
except ImportError:
    wandb.termerror(
        "Failed to import tracklab_workspaces.  To edit reports programmatically, please install it using `pip install wandb[workspaces]`."
    )
