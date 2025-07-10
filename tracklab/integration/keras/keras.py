"""Keras callback for TrackLab integration."""

try:
    import tensorflow as tf
    from tensorflow import keras
    _keras_available = True
except ImportError:
    try:
        import keras
        _keras_available = True
    except ImportError:
        _keras_available = False
        keras = None

from typing import Dict, Any, Optional, List


class TrackLabCallback:
    """Keras callback for automatic logging to TrackLab."""
    
    def __init__(self, 
                 log_frequency: int = 1,
                 log_weights: bool = False,
                 log_gradients: bool = False):
        if not _keras_available:
            raise ImportError("Keras is not installed. Please install keras or tensorflow to use this integration.")
            
        self.log_frequency = log_frequency
        self.log_weights = log_weights
        self.log_gradients = log_gradients
        self._current_run = None
        
    def on_train_begin(self, logs: Optional[Dict] = None):
        """Called at the beginning of training."""
        try:
            import tracklab
            self._current_run = tracklab.run
            
            if self._current_run:
                # Log model architecture info
                model = getattr(self, 'model', None)
                if model:
                    self._log_model_info(model)
        except (ImportError, AttributeError):
            self._current_run = None
            
    def on_epoch_end(self, epoch: int, logs: Optional[Dict] = None):
        """Called at the end of each epoch."""
        if not self._current_run or not logs:
            return
            
        if epoch % self.log_frequency == 0:
            # Log metrics
            metrics = {f"keras/{k}": v for k, v in logs.items()}
            metrics["keras/epoch"] = epoch
            self._current_run.log(metrics)
            
    def on_train_end(self, logs: Optional[Dict] = None):
        """Called at the end of training."""
        if self._current_run and logs:
            final_metrics = {f"keras/final_{k}": v for k, v in logs.items()}
            self._current_run.log(final_metrics)
            
    def _log_model_info(self, model):
        """Log model architecture information."""
        try:
            info = {
                "keras/total_params": model.count_params(),
                "keras/trainable_params": sum([tf.size(w).numpy() for w in model.trainable_weights]) if hasattr(tf, 'size') else 0,
                "keras/layers": len(model.layers)
            }
            
            # Add optimizer info
            if hasattr(model, 'optimizer') and model.optimizer:
                info["keras/optimizer"] = model.optimizer.__class__.__name__
                if hasattr(model.optimizer, 'learning_rate'):
                    lr = model.optimizer.learning_rate
                    if hasattr(lr, 'numpy'):
                        info["keras/learning_rate"] = float(lr.numpy())
                    else:
                        info["keras/learning_rate"] = float(lr)
                        
            self._current_run.log(info)
        except Exception as e:
            print(f"Warning: Could not log model info: {e}")


def log_model(model, name: str = "keras_model"):
    """Log Keras model information manually."""
    if not _keras_available:
        return
        
    try:
        import tracklab
        if tracklab.run is None:
            return
            
        info = {
            f"{name}/total_params": model.count_params(),
            f"{name}/layers": len(model.layers)
        }
        
        # Add model summary as text
        try:
            import io
            string_buffer = io.StringIO()
            model.summary(print_fn=lambda x: string_buffer.write(x + '\n'))
            summary_str = string_buffer.getvalue()
            info[f"{name}/summary"] = summary_str
        except Exception:
            pass
            
        tracklab.run.log(info)
        
    except ImportError:
        pass