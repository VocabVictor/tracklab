"""
Simplified utility module that imports from focused sub-modules.

This replaces the original 1,971-line util.py with a clean interface
that delegates to specialized modules.
"""

# Import all functionality from the new modular structure
from .utils.module_utils import *
from .utils.type_detection import *

# Temporary: Import remaining functions from original util.py
# TODO: Move these to appropriate modules as we continue refactoring
from .util import (
    # JSON serialization functions (will move to json_serialization.py)
    json_friendly,
    json_friendly_val,
    json_dump_safer,
    json_dumps_safer,
    make_json_if_not_number,
    make_safe_for_json,
    WandBJSONEncoder,
    WandBHistoryJSONEncoder,
    
    # HTTP utilities (will move to http_utils.py)
    download_file_from_url,
    download_file_into_memory,
    app_url,
    launch_browser,
    
    # File/path utilities (will move to file_path_utils.py)
    make_tarfile,
    auto_project_name,
    find_runner,
    load_yaml,
    load_json_yaml_dict,
    
    # Artifact utilities (will move to artifact_utils.py)
    artifact_to_json,
    parse_artifact_string,
    make_artifact_name_safe,
    
    # Data utilities (will move to data_utils.py)
    downsample,
    to_human_size,
    from_human_size,
    random_string,
    coalesce,
    merge_dicts,
    
    # System detection utilities (will move to system_detection.py)
    generate_id,
    host_from_path,
    uri_from_path,
    stopwatch_now,
    
    # Constants and other utilities
    VALUE_BYTES_LIMIT,
    MAX_LINE_BYTES,
    LAUNCH_JOB_ARTIFACT_SLOT_NAME,
)

# Re-export everything for backward compatibility
__all__ = [
    # From module_utils
    "vendor_setup",
    "vendor_import", 
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
    
    # From original util.py (temporary)
    "json_friendly",
    "json_friendly_val",
    "json_dump_safer",
    "json_dumps_safer",
    "make_json_if_not_number",
    "make_safe_for_json",
    "WandBJSONEncoder",
    "WandBHistoryJSONEncoder",
    "download_file_from_url",
    "download_file_into_memory",
    "app_url",
    "launch_browser",
    "make_tarfile",
    "auto_project_name",
    "find_runner",
    "load_yaml",
    "load_json_yaml_dict",
    "artifact_to_json",
    "parse_artifact_string",
    "make_artifact_name_safe",
    "downsample",
    "to_human_size",
    "from_human_size",
    "random_string",
    "coalesce",
    "merge_dicts",
    "generate_id",
    "host_from_path",
    "uri_from_path",
    "stopwatch_now",
    "VALUE_BYTES_LIMIT",
    "MAX_LINE_BYTES",
    "LAUNCH_JOB_ARTIFACT_SLOT_NAME",
]