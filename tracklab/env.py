"""TrackLab environment variables.

This module provides a simplified interface to TrackLab's environment variables,
organized into logical categories for better maintainability.

Environment variables are used to configure TrackLab's behavior without modifying code.
They are not always the authoritative source for configuration values.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import MutableMapping

# Import all environment functionality from submodules
from .env.auth import (
    API_KEY,
    ANONYMOUS,
    CREDENTIALS_FILE,
    IDENTITY_TOKEN_FILE,
    USER_EMAIL,
    USERNAME,
    get_api_key,
    get_credentials_file,
    get_identity_token_file,
    get_user_email,
    get_username,
    is_anonymous,
)
from .env.core import (
    DESCRIPTION,
    ENTITY,
    NAME,
    NOTES,
    ORGANIZATION,
    PROJECT,
    RUN_GROUP,
    RUN_ID,
    TAGS,
    get_description,
    get_entity,
    get_name,
    get_notes,
    get_organization,
    get_project,
    get_run,
    get_run_group,
    get_tags,
    set_entity,
    set_project,
)
from .env.features import (
    DISABLE_CODE,
    DISABLE_GIT,
    DISABLE_SSL,
    ERROR_REPORTING,
    IGNORE_GLOBS,
    JUPYTER,
    NOTEBOOK_NAME,
    SAVE_CODE,
    disable_git,
    error_reporting_enabled,
    get_error_reporting,
    get_ignore_globs,
    get_notebook_name,
    is_jupyter,
    should_save_code,
    ssl_disabled,
)
from .env.paths import (
    ARTIFACT_DIR,
    CACHE_DIR,
    CONFIG_DIR,
    CONFIG_PATHS,
    DATA_DIR,
    DIR,
    GIT_ROOT,
    RUN_DIR,
    get_artifact_dir,
    get_cache_dir,
    get_config_dir,
    get_config_paths,
    get_data_dir,
    get_dir,
    get_git_root,
    get_run_dir,
)
from .env.runtime import (
    DEBUG,
    FILE_PUSHER_TIMEOUT,
    HTTP_TIMEOUT,
    INIT_TIMEOUT,
    INITED,
    MODE,
    QUIET,
    SILENT,
    START_METHOD,
    get_file_pusher_timeout,
    get_http_timeout,
    get_init_timeout,
    get_mode,
    get_start_method,
    is_debug,
    is_offline,
    is_quiet,
    is_silent,
)
from .env.utils import strtobool

# Additional environment variables for local TrackLab operation
# Cloud-related URLs removed for local-only mode
PROGRAM = "TRACKLAB_PROGRAM"
ARGS = "TRACKLAB_ARGS"
RESUME = "TRACKLAB_RESUME"
RUN_STORAGE_ID = "TRACKLAB_RUN_STORAGE_ID"
SWEEP_ID = "TRACKLAB_SWEEP_ID"
SWEEP_PARAM_PATH = "TRACKLAB_SWEEP_PARAM_PATH"
JOB_TYPE = "TRACKLAB_JOB_TYPE"
HOST = "TRACKLAB_HOST"
# Cloud service variables removed for local-only operation
GIT_COMMIT = "TRACKLAB_GIT_COMMIT"
GIT_REMOTE_URL = "TRACKLAB_GIT_REMOTE_URL"
MAGIC = "TRACKLAB_MAGIC"
SHOW_RUN = "TRACKLAB_SHOW_RUN"

# Agent-related environment variables
AGENT_REPORT_INTERVAL = "TRACKLAB_AGENT_REPORT_INTERVAL"
AGENT_KILL_DELAY = "TRACKLAB_AGENT_KILL_DELAY"
AGENT_DISABLE_FLAPPING = "TRACKLAB_AGENT_DISABLE_FLAPPING"
AGENT_MAX_INITIAL_FAILURES = "TRACKLAB_AGENT_MAX_INITIAL_FAILURES"

# Launch queue variables removed for local-only operation

# Other settings
CRASH_NOSYNC_TIME = "TRACKLAB_CRASH_NOSYNC_TIME"
ARTIFACT_FETCH_FILE_URL_BATCH_SIZE = "TRACKLAB_ARTIFACT_FETCH_FILE_URL_BATCH_SIZE"
_EXECUTABLE = "TRACKLAB_X_EXECUTABLE"

# Backward compatibility alias
IGNORE = IGNORE_GLOBS


def immutable_keys() -> list[str]:
    """These are env keys that shouldn't change within a single process.

    We use this to maintain certain values between multiple calls to tracklab.init
    within a single process.
    """
    return [
        DIR,
        ENTITY,
        PROJECT,
        API_KEY,
        IGNORE_GLOBS,
        DISABLE_CODE,
        DISABLE_GIT,
        MODE,
        ERROR_REPORTING,
        CRASH_NOSYNC_TIME,
        MAGIC,
        USERNAME,
        USER_EMAIL,
        SILENT,
        CONFIG_PATHS,
        ANONYMOUS,
        RUN_GROUP,
        JOB_TYPE,
        TAGS,
        RESUME,
        PROGRAM,
        AGENT_REPORT_INTERVAL,
        HTTP_TIMEOUT,
        HOST,
        DATA_DIR,
        ARTIFACT_DIR,
        ARTIFACT_FETCH_FILE_URL_BATCH_SIZE,
        CACHE_DIR,
        DISABLE_SSL,
        IDENTITY_TOKEN_FILE,
        CREDENTIALS_FILE,
    ]


# Additional getter functions for backward compatibility
def get_base_url(
    default: str | None = None, env: MutableMapping | None = None
) -> str | None:
    """Get base URL from environment."""
    if env is None:
        env = os.environ
    return env.get(BASE_URL, default)


def get_app_url(
    default: str | None = None, env: MutableMapping | None = None
) -> str | None:
    """Get app URL from environment."""
    if env is None:
        env = os.environ
    return env.get(APP_URL, default)


def get_show_run(default: str | None = None, env: MutableMapping | None = None) -> bool:
    """Check if run should be shown."""
    if env is None:
        env = os.environ
    return bool(env.get(SHOW_RUN, default))


def get_args(
    default: list[str] | None = None, env: MutableMapping | None = None
) -> list[str] | None:
    """Get command line arguments from environment."""
    if env is None:
        env = os.environ
    if env.get(ARGS):
        try:
            return json.loads(env.get(ARGS, "[]"))
        except ValueError:
            return None
    else:
        return default or sys.argv[1:]


def get_agent_report_interval(
    default: str | None = None, env: MutableMapping | None = None
) -> int | None:
    """Get agent report interval in seconds."""
    if env is None:
        env = os.environ
    val = env.get(AGENT_REPORT_INTERVAL, default)
    try:
        val = int(val)
    except (ValueError, TypeError):
        val = None
    return val


def get_agent_kill_delay(
    default: str | None = None, env: MutableMapping | None = None
) -> int | None:
    """Get agent kill delay in seconds."""
    if env is None:
        env = os.environ
    val = env.get(AGENT_KILL_DELAY, default)
    try:
        val = int(val)
    except (ValueError, TypeError):
        val = None
    return val


def get_agent_max_initial_failures(
    default: int | None = None, env: MutableMapping | None = None
) -> int | None:
    """Get maximum initial failures for agent."""
    if env is None:
        env = os.environ
    val = env.get(AGENT_MAX_INITIAL_FAILURES, default)
    try:
        val = int(val)
    except (ValueError, TypeError):
        val = default
    return val


def get_crash_nosync_time(
    default: str | None = None, env: MutableMapping | None = None
) -> int | None:
    """Get crash no-sync time in seconds."""
    if env is None:
        env = os.environ
    val = env.get(CRASH_NOSYNC_TIME, default)
    try:
        val = int(val)
    except (ValueError, TypeError):
        val = None
    return val


def get_magic(
    default: str | None = None, env: MutableMapping | None = None
) -> str | None:
    """Get magic value from environment."""
    if env is None:
        env = os.environ
    return env.get(MAGIC, default)


def get_artifact_fetch_file_url_batch_size(env: MutableMapping | None = None) -> int:
    """Get artifact fetch file URL batch size."""
    default_batch_size = 5000
    if env is None:
        env = os.environ
    val = int(env.get(ARTIFACT_FETCH_FILE_URL_BATCH_SIZE, default_batch_size))
    return val


def get_launch_queue_name(env: MutableMapping | None = None) -> str | None:
    """Get launch queue name."""
    if env is None:
        env = os.environ
    return env.get(LAUNCH_QUEUE_NAME, None)


def get_launch_queue_entity(env: MutableMapping | None = None) -> str | None:
    """Get launch queue entity."""
    if env is None:
        env = os.environ
    return env.get(LAUNCH_QUEUE_ENTITY, None)


def get_launch_trace_id(env: MutableMapping | None = None) -> str | None:
    """Get launch trace ID."""
    if env is None:
        env = os.environ
    return env.get(LAUNCH_TRACE_ID, None)


# Backward compatibility functions
def _env_as_bool(
    var: str, default: str | None = None, env: MutableMapping | None = None
) -> bool:
    """Convert environment variable to boolean."""
    if env is None:
        env = os.environ
    val = env.get(var, default)
    if not isinstance(val, str):
        return False
    try:
        return strtobool(val)
    except ValueError:
        return False


def core_debug(default: str | None = None) -> bool:
    """Check if core debug is enabled."""
    return _env_as_bool("TRACKLAB_CORE_DEBUG", default=default) or is_debug()


# Backward compatibility alias
get_ignore = get_ignore_globs


def dcgm_profiling_enabled(env: MutableMapping | None = None) -> bool:
    """Check if DCGM profiling is enabled."""
    if env is None:
        env = os.environ
    return _env_as_bool("TRACKLAB_DCGM_PROFILING", default="false", env=env)