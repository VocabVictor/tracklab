"""Python agent implementation."""

from typing import Dict, Any, Optional, Callable
import threading
import time


class PyAgent:
    """Python-based agent for automated experiment management.
    
    Simplified version of wandb's agent functionality for local sweep operations.
    """
    
    def __init__(self, 
                 sweep_config: Optional[Dict[str, Any]] = None,
                 function: Optional[Callable] = None,
                 count: Optional[int] = None):
        self.sweep_config = sweep_config or {}
        self.function = function
        self.count = count
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self.run_count = 0
        
    def start(self):
        """Start the agent."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the agent."""
        self._running = False
        if self._thread:
            self._thread.join()
            
    def _run_loop(self):
        """Main agent execution loop."""
        while self._running:
            if self.count is not None and self.run_count >= self.count:
                break
                
            if self.function:
                try:
                    self.function()
                    self.run_count += 1
                except Exception as e:
                    print(f"Agent function error: {e}")
                    
            time.sleep(1)  # Basic delay between runs
            
        self._running = False
        
    @property
    def is_running(self) -> bool:
        """Check if agent is running."""
        return self._running
        
    def __repr__(self) -> str:
        return f"PyAgent(runs={self.run_count}, running={self.is_running})"