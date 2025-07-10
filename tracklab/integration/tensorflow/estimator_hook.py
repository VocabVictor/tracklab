"""TensorFlow estimator hook for TrackLab integration."""

try:
    import tensorflow as tf
    _tensorflow_available = True
except ImportError:
    _tensorflow_available = False
    tf = None

from typing import Dict, Any, Optional


class TrackLabHook:
    """TensorFlow SessionRunHook for automatic logging to TrackLab."""
    
    def __init__(self, 
                 log_frequency: int = 100,
                 include_params: bool = True):
        if not _tensorflow_available:
            raise ImportError("TensorFlow is not installed. Please install tensorflow to use this integration.")
            
        self.log_frequency = log_frequency
        self.include_params = include_params
        self._step_count = 0
        self._current_run = None
        
    def begin(self):
        """Called once before using the session."""
        # Get current tracklab run
        try:
            import tracklab
            self._current_run = tracklab.run
        except (ImportError, AttributeError):
            self._current_run = None
            
    def before_run(self, run_context):
        """Called before each call to run()."""
        # Could request specific tensors to log
        return None
        
    def after_run(self, run_context, run_values):
        """Called after each call to run()."""
        self._step_count += 1
        
        if self._current_run and self._step_count % self.log_frequency == 0:
            # Log basic step information
            self._current_run.log({
                "tensorflow/step": self._step_count,
                "tensorflow/global_step": self._step_count
            })
            
    def end(self, session):
        """Called at the end of session."""
        if self._current_run:
            self._current_run.log({
                "tensorflow/total_steps": self._step_count
            })


def log_model_info(model, name: str = "tensorflow_model"):
    """Log TensorFlow model information."""
    if not _tensorflow_available:
        return
        
    try:
        import tracklab
        if tracklab.run is None:
            return
            
        # Log model summary if available
        if hasattr(model, 'summary'):
            # For Keras models
            try:
                model_config = model.get_config()
                tracklab.run.log({
                    f"{name}/layers": len(model_config.get('layers', [])),
                    f"{name}/trainable_params": model.count_params() if hasattr(model, 'count_params') else 0
                })
            except Exception:
                pass
                
    except ImportError:
        pass