from __future__ import annotations

__all__ = ("Sentry",)

import os
from typing import TYPE_CHECKING, Any, Optional
from typing_extensions import Never

from .local_analytics import LocalAnalytics, SessionStatus

if TYPE_CHECKING:
    from types import TracebackType


class Sentry:
    """Adapter class to maintain compatibility with the original Sentry interface.
    
    This class wraps LocalAnalytics and provides the same interface as the original
    Sentry integration, but stores all data locally instead of sending to Sentry.
    """
    
    def __init__(self) -> None:
        self._analytics = LocalAnalytics()
        self._disabled = self._analytics._disabled
        self.dsn = "local://analytics"  # Fake DSN for compatibility
        self.scope = None  # Compatibility attribute
    
    @property
    def environment(self) -> str:
        """Return the environment we're running in."""
        return self._analytics.environment
    
    def setup(self) -> None:
        """Setup analytics SDK."""
        self._analytics.setup()
    
    def message(self, message: str, repeat: bool = True) -> str | None:
        """Send a message to analytics."""
        return self._analytics.message(message, repeat=repeat)
    
    def exception(
        self,
        exc: str
        | BaseException
        | tuple[
            type[BaseException] | None,
            BaseException | None,
            TracebackType | None,
        ]
        | None,
        handled: bool = False,
        status: SessionStatus | None = None,
    ) -> str | None:
        """Log an exception to analytics."""
        return self._analytics.exception(exc, handled=handled, status=status)
    
    def reraise(self, exc: Any) -> Never:
        """Re-raise an exception after logging it to analytics."""
        self._analytics.reraise(exc)
    
    def start_session(self) -> None:
        """Start a new session."""
        self._analytics.start_session()
    
    def end_session(self) -> None:
        """End the current session."""
        self._analytics.end_session()
    
    def mark_session(self, status: SessionStatus | None = None) -> None:
        """Mark the current session with a status."""
        self._analytics.mark_session(status=status)
    
    def configure_scope(
        self,
        tags: dict[str, Any] | None = None,
        process_context: str | None = None,
    ) -> None:
        """Configure the analytics scope for the current thread."""
        self._analytics.configure_scope(tags=tags, process_context=process_context)