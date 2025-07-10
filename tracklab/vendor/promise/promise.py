"""Simple Promise implementation."""

import threading
from typing import Any, Callable, Optional, Union
from concurrent.futures import ThreadPoolExecutor, Future


class Promise:
    """A simple Promise implementation for asynchronous operations.
    
    This is a simplified version of JavaScript-style Promises,
    adapted for TrackLab's needs.
    """
    
    def __init__(self, executor_fn: Optional[Callable] = None):
        self._state = "pending"  # pending, fulfilled, rejected
        self._value: Any = None
        self._reason: Any = None
        self._callbacks = []
        self._error_callbacks = []
        self._lock = threading.Lock()
        
        if executor_fn:
            try:
                executor_fn(self._resolve, self._reject)
            except Exception as e:
                self._reject(e)
                
    def _resolve(self, value: Any):
        """Resolve the promise with a value."""
        with self._lock:
            if self._state == "pending":
                self._state = "fulfilled"
                self._value = value
                for callback in self._callbacks:
                    try:
                        callback(value)
                    except Exception as e:
                        # Silent error handling for callbacks
                        pass
                        
    def _reject(self, reason: Any):
        """Reject the promise with a reason."""
        with self._lock:
            if self._state == "pending":
                self._state = "rejected"
                self._reason = reason
                for callback in self._error_callbacks:
                    try:
                        callback(reason)
                    except Exception as e:
                        # Silent error handling for callbacks
                        pass
                        
    def then(self, on_fulfilled: Optional[Callable] = None, on_rejected: Optional[Callable] = None) -> 'Promise':
        """Add success and error callbacks."""
        new_promise = Promise()
        
        def handle_fulfilled(value):
            try:
                if on_fulfilled:
                    result = on_fulfilled(value)
                    new_promise._resolve(result)
                else:
                    new_promise._resolve(value)
            except Exception as e:
                new_promise._reject(e)
                
        def handle_rejected(reason):
            try:
                if on_rejected:
                    result = on_rejected(reason)
                    new_promise._resolve(result)
                else:
                    new_promise._reject(reason)
            except Exception as e:
                new_promise._reject(e)
                
        with self._lock:
            if self._state == "fulfilled":
                handle_fulfilled(self._value)
            elif self._state == "rejected":
                handle_rejected(self._reason)
            else:
                self._callbacks.append(handle_fulfilled)
                self._error_callbacks.append(handle_rejected)
                
        return new_promise
        
    def catch(self, on_rejected: Callable) -> 'Promise':
        """Add error callback."""
        return self.then(None, on_rejected)
        
    def finally_do(self, on_finally: Callable) -> 'Promise':
        """Add callback that runs regardless of outcome."""
        def handle_finally(value):
            on_finally()
            return value
            
        return self.then(handle_finally, handle_finally)
        
    @property
    def is_pending(self) -> bool:
        return self._state == "pending"
        
    @property
    def is_fulfilled(self) -> bool:
        return self._state == "fulfilled"
        
    @property
    def is_rejected(self) -> bool:
        return self._state == "rejected"
        
    @property
    def value(self) -> Any:
        """Get the resolved value (None if not fulfilled)."""
        return self._value if self.is_fulfilled else None
        
    @property
    def reason(self) -> Any:
        """Get the rejection reason (None if not rejected)."""
        return self._reason if self.is_rejected else None
        
    @staticmethod
    def resolve(value: Any) -> 'Promise':
        """Create a Promise that resolves to the given value."""
        promise = Promise()
        promise._resolve(value)
        return promise
        
    @staticmethod
    def reject(reason: Any) -> 'Promise':
        """Create a Promise that rejects with the given reason."""
        promise = Promise()
        promise._reject(reason)
        return promise
        
    @staticmethod
    def all(promises: list) -> 'Promise':
        """Wait for all promises to resolve."""
        result_promise = Promise()
        results = [None] * len(promises)
        completed = [False] * len(promises)
        
        def check_completion():
            if all(completed):
                result_promise._resolve(results)
                
        for i, promise in enumerate(promises):
            def make_callback(index):
                def callback(value):
                    results[index] = value
                    completed[index] = True
                    check_completion()
                return callback
                
            def error_callback(reason):
                result_promise._reject(reason)
                
            promise.then(make_callback(i), error_callback)
            
        return result_promise