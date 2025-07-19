"""HTTP/network utilities, error handling, and retry logic."""

import os
import socket
import threading
import webbrowser
from datetime import timedelta
from typing import Any, Callable, Optional, Union

import requests

# Thread-local storage for API settings
_thread_local_api_settings = threading.local()


def app_url(api_url: str) -> str:
    """Return the frontend app url without a trailing slash."""
    # TODO: move me to settings
    import tracklab.env
    app_url = tracklab.env.get_app_url()
    if app_url is not None:
        return str(app_url.strip("/"))
    
    # Fallback logic
    if api_url.endswith("/graphql"):
        return api_url[:-8]
    elif api_url.endswith("/api/v1"):
        return api_url[:-7]
    else:
        return api_url.rstrip("/")


def launch_browser(attempt_launch_browser: bool = True) -> bool:
    """Decide if we should launch a browser."""
    _display_variables = ["DISPLAY", "WAYLAND_DISPLAY", "MIR_SOCKET"]
    _webbrowser_names_blocklist = ["www-browser", "lynx", "links", "elinks", "w3m"]

    if not attempt_launch_browser:
        return False

    # Check if we have a display
    if not any(os.environ.get(var) for var in _display_variables):
        return False

    # Check if we have a valid browser
    try:
        browser = webbrowser.get()
        if any(name in browser.name for name in _webbrowser_names_blocklist):
            return False
    except webbrowser.Error:
        return False

    return True


def _has_internet() -> bool:
    """Returns whether we have internet access.

    Checks for internet access by attempting to open a DNS connection to
    Google's root servers.
    """
    try:
        # Connect to Google's DNS servers
        socket.setdefaulttimeout(3)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        return True
    except OSError:
        return False


def no_retry_4xx(e: Exception) -> bool:
    """Check if we should not retry on 4xx errors."""
    if not isinstance(e, requests.HTTPError):
        return True
    assert e.response is not None
    if not (400 <= e.response.status_code < 500) or e.response.status_code == 429:
        return True
    return False


def no_retry_auth(e: Any) -> bool:
    """Check if we should not retry on auth errors."""
    if hasattr(e, "exception"):
        e = e.exception
    if not isinstance(e, requests.HTTPError):
        return True
    if e.response is None:
        return True
    if e.response.status_code == 401:
        return False
    return True


def parse_backend_error_messages(e: Any) -> str:
    """Parse backend error messages from exceptions."""
    if hasattr(e, "exception"):
        e = e.exception
    if isinstance(e, requests.HTTPError) and e.response is not None:
        try:
            error_data = e.response.json()
            if "errors" in error_data:
                return "; ".join(error_data["errors"])
            elif "message" in error_data:
                return error_data["message"]
        except (ValueError, KeyError):
            pass
    return str(e)


def check_retry_conflict(e: Any) -> Optional[bool]:
    """Check if the exception is a conflict type so it can be retried.

    Returns:
        True - Should retry this operation
        False - Should not retry this operation
        None - Don't know, use fallback
    """
    if hasattr(e, "exception"):
        e = e.exception
    if isinstance(e, requests.HTTPError) and e.response is not None:
        if e.response.status_code == 409:  # Conflict
            return True
    return None


def check_retry_conflict_or_gone(e: Any) -> Optional[bool]:
    """Check if the exception is a conflict or gone type, so it can be retried or not.

    Returns:
        True - Should retry this operation
        False - Should not retry this operation
        None - Don't know, use fallback
    """
    if hasattr(e, "exception"):
        e = e.exception
    if isinstance(e, requests.HTTPError) and e.response is not None:
        if e.response.status_code == 409:  # Conflict
            return True
        elif e.response.status_code == 410:  # Gone
            return False
    return None


def make_check_retry_fn(
    check_fn: Callable[[Any], Optional[bool]],
    fallback_retry_fn: Callable[[Exception], Union[bool, timedelta]],
) -> Callable[[Exception], Union[bool, timedelta]]:
    """Create a retry check function that combines custom logic with fallback."""
    def check_retry_fn(e: Exception) -> Union[bool, timedelta]:
        check = check_fn(e)
        if check is None:
            return fallback_retry_fn(e)
        if check is False:
            return False
        return True
    
    return check_retry_fn


def download_file_from_url(
    dest_path: str, source_url: str, api_key: Optional[str] = None
) -> None:
    """Download a file from a URL to a destination path."""
    auth = None
    if not hasattr(_thread_local_api_settings, 'cookies') or not _thread_local_api_settings.cookies:
        auth = ("api", api_key or "")
    
    response = requests.get(
        source_url,
        auth=auth,
        cookies=getattr(_thread_local_api_settings, 'cookies', None),
        stream=True,
        timeout=30,
    )
    response.raise_for_status()
    
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def download_file_into_memory(source_url: str, api_key: Optional[str] = None) -> bytes:
    """Download a file from a URL into memory."""
    auth = None
    if not hasattr(_thread_local_api_settings, 'cookies') or not _thread_local_api_settings.cookies:
        auth = ("api", api_key or "")
    
    response = requests.get(
        source_url,
        auth=auth,
        cookies=getattr(_thread_local_api_settings, 'cookies', None),
        timeout=30,
    )
    response.raise_for_status()
    return response.content


__all__ = [
    "app_url",
    "launch_browser",
    "_has_internet",
    "no_retry_4xx",
    "no_retry_auth",
    "parse_backend_error_messages",
    "check_retry_conflict",
    "check_retry_conflict_or_gone",
    "make_check_retry_fn",
    "download_file_from_url",
    "download_file_into_memory",
]