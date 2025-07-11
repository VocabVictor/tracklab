import tracklab

try:
    from tracklab_workspaces.workspaces import *  # noqa: F403
except ImportError:
    wandb.termerror(
        "Failed to import tracklab_workspaces. To edit workspaces programmatically, please install it using `pip install wandb[workspaces]`."
    )
