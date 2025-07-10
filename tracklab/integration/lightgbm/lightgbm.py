"""LightGBM integration for TrackLab."""

try:
    import lightgbm as lgb
    _lightgbm_available = True
except ImportError:
    _lightgbm_available = False
    lgb = None

from typing import Dict, Any, Optional


class TrackLabCallback:
    """LightGBM callback for logging to TrackLab."""
    
    def __init__(self, log_frequency: int = 1):
        if not _lightgbm_available:
            raise ImportError("LightGBM is not installed. Please install lightgbm to use this integration.")
            
        self.log_frequency = log_frequency
        self._current_run = None
        
    def __call__(self, env):
        """Callback function called by LightGBM."""
        if self._current_run is None:
            try:
                import tracklab
                self._current_run = tracklab.run
            except (ImportError, AttributeError):
                return
                
        if self._current_run and env.iteration % self.log_frequency == 0:
            # Log training metrics
            metrics = {}
            
            # Log evaluation results
            for eval_result in env.evaluation_result_list:
                data_name, eval_name, score, _ = eval_result
                metrics[f"lightgbm/{data_name}_{eval_name}"] = score
                
            metrics["lightgbm/iteration"] = env.iteration
            self._current_run.log(metrics)


def log_model(model, name: str = "lightgbm_model"):
    """Log LightGBM model information."""
    if not _lightgbm_available:
        return
        
    try:
        import tracklab
        if tracklab.run is None:
            return
            
        # Log model parameters and info
        model_info = {
            f"{name}/num_trees": model.num_trees(),
            f"{name}/num_features": model.num_feature(),
        }
        
        # Log feature importance
        try:
            importance = model.feature_importance()
            if len(importance) > 0:
                model_info[f"{name}/avg_feature_importance"] = float(importance.mean())
                model_info[f"{name}/max_feature_importance"] = float(importance.max())
                
        except Exception:
            pass
            
        tracklab.run.log(model_info)
        
    except ImportError:
        pass