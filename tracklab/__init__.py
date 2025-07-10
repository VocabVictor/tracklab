"""
TrackLab - Local experiment tracking for machine learning

A wandb-compatible local experiment tracking library that provides:
- 100% wandb API compatibility
- Local-only operation (no cloud dependencies)
- Automatic server management
- Real-time visualization
- Zero configuration setup
"""

__version__ = "0.1.0"
__author__ = "TrackLab Team"
__email__ = "tracklab@example.com"

# Defer imports to avoid circular dependencies
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .sdk.tracklab_run import Run
    from .sdk.tracklab_config import Config
    from .sdk.tracklab_summary import Summary
    from .data_types import Image, Table, Histogram, Video, Audio, Object3D, Graph, Plotly, Html
    from .apis.public import Api
    from .artifacts.artifact import Artifact

# Global state management (similar to wandb)
run: "Run | None" = None
config: "Config | None" = None  
summary: "Summary | None" = None
api: "Api | None" = None

# Pre-initialization objects to provide helpful error messages
class _PreInitObject:
    """Object that raises helpful error if accessed before init()"""
    def __init__(self, name: str):
        self._name = name
        
    def __getattr__(self, key: str):
        from .errors import TrackLabError
        raise TrackLabError(f"You must call tracklab.init() before {self._name}.{key}")
        
    def __setattr__(self, key: str, value):
        if key.startswith('_'):
            super().__setattr__(key, value)
        else:
            from .errors import TrackLabError
            raise TrackLabError(f"You must call tracklab.init() before {self._name}.{key}")

class _PreInitCallable:
    """Callable that raises helpful error if called before init()"""
    def __init__(self, name: str):
        self._name = name
        
    def __call__(self, *args, **kwargs):
        from .errors import TrackLabError
        raise TrackLabError(f"You must call tracklab.init() before {self._name}()")

# Initialize pre-init objects
config = _PreInitObject("tracklab.config")
summary = _PreInitObject("tracklab.summary")
log = _PreInitCallable("tracklab.log")

# Core API functions - these will be replaced by actual implementations
def init(
    project: str | None = None,
    entity: str | None = None,
    config: dict | None = None,
    name: str | None = None,
    notes: str | None = None,
    tags: list[str] | None = None,
    group: str | None = None,
    job_type: str | None = None,
    dir: str | None = None,
    id: str | None = None,
    resume: bool | str | None = None,
    reinit: bool | None = None,
    save_code: bool | None = None,
    mode: str | None = None,
    **kwargs
) -> "Run":
    """Initialize a new TrackLab run - wandb compatible"""
    from .sdk.tracklab_init import init as _init
    return _init(
        project=project,
        entity=entity,
        config=config,
        name=name,
        notes=notes,
        tags=tags,
        group=group,
        job_type=job_type,
        dir=dir,
        id=id,
        resume=resume,
        reinit=reinit,
        save_code=save_code,
        mode=mode,
        **kwargs
    )

def finish(exit_code: int | None = None) -> None:
    """Mark a run as finished"""
    from .sdk.tracklab_run import finish as _finish
    _finish(exit_code=exit_code)

def login(
    key: str | None = None,
    host: str | None = None,
    relogin: bool | None = None,
    force: bool | None = None,
    **kwargs
) -> None:
    """Login to TrackLab (local mode - no-op for compatibility)"""
    from .sdk.tracklab_login import login as _login
    _login(key=key, host=host, relogin=relogin, force=force, **kwargs)

def save(
    glob_str: str | None = None,
    base_path: str | None = None,
    policy: str = "live"
) -> None:
    """Save files to the current run"""
    if run is None:
        from .errors import TrackLabError
        raise TrackLabError("You must call tracklab.init() before tracklab.save()")
    return run.save(glob_str=glob_str, base_path=base_path, policy=policy)

def watch(
    models,
    criterion=None,
    log: str = "gradients",
    log_freq: int = 1000,
    idx: int | None = None,
    log_graph: bool = True
) -> None:
    """Watch model gradients and parameters"""
    if run is None:
        from .errors import TrackLabError
        raise TrackLabError("You must call tracklab.init() before tracklab.watch()")
    return run.watch(models=models, criterion=criterion, log=log, log_freq=log_freq, idx=idx, log_graph=log_graph)

def sweep(
    sweep_config: dict,
    project: str | None = None,
    entity: str | None = None
) -> str:
    """Create a hyperparameter sweep"""
    from .sdk.tracklab_sweep import sweep as _sweep
    return _sweep(sweep_config=sweep_config, project=project, entity=entity)

def agent(
    sweep_id: str,
    function: callable | None = None,
    entity: str | None = None,
    project: str | None = None,
    count: int | None = None
) -> None:
    """Run a sweep agent"""
    from .sdk.tracklab_sweep import agent as _agent
    return _agent(sweep_id=sweep_id, function=function, entity=entity, project=project, count=count)

def log_artifact(artifact: "Artifact") -> None:
    """Log artifact to current run"""
    from .artifacts import log_artifact as _log_artifact
    return _log_artifact(artifact)

# Data type imports - delay imported to avoid circular dependencies
def __getattr__(name: str):
    """Lazy import for data types and other modules"""
    if name == "Image":
        from .data_types import Image
        return Image
    elif name == "Table":
        from .data_types import Table
        return Table
    elif name == "Histogram":
        from .data_types import Histogram
        return Histogram
    elif name == "Video":
        from .data_types import Video
        return Video
    elif name == "Audio":
        from .data_types import Audio
        return Audio
    elif name == "Object3D":
        from .data_types import Object3D
        return Object3D
    elif name == "Graph":
        from .data_types import Graph
        return Graph
    elif name == "Plotly":
        from .data_types import Plotly
        return Plotly
    elif name == "Html":
        from .data_types import Html
        return Html
    elif name == "Artifact":
        from .artifacts.artifact import Artifact
        return Artifact
    elif name == "Api":
        from .apis.public import Api
        return Api
    else:
        raise AttributeError(f"module 'tracklab' has no attribute '{name}'")

# All available exports
__all__ = [
    # Core API
    "init",
    "finish",
    "login",
    "save",
    "watch",
    "sweep",
    "agent",
    "log_artifact",
    # Global objects
    "run",
    "config", 
    "summary",
    "log",
    "api",
    # Data types (lazy loaded)
    "Image",
    "Table",
    "Histogram", 
    "Video",
    "Audio",
    "Object3D",
    "Graph",
    "Plotly",
    "Html",
    "Artifact",
    "Api",
]