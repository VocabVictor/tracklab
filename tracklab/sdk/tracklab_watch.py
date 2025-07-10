"""
TrackLab watch functionality - model monitoring
"""

from typing import Any, Optional, Union, List

from ..errors import TrackLabError
from ..util.logging import get_logger

logger = get_logger(__name__)

def watch(
    models: Union[Any, List[Any]],
    criterion: Optional[Any] = None,
    log: str = "gradients",
    log_freq: int = 1000,
    idx: Optional[int] = None,
    log_graph: bool = True
) -> None:
    """
    Watch model gradients and parameters
    
    Args:
        models: Model(s) to watch
        criterion: Loss function to watch
        log: What to log ("gradients", "parameters", "all")
        log_freq: Frequency of logging
        idx: Index for multiple models
        log_graph: Whether to log computational graph
    """
    
    # Ensure models is a list
    if not isinstance(models, list):
        models = [models]
    
    # Validate log parameter
    if log not in ["gradients", "parameters", "all"]:
        raise TrackLabError(f"Invalid log parameter: {log}. Must be 'gradients', 'parameters', or 'all'")
    
    logger.info(f"Setting up model watching for {len(models)} model(s)")
    
    # Try to detect framework and set up appropriate watching
    for i, model in enumerate(models):
        model_idx = idx if idx is not None else i
        
        # Check if it's a PyTorch model
        if _is_pytorch_model(model):
            _setup_pytorch_watch(model, criterion, log, log_freq, model_idx, log_graph)
        
        # Check if it's a TensorFlow model
        elif _is_tensorflow_model(model):
            _setup_tensorflow_watch(model, criterion, log, log_freq, model_idx, log_graph)
        
        # Check if it's a Keras model
        elif _is_keras_model(model):
            _setup_keras_watch(model, criterion, log, log_freq, model_idx, log_graph)
        
        else:
            logger.warning(f"Unsupported model type for watching: {type(model)}")

def _is_pytorch_model(model: Any) -> bool:
    """Check if model is a PyTorch model"""
    try:
        import torch
        return isinstance(model, torch.nn.Module)
    except ImportError:
        return False

def _is_tensorflow_model(model: Any) -> bool:
    """Check if model is a TensorFlow model"""
    try:
        import tensorflow as tf
        return isinstance(model, tf.Module)
    except ImportError:
        return False

def _is_keras_model(model: Any) -> bool:
    """Check if model is a Keras model"""
    try:
        import tensorflow as tf
        return isinstance(model, tf.keras.Model)
    except ImportError:
        return False

def _setup_pytorch_watch(
    model: Any,
    criterion: Optional[Any],
    log: str,
    log_freq: int,
    idx: int,
    log_graph: bool
) -> None:
    """Set up PyTorch model watching"""
    try:
        from ..integration.torch import setup_model_watching
        setup_model_watching(model, criterion, log, log_freq, idx, log_graph)
        logger.info(f"PyTorch model watching set up for model {idx}")
    except ImportError:
        logger.error("PyTorch not available for model watching")
    except Exception as e:
        logger.error(f"Failed to set up PyTorch model watching: {e}")

def _setup_tensorflow_watch(
    model: Any,
    criterion: Optional[Any],
    log: str,
    log_freq: int,
    idx: int,
    log_graph: bool
) -> None:
    """Set up TensorFlow model watching"""
    try:
        from ..integration.tensorflow import setup_model_watching
        setup_model_watching(model, criterion, log, log_freq, idx, log_graph)
        logger.info(f"TensorFlow model watching set up for model {idx}")
    except ImportError:
        logger.error("TensorFlow not available for model watching")
    except Exception as e:
        logger.error(f"Failed to set up TensorFlow model watching: {e}")

def _setup_keras_watch(
    model: Any,
    criterion: Optional[Any],
    log: str,
    log_freq: int,
    idx: int,
    log_graph: bool
) -> None:
    """Set up Keras model watching"""
    try:
        from ..integration.tensorflow import setup_keras_watching
        setup_keras_watching(model, criterion, log, log_freq, idx, log_graph)
        logger.info(f"Keras model watching set up for model {idx}")
    except ImportError:
        logger.error("Keras not available for model watching")
    except Exception as e:
        logger.error(f"Failed to set up Keras model watching: {e}")

def unwatch(models: Union[Any, List[Any]]) -> None:
    """
    Stop watching models
    
    Args:
        models: Model(s) to stop watching
    """
    
    # Ensure models is a list
    if not isinstance(models, list):
        models = [models]
    
    logger.info(f"Stopping model watching for {len(models)} model(s)")
    
    for model in models:
        # Try to remove hooks based on framework
        if _is_pytorch_model(model):
            _remove_pytorch_hooks(model)
        elif _is_tensorflow_model(model) or _is_keras_model(model):
            _remove_tensorflow_hooks(model)

def _remove_pytorch_hooks(model: Any) -> None:
    """Remove PyTorch model hooks"""
    try:
        # Remove hooks if they exist
        if hasattr(model, '_tracklab_hooks'):
            for hook in model._tracklab_hooks:
                hook.remove()
            delattr(model, '_tracklab_hooks')
        logger.debug("PyTorch hooks removed")
    except Exception as e:
        logger.error(f"Failed to remove PyTorch hooks: {e}")

def _remove_tensorflow_hooks(model: Any) -> None:
    """Remove TensorFlow model hooks"""
    try:
        # Remove callbacks if they exist
        if hasattr(model, '_tracklab_callbacks'):
            # This would be framework-specific
            pass
        logger.debug("TensorFlow hooks removed")
    except Exception as e:
        logger.error(f"Failed to remove TensorFlow hooks: {e}")

class ModelWatcher:
    """
    Model watcher for manual control
    """
    
    def __init__(self, model: Any, log: str = "gradients", log_freq: int = 1000):
        self.model = model
        self.log = log
        self.log_freq = log_freq
        self.step_count = 0
        self.watching = False
    
    def start(self) -> None:
        """Start watching the model"""
        watch(self.model, log=self.log, log_freq=self.log_freq)
        self.watching = True
        logger.info("Model watching started")
    
    def stop(self) -> None:
        """Stop watching the model"""
        unwatch(self.model)
        self.watching = False
        logger.info("Model watching stopped")
    
    def step(self) -> None:
        """Manual step for logging"""
        self.step_count += 1
        if self.watching and self.step_count % self.log_freq == 0:
            self._log_metrics()
    
    def _log_metrics(self) -> None:
        """Log model metrics"""
        from .tracklab_init import get_current_run
        
        run = get_current_run()
        if not run:
            return
        
        # Framework-specific metric logging would go here
        logger.debug(f"Logging model metrics at step {self.step_count}")
    
    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()