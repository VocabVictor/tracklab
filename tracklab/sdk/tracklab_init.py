"""
TrackLab initialization - main entry point for experiment tracking
"""

import os
from typing import Any, Dict, List, Optional, Union

from .tracklab_run import Run, set_current_run, get_current_run
from .tracklab_settings import get_settings, update_settings
from ..errors import TrackLabInitError
from ..util.logging import get_logger

logger = get_logger(__name__)

def init(
    project: Optional[str] = None,
    entity: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    name: Optional[str] = None,
    notes: Optional[str] = None,
    tags: Optional[List[str]] = None,
    group: Optional[str] = None,
    job_type: Optional[str] = None,
    dir: Optional[str] = None,
    id: Optional[str] = None,
    resume: Optional[Union[bool, str]] = None,
    reinit: Optional[bool] = None,
    save_code: Optional[bool] = None,
    mode: Optional[str] = None,
    **kwargs
) -> Run:
    """
    Initialize a new TrackLab run
    
    Args:
        project: Project name
        entity: Entity name (user/organization)
        config: Configuration dictionary
        name: Run name
        notes: Run notes/description
        tags: List of tags
        group: Run group
        job_type: Job type
        dir: Directory for run files
        id: Run ID
        resume: Resume existing run
        reinit: Allow reinitialization
        save_code: Save code files
        mode: Run mode (online, offline, disabled)
        **kwargs: Additional arguments
    
    Returns:
        Run object
    """
    
    # Check if run already exists
    current_run = get_current_run()
    if current_run and not reinit:
        if current_run.state == "running":
            logger.warning("Run already initialized, returning existing run")
            return current_run
        elif current_run.state == "finished":
            logger.info("Previous run finished, creating new run")
        else:
            raise TrackLabInitError(f"Run in invalid state: {current_run.state}")
    
    # Update settings based on parameters
    settings_updates = {}
    if mode:
        settings_updates["mode"] = mode
    if save_code is not None:
        settings_updates["save_code"] = save_code
    
    if settings_updates:
        update_settings(**settings_updates)
    
    # Get current settings
    settings = get_settings()
    
    # Validate mode
    if settings.mode not in ["online", "offline", "disabled"]:
        raise TrackLabInitError(f"Invalid mode: {settings.mode}")
    
    if settings.mode == "disabled":
        logger.info("TrackLab is disabled, returning no-op run")
        return _create_noop_run()
    
    # Start backend server if needed
    if settings.mode == "online" and settings.server_auto_start:
        _ensure_backend_server()
    
    # Create run
    try:
        run = Run(
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
            **kwargs
        )
        
        # Register run with backend if online
        if settings.mode == "online":
            _register_run_with_backend(run)
        
        # Set as current run
        set_current_run(run)
        
        # Update global state
        _update_global_state(run)
        
        # Save code if requested
        if settings.save_code:
            run.save()
        
        logger.info(f"TrackLab run initialized: {run.project}/{run.name}")
        
        return run
        
    except Exception as e:
        logger.error(f"Failed to initialize run: {e}")
        raise TrackLabInitError(f"Failed to initialize run: {e}")

def _create_noop_run() -> Run:
    """Create a no-op run for disabled mode"""
    from .tracklab_run import Run
    
    class NoOpRun(Run):
        """No-op run that does nothing"""
        
        def __init__(self):
            # Minimal initialization
            self.id = "noop"
            self.project = "noop"
            self.entity = "noop"
            self.name = "noop"
            self.state = "running"
            
            from .tracklab_config import Config
            from .tracklab_summary import Summary
            self.config = Config()
            self.summary = Summary()
        
        def log(self, *args, **kwargs):
            pass
            
        def save(self, *args, **kwargs):
            pass
            
        def watch(self, *args, **kwargs):
            pass
            
        def finish(self, *args, **kwargs):
            pass
    
    return NoOpRun()

def _ensure_backend_server() -> None:
    """Ensure backend server is running"""
    try:
        import requests
        from ..backend.server.manager import ServerManager
        
        settings = get_settings()
        server_url = f"http://{settings.server_host}:{settings.server_port}"
        
        # Check if server is already running
        try:
            response = requests.get(f"{server_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("Backend server is already running")
                return
        except requests.exceptions.RequestException:
            pass
        
        # Start server
        logger.info("Starting backend server...")
        manager = ServerManager()
        manager.start()
        
        # Wait for server to start
        import time
        for i in range(30):  # Wait up to 30 seconds
            try:
                response = requests.get(f"{server_url}/health", timeout=2)
                if response.status_code == 200:
                    logger.info("Backend server started successfully")
                    return
            except requests.exceptions.RequestException:
                time.sleep(1)
        
        raise TrackLabInitError("Backend server failed to start")
        
    except ImportError:
        logger.warning("Backend server dependencies not available")
    except Exception as e:
        logger.error(f"Failed to start backend server: {e}")
        raise TrackLabInitError(f"Failed to start backend server: {e}")

def _register_run_with_backend(run: Run) -> None:
    """Register run with backend"""
    try:
        from ..apis.internal import get_internal_api
        api = get_internal_api()
        
        # Prepare run data
        run_data = {
            "id": run.id,
            "project": run.project,
            "entity": run.entity,
            "name": run.name,
            "notes": run.notes,
            "tags": run.tags,
            "group": run.group,
            "job_type": run.job_type,
            "state": run.state,
            "start_time": run.start_time,
            "config": run.config.as_dict(),
            "summary": run.summary.as_dict()
        }
        
        # Register with backend
        api.create_run(run_data)
        
        logger.debug(f"Registered run with backend: {run.id}")
        
    except Exception as e:
        logger.error(f"Failed to register run with backend: {e}")
        # Don't fail initialization if backend registration fails
        pass

def _update_global_state(run: Run) -> None:
    """Update global TrackLab state"""
    import tracklab
    
    # Update global objects
    tracklab.run = run
    tracklab.config = run.config
    tracklab.summary = run.summary
    
    # Update log function
    def log(data: Dict[str, Any], **kwargs) -> None:
        if tracklab.run:
            tracklab.run.log(data, **kwargs)
        else:
            raise TrackLabInitError("No active run. Call tracklab.init() first.")
    
    tracklab.log = log

def reinit() -> None:
    """Reinitialize TrackLab (reset global state)"""
    import tracklab
    
    # Clear global state
    tracklab.run = None
    tracklab.config = tracklab._PreInitObject("tracklab.config")
    tracklab.summary = tracklab._PreInitObject("tracklab.summary")
    tracklab.log = tracklab._PreInitCallable("tracklab.log")
    
    # Clear current run
    set_current_run(None)
    
    logger.info("TrackLab state reset")

def is_initialized() -> bool:
    """Check if TrackLab is initialized"""
    return get_current_run() is not None

def require_initialized() -> Run:
    """Require that TrackLab is initialized"""
    run = get_current_run()
    if run is None:
        raise TrackLabInitError("TrackLab not initialized. Call tracklab.init() first.")
    return run