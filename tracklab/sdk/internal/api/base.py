"""Base API class with core functionality."""

import datetime
import logging
import os
import threading
from typing import Any, Dict, Optional, Union

import tracklab
from tracklab import env
from tracklab.sdk.internal import context
from tracklab.sdk.internal.thread_local_settings import _thread_local_api_settings

logger = logging.getLogger(__name__)


class _ThreadLocalData(threading.local):
    """Thread-local storage for API context."""
    
    context: Optional[context.Context]

    def __init__(self) -> None:
        self.context = None


class ApiBase:
    """Base class for W&B Internal Api wrapper.
    
    This class provides core functionality like authentication, settings management,
    and basic API operations. All other API functionality is provided through mixins.
    """
    
    HTTP_TIMEOUT = env.get_http_timeout(20)
    FILE_PUSHER_TIMEOUT = env.get_file_pusher_timeout()
    _global_context: context.Context
    _local_data: _ThreadLocalData
    
    def __init__(
        self,
        default_settings: Optional[Dict] = None,
        load_settings: bool = True,
        retry_timedelta: datetime.timedelta = datetime.timedelta(days=7),
        proxies: Optional[Dict[str, str]] = None,
        overrides: Optional[Dict[str, Any]] = None,
        cookie_authentication_enabled: bool = False,
    ) -> None:
        """Initialize the API client.
        
        Args:
            default_settings: Default settings to use
            load_settings: Whether to load settings from file
            retry_timedelta: Retry window for failed requests
            proxies: Proxy configuration
            overrides: Settings overrides
            cookie_authentication_enabled: Whether to enable cookie auth
        """
        self._local_data = _ThreadLocalData()
        self._retry_timedelta = retry_timedelta
        self._proxies = proxies
        self._max_cli_version = None
        self._current_run_id = None
        self.dynamic_settings = {"system_sample_seconds": 2, "system_samples": 15}
        self.retry_uploads = 10
        self._viewer = None
        self._default_entity = None  # Use private attribute to avoid property conflict
        self._teams = {}
        self.cookie_authentication_enabled = cookie_authentication_enabled
        
        # Mock settings for now
        self.default_settings = default_settings or {}
        self.overrides = overrides or {}
        
        # Initialize global context
        self._global_context = context.Context()
        
    def set_local_context(self, api_context: Optional[context.Context]) -> None:
        """Set thread-local API context."""
        self._local_data.context = api_context
        
    def clear_local_context(self) -> None:
        """Clear thread-local API context."""
        self._local_data.context = None
        
    @property
    def context(self) -> context.Context:
        """Get current context (thread-local or global)."""
        return self._local_data.context or self._global_context
        
    def set_current_run_id(self, run_id: str) -> None:
        """Set the current run ID."""
        self._current_run_id = run_id
        
    @property
    def current_run_id(self) -> Optional[str]:
        """Get the current run ID."""
        return self._current_run_id
        
    @property
    def user_agent(self) -> str:
        """Get the user agent string."""
        return f"TrackLab Internal Client {tracklab.__version__}"
        
    @property
    def api_key(self) -> Optional[str]:
        """Get the API key."""
        if _thread_local_api_settings.api_key:
            return _thread_local_api_settings.api_key
        # For local TrackLab, we don't need a real API key
        return "local-tracklab-key"
        
    @property
    def api_url(self) -> str:
        """Get the API URL."""
        return self.settings("base_url") or "http://localhost:8080"
        
    @property
    def app_url(self) -> str:
        """Get the app URL."""
        return tracklab.util.app_url(self.api_url)
        
    def settings(self, key: Optional[str] = None, section: Optional[str] = None) -> Any:
        """Get settings value."""
        if key:
            return self.default_settings.get(key, self.overrides.get(key))
        return self.default_settings
        
    def clear_setting(
        self, key: str, globally: bool = False, persist: bool = False
    ) -> None:
        """Clear a setting."""
        if key in self.overrides:
            del self.overrides[key]
            
    def set_setting(
        self, key: str, value: Any, globally: bool = False, persist: bool = False
    ) -> None:
        """Set a setting value."""
        self.overrides[key] = value
        
    def format_project(self, project: str) -> str:
        """Format project name to be URL-safe."""
        import re
        return re.sub(r"\W+", "-", project.lower()).strip("-_")
    
    @property
    def default_entity(self):
        """Get default entity."""
        return self._default_entity
    
    @default_entity.setter
    def default_entity(self, value):
        """Set default entity."""
        self._default_entity = value
    
    def _fetch_orgs_and_org_entities_from_entity(self, entity: str):
        """Mock implementation for organization fetching.
        
        This is a stub for compatibility with tests that expect this method.
        In a local-only system, we don't need to fetch organizations from a server.
        """
        # Return empty list - no organizations in local system
        return []