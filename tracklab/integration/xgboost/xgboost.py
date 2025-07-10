"""XGBoost integration for TrackLab."""

try:
    import xgboost as xgb
    _xgboost_available = True
except ImportError:
    _xgboost_available = False
    xgb = None

from typing import Dict, Any, Optional


class TrackLabCallback:
    """XGBoost callback for logging to TrackLab."""
    
    def __init__(self, log_frequency: int = 1):
        if not _xgboost_available:
            raise ImportError("XGBoost is not installed. Please install xgboost to use this integration.")
            
        self.log_frequency = log_frequency
        self._current_run = None
        
    def __call__(self, env):
        """Callback function called by XGBoost."""
        if self._current_run is None:
            try:
                import tracklab
                self._current_run = tracklab.run
            except (ImportError, AttributeError):
                return
                
        if self._current_run and env.iteration % self.log_frequency == 0:
            # Log training metrics
            metrics = {}
            
            # Log evaluation results from env.evaluation_result_list
            for eval_name, eval_score in env.evaluation_result_list:
                metrics[f"xgboost/{eval_name}"] = eval_score
                
            metrics["xgboost/iteration"] = env.iteration
            self._current_run.log(metrics)


def log_model(model, name: str = "xgboost_model"):
    """Log XGBoost model information."""
    if not _xgboost_available:
        return
        
    try:
        import tracklab
        if tracklab.run is None:
            return
            
        # Log model info
        model_info = {}
        
        if hasattr(model, 'num_boosted_rounds'):
            model_info[f"{name}/num_boosted_rounds"] = model.num_boosted_rounds()
            
        if hasattr(model, 'num_features'):
            model_info[f"{name}/num_features"] = model.num_features()
            
        # Log feature importance
        try:
            importance = model.get_fscore()
            if importance:
                avg_importance = sum(importance.values()) / len(importance)
                model_info[f"{name}/avg_feature_importance"] = avg_importance
                model_info[f"{name}/num_important_features"] = len(importance)
                
        except Exception:
            pass
            
        if model_info:
            tracklab.run.log(model_info)
            
    except ImportError:
        pass