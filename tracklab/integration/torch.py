"""
TrackLab PyTorch integration
"""

from typing import Any, Optional, List, Dict
import warnings

from ..util.logging import get_logger

logger = get_logger(__name__)

def setup_model_watching(
    model: Any,
    criterion: Optional[Any],
    log: str,
    log_freq: int,
    idx: int,
    log_graph: bool
) -> None:
    """Set up PyTorch model watching"""
    
    try:
        import torch
        import torch.nn as nn
    except ImportError:
        raise ImportError("PyTorch not available")
    
    if not isinstance(model, nn.Module):
        raise ValueError("Model must be a PyTorch nn.Module")
    
    # Store hooks for later removal
    if not hasattr(model, '_tracklab_hooks'):
        model._tracklab_hooks = []
    
    # Set up parameter and gradient hooks
    if log in ["parameters", "all"]:
        _setup_parameter_hooks(model, log_freq, idx)
    
    if log in ["gradients", "all"]:
        _setup_gradient_hooks(model, log_freq, idx)
    
    # Store watching configuration
    model._tracklab_watch_config = {
        "log": log,
        "log_freq": log_freq,
        "idx": idx,
        "log_graph": log_graph,
        "step_count": 0
    }
    
    logger.info(f"PyTorch model watching configured for model {idx}")

def _setup_parameter_hooks(model: Any, log_freq: int, idx: int) -> None:
    """Set up parameter monitoring hooks"""
    
    def parameter_hook(module, input, output):
        """Hook to log parameters"""
        config = model._tracklab_watch_config
        config["step_count"] += 1
        
        if config["step_count"] % log_freq == 0:
            _log_parameters(model, idx, config["step_count"])
    
    # Register forward hook
    hook = model.register_forward_hook(parameter_hook)
    model._tracklab_hooks.append(hook)

def _setup_gradient_hooks(model: Any, log_freq: int, idx: int) -> None:
    """Set up gradient monitoring hooks"""
    
    def gradient_hook(grad):
        """Hook to log gradients"""
        config = model._tracklab_watch_config
        if config["step_count"] % log_freq == 0:
            _log_gradients(model, idx, config["step_count"])
        return grad
    
    # Register backward hooks on parameters
    for name, param in model.named_parameters():
        if param.requires_grad:
            hook = param.register_hook(gradient_hook)
            model._tracklab_hooks.append(hook)

def _log_parameters(model: Any, idx: int, step: int) -> None:
    """Log model parameters"""
    from ..sdk.tracklab_init import get_current_run
    
    run = get_current_run()
    if not run:
        return
    
    import torch
    
    # Collect parameter statistics
    param_stats = {}
    
    for name, param in model.named_parameters():
        if param.data is not None:
            param_name = f"model_{idx}/parameters/{name}"
            
            # Basic statistics
            param_stats[f"{param_name}/mean"] = param.data.mean().item()
            param_stats[f"{param_name}/std"] = param.data.std().item()
            param_stats[f"{param_name}/min"] = param.data.min().item()
            param_stats[f"{param_name}/max"] = param.data.max().item()
            param_stats[f"{param_name}/norm"] = param.data.norm().item()
    
    # Log to run
    run.log(param_stats, step=step)

def _log_gradients(model: Any, idx: int, step: int) -> None:
    """Log model gradients"""
    from ..sdk.tracklab_init import get_current_run
    
    run = get_current_run()
    if not run:
        return
    
    import torch
    
    # Collect gradient statistics
    grad_stats = {}
    
    for name, param in model.named_parameters():
        if param.grad is not None:
            grad_name = f"model_{idx}/gradients/{name}"
            
            # Basic statistics
            grad_stats[f"{grad_name}/mean"] = param.grad.mean().item()
            grad_stats[f"{grad_name}/std"] = param.grad.std().item()
            grad_stats[f"{grad_name}/min"] = param.grad.min().item()
            grad_stats[f"{grad_name}/max"] = param.grad.max().item()
            grad_stats[f"{grad_name}/norm"] = param.grad.norm().item()
    
    # Log to run
    run.log(grad_stats, step=step)

def watch_model(
    models: Any,
    criterion: Optional[Any] = None,
    log: str = "gradients",
    log_freq: int = 1000,
    idx: Optional[int] = None,
    log_graph: bool = True,
    run: Optional[Any] = None
) -> None:
    """
    Watch PyTorch models (called from SDK)
    
    Args:
        models: Model(s) to watch
        criterion: Loss function
        log: What to log
        log_freq: Logging frequency
        idx: Model index
        log_graph: Whether to log graph
        run: TrackLab run object
    """
    
    # Ensure models is a list
    if not isinstance(models, list):
        models = [models]
    
    for i, model in enumerate(models):
        model_idx = idx if idx is not None else i
        setup_model_watching(model, criterion, log, log_freq, model_idx, log_graph)

def log_model_summary(model: Any, input_shape: Optional[tuple] = None) -> None:
    """Log model summary"""
    from ..sdk.tracklab_init import get_current_run
    
    run = get_current_run()
    if not run:
        return
    
    try:
        import torch
        import torch.nn as nn
        
        if not isinstance(model, nn.Module):
            logger.warning("Model is not a PyTorch nn.Module")
            return
        
        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        
        # Log model info
        model_info = {
            "model/total_parameters": total_params,
            "model/trainable_parameters": trainable_params,
            "model/non_trainable_parameters": total_params - trainable_params,
            "model/layers": len(list(model.modules())),
        }
        
        run.log(model_info)
        
        # Try to get more detailed summary if input shape provided
        if input_shape:
            try:
                # Create dummy input
                dummy_input = torch.randn(1, *input_shape)
                
                # Forward pass to get output shape
                model.eval()
                with torch.no_grad():
                    output = model(dummy_input)
                    if isinstance(output, torch.Tensor):
                        output_shape = output.shape[1:]  # Remove batch dimension
                        run.log({"model/output_shape": str(output_shape)})
                
            except Exception as e:
                logger.warning(f"Failed to get model output shape: {e}")
        
        logger.info(f"Logged model summary: {trainable_params:,} trainable parameters")
        
    except ImportError:
        logger.error("PyTorch not available for model summary")
    except Exception as e:
        logger.error(f"Failed to log model summary: {e}")

def log_optimizer_state(optimizer: Any) -> None:
    """Log optimizer state"""
    from ..sdk.tracklab_init import get_current_run
    
    run = get_current_run()
    if not run:
        return
    
    try:
        import torch.optim as optim
        
        if not isinstance(optimizer, optim.Optimizer):
            logger.warning("Optimizer is not a PyTorch optimizer")
            return
        
        # Get optimizer info
        optimizer_info = {
            "optimizer/class": optimizer.__class__.__name__,
            "optimizer/param_groups": len(optimizer.param_groups),
        }
        
        # Log learning rates
        for i, group in enumerate(optimizer.param_groups):
            if 'lr' in group:
                optimizer_info[f"optimizer/lr_group_{i}"] = group['lr']
        
        run.log(optimizer_info)
        
    except ImportError:
        logger.error("PyTorch not available for optimizer logging")
    except Exception as e:
        logger.error(f"Failed to log optimizer state: {e}")

def create_lr_scheduler_callback(scheduler: Any) -> callable:
    """Create callback for learning rate scheduler"""
    
    def lr_callback():
        """Callback to log learning rate"""
        from ..sdk.tracklab_init import get_current_run
        
        run = get_current_run()
        if not run:
            return
        
        try:
            # Get current learning rate
            current_lr = scheduler.get_last_lr()[0]
            run.log({"optimizer/learning_rate": current_lr})
            
        except Exception as e:
            logger.error(f"Failed to log learning rate: {e}")
    
    return lr_callback