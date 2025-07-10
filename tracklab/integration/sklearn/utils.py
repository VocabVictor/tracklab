"""Scikit-learn utilities for TrackLab."""

try:
    import sklearn
    _sklearn_available = True
except ImportError:
    _sklearn_available = False
    sklearn = None

from typing import Any, Optional, Dict
import json


def log_sklearn_model(model: Any, 
                      X_test: Any = None, 
                      y_test: Any = None,
                      name: str = "sklearn_model"):
    """Log scikit-learn model information and performance."""
    if not _sklearn_available:
        print("Warning: scikit-learn not available")
        return
        
    try:
        import tracklab
        if tracklab.run is None:
            return
            
        # Log model type and parameters
        model_info = {
            f"{name}/model_type": model.__class__.__name__,
            f"{name}/parameters": str(model.get_params())
        }
        
        # Log model performance if test data provided
        if X_test is not None and y_test is not None:
            try:
                score = model.score(X_test, y_test)
                model_info[f"{name}/test_score"] = score
                
                # Log predictions for classification
                if hasattr(model, 'predict_proba'):
                    y_pred = model.predict(X_test)
                    
                    # Calculate additional metrics for classification
                    try:
                        from sklearn.metrics import classification_report, confusion_matrix
                        
                        # Classification report
                        report = classification_report(y_test, y_pred, output_dict=True)
                        model_info[f"{name}/precision"] = report['weighted avg']['precision']
                        model_info[f"{name}/recall"] = report['weighted avg']['recall']
                        model_info[f"{name}/f1_score"] = report['weighted avg']['f1-score']
                        
                    except ImportError:
                        pass
                        
            except Exception as e:
                print(f"Warning: Could not calculate model performance: {e}")
                
        tracklab.run.log(model_info)
        
    except ImportError:
        pass


def log_feature_importance(model: Any, feature_names: Optional[list] = None, name: str = "feature_importance"):
    """Log feature importance for models that support it."""
    if not _sklearn_available:
        return
        
    try:
        import tracklab
        if tracklab.run is None:
            return
            
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            
            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(len(importances))]
                
            # Create feature importance data
            importance_data = [
                {"feature": feat, "importance": float(imp)} 
                for feat, imp in zip(feature_names, importances)
            ]
            
            # Sort by importance
            importance_data.sort(key=lambda x: x['importance'], reverse=True)
            
            # Log top features
            top_features = importance_data[:10]  # Top 10 features
            for i, item in enumerate(top_features):
                tracklab.run.log({
                    f"{name}/top_{i+1}_feature": item['feature'],
                    f"{name}/top_{i+1}_importance": item['importance']
                })
                
        elif hasattr(model, 'coef_'):
            # For linear models, use coefficients
            coef = model.coef_
            if coef.ndim > 1:
                coef = coef[0]  # Take first class for multiclass
                
            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(len(coef))]
                
            # Log top coefficients by absolute value
            coef_data = [
                {"feature": feat, "coefficient": float(c)} 
                for feat, c in zip(feature_names, coef)
            ]
            
            coef_data.sort(key=lambda x: abs(x['coefficient']), reverse=True)
            
            top_coef = coef_data[:10]
            for i, item in enumerate(top_coef):
                tracklab.run.log({
                    f"{name}/top_{i+1}_feature": item['feature'],
                    f"{name}/top_{i+1}_coefficient": item['coefficient']
                })
                
    except ImportError:
        pass