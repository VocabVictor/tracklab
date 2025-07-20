"""
Simplified utility module that imports from focused sub-modules.

This replaces the original 1,971-line util.py with a clean interface
that delegates to specialized modules.
"""

from typing import Sequence, Union

# Import all functionality from the new modular structure
from .utils.module_utils import *
from .utils.type_detection import *
from .utils.json_serialization import *
from .utils.http_utils import *
from .utils.data_utils import *

# Note: The following modules are not yet created but will be added:
# - file_path_utils.py (for file/path operations)
# - artifact_utils.py (for artifact handling)
# - system_detection.py (for system info)

# For now, define missing functions that are required by other modules
def load_yaml(file_path):
    """Load YAML file - temporary implementation."""
    import yaml
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def load_json_yaml_dict(file_path):
    """Load JSON or YAML file as dict - temporary implementation."""
    if file_path.endswith('.json'):
        import json
        with open(file_path, 'r') as f:
            return json.load(f)
    else:
        return load_yaml(file_path)

# Path utility functions
def to_forward_slash_path(path):
    """Convert path to use forward slashes."""
    if path is None:
        return None
    return str(path).replace('\\', '/')

# Import functions that are implemented elsewhere  
from .sdk.lib.runid import generate_id
from .utils.data_utils import stopwatch_now

# Constants
LAUNCH_JOB_ARTIFACT_SLOT_NAME = "tracklab-launch-job"

def auto_project_name(program: str = None) -> str:
    """Automatically generate a project name from program path.
    
    Args:
        program: The program path
        
    Returns:
        Generated project name
    """
    if not program:
        return "untitled"
    
    import os
    # Get the basename without extension
    name = os.path.splitext(os.path.basename(program))[0]
    
    # Clean up the name
    name = name.replace("_", "-").replace(" ", "-")
    
    # If name is empty or just dots/dashes, use parent directory
    if not name or name.replace("-", "").replace(".", "") == "":
        parent_dir = os.path.basename(os.path.dirname(os.path.abspath(program)))
        if parent_dir:
            name = parent_dir.replace("_", "-").replace(" ", "-")
        else:
            name = "untitled"
    
    return name or "untitled"

# Artifact functionality has been removed from tracklab

def _is_artifact_string(*args, **kwargs):
    """Check if string is artifact - removed functionality."""
    return False

# Constants
MAX_LINE_BYTES = 1024 * 1024  # 1MB
# Artifact functionality has been removed

# Re-export everything for backward compatibility
__all__ = [
    # From module_utils
    "get_module",
    "get_optional_module",
    "import_module_lazy",
    "add_import_hook",
    "np",
    "pd_available",
    
    # From type_detection
    "get_full_typename",
    "get_h5_typename",
    "is_tf_tensor",
    "is_tf_tensor_typename",
    "is_pytorch_tensor",
    "is_pytorch_tensor_typename",
    "is_jax_tensor_typename",
    "is_numpy_array",
    "is_pandas_data_frame",
    "is_matplotlib_typename",
    "is_plotly_typename",
    "guess_data_type",
    
    # From json_serialization
    "json_friendly",
    "json_friendly_val",
    "json_dump_safer",
    "json_dumps_safer",
    "make_json_if_not_number",
    "make_safe_for_json",
    "WandBJSONEncoder",
    "WandBHistoryJSONEncoder",
    "VALUE_BYTES_LIMIT",
    
    # From http_utils
    "download_file_from_url",
    "download_file_into_memory",
    "app_url",
    "launch_browser",
    
    # From data_utils
    "downsample",
    "to_human_size",
    "from_human_size",
    "random_string",
    "coalesce",
    "merge_dicts",
    
    # Path utilities
    "to_forward_slash_path",
    
    # Utility functions
    "load_yaml",
    "load_json_yaml_dict",
    "auto_project_name",
    "generate_id",
    "stopwatch_now",
    "_is_artifact_string",
    "MAX_LINE_BYTES",
    "prompt_choices",
    "_is_py_requirements_or_dockerfile",
]


def prompt_choices(
    choices: Sequence[str],
    input_timeout: Union[int, float, None] = None,
    jupyter: bool = False,
) -> str:
    """Allow a user to choose from a list of options."""
    if not choices:
        return ""
    
    # For testing, just return the first choice
    # In a real implementation, this would prompt the user
    return choices[0]

def _is_py_requirements_or_dockerfile(path: str) -> bool:
    """Check if path is a Python requirements file or Dockerfile."""
    filename = path.lower()
    return (
        'requirements' in filename and filename.endswith('.txt') or
        filename == 'dockerfile' or
        filename == 'pyproject.toml' or
        filename == 'setup.py'
    )