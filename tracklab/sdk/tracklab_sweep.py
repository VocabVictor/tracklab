"""
TrackLab sweep functionality - hyperparameter optimization
"""

import json
import random
import uuid
from typing import Any, Callable, Dict, List, Optional, Union

from .tracklab_init import init
from .tracklab_settings import get_settings
from ..errors import TrackLabError
from ..util.logging import get_logger

logger = get_logger(__name__)

class SweepConfig:
    """Configuration for hyperparameter sweeps"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.method = config.get("method", "grid")
        self.metric = config.get("metric", {})
        self.parameters = config.get("parameters", {})
        self.early_terminate = config.get("early_terminate", {})
        
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate sweep configuration"""
        if not isinstance(self.parameters, dict):
            raise TrackLabError("Sweep parameters must be a dictionary")
        
        if self.method not in ["grid", "random", "bayes"]:
            raise TrackLabError(f"Invalid sweep method: {self.method}")
        
        if self.metric and not isinstance(self.metric, dict):
            raise TrackLabError("Sweep metric must be a dictionary")

class SweepAgent:
    """Agent for running sweep experiments"""
    
    def __init__(self, sweep_id: str, project: Optional[str] = None):
        self.sweep_id = sweep_id
        self.project = project
        self.config = None
        self.runs_completed = 0
        self.max_runs = None
        
        # Load sweep configuration
        self._load_sweep_config()
    
    def _load_sweep_config(self) -> None:
        """Load sweep configuration from storage"""
        # In a real implementation, this would load from backend
        # For now, we'll simulate it
        logger.info(f"Loading sweep config for {self.sweep_id}")
        
        # This would be loaded from backend in real implementation
        self.config = SweepConfig({
            "method": "random",
            "metric": {"name": "loss", "goal": "minimize"},
            "parameters": {
                "learning_rate": {"values": [0.01, 0.001, 0.0001]},
                "batch_size": {"values": [16, 32, 64]},
                "epochs": {"min": 1, "max": 100}
            }
        })
    
    def get_next_run_config(self) -> Optional[Dict[str, Any]]:
        """Get configuration for next run"""
        if not self.config:
            return None
        
        if self.max_runs and self.runs_completed >= self.max_runs:
            return None
        
        # Generate configuration based on method
        if self.config.method == "grid":
            return self._generate_grid_config()
        elif self.config.method == "random":
            return self._generate_random_config()
        elif self.config.method == "bayes":
            return self._generate_bayes_config()
        else:
            raise TrackLabError(f"Unknown sweep method: {self.config.method}")
    
    def _generate_grid_config(self) -> Dict[str, Any]:
        """Generate grid search configuration"""
        # Simple grid search implementation
        config = {}
        
        for param_name, param_config in self.config.parameters.items():
            if "values" in param_config:
                # Cycle through values
                values = param_config["values"]
                config[param_name] = values[self.runs_completed % len(values)]
            elif "min" in param_config and "max" in param_config:
                # For continuous parameters, use linear spacing
                min_val = param_config["min"]
                max_val = param_config["max"]
                steps = param_config.get("steps", 10)
                step_size = (max_val - min_val) / steps
                config[param_name] = min_val + (self.runs_completed % steps) * step_size
        
        return config
    
    def _generate_random_config(self) -> Dict[str, Any]:
        """Generate random search configuration"""
        config = {}
        
        for param_name, param_config in self.config.parameters.items():
            if "values" in param_config:
                # Random choice from values
                config[param_name] = random.choice(param_config["values"])
            elif "min" in param_config and "max" in param_config:
                # Random value in range
                min_val = param_config["min"]
                max_val = param_config["max"]
                if isinstance(min_val, int) and isinstance(max_val, int):
                    config[param_name] = random.randint(min_val, max_val)
                else:
                    config[param_name] = random.uniform(min_val, max_val)
            elif "mu" in param_config and "sigma" in param_config:
                # Normal distribution
                config[param_name] = random.normalvariate(
                    param_config["mu"],
                    param_config["sigma"]
                )
        
        return config
    
    def _generate_bayes_config(self) -> Dict[str, Any]:
        """Generate Bayesian optimization configuration"""
        # Placeholder for Bayesian optimization
        # In a real implementation, this would use a library like Optuna
        logger.warning("Bayesian optimization not fully implemented, falling back to random")
        return self._generate_random_config()
    
    def run_experiment(self, function: Callable, config: Dict[str, Any]) -> None:
        """Run a single experiment"""
        # Initialize run with sweep configuration
        run = init(
            project=self.project,
            config=config,
            group=f"sweep-{self.sweep_id}",
            job_type="sweep"
        )
        
        # Add sweep metadata
        run.config.update({
            "_sweep_id": self.sweep_id,
            "_sweep_run": self.runs_completed
        })
        
        try:
            # Run the function
            function()
            
            # Mark run as completed
            run.finish(exit_code=0)
            
        except Exception as e:
            logger.error(f"Sweep run failed: {e}")
            run.finish(exit_code=1)
            raise
        
        finally:
            self.runs_completed += 1

def sweep(
    sweep_config: Dict[str, Any],
    project: Optional[str] = None,
    entity: Optional[str] = None
) -> str:
    """
    Create a hyperparameter sweep
    
    Args:
        sweep_config: Sweep configuration dictionary
        project: Project name
        entity: Entity name
        
    Returns:
        str: Sweep ID
    """
    
    # Validate sweep configuration
    config = SweepConfig(sweep_config)
    
    # Generate sweep ID
    sweep_id = str(uuid.uuid4())
    
    # Store sweep configuration
    # In a real implementation, this would be stored in backend
    settings = get_settings()
    sweep_dir = settings.tracklab_dir + "/sweeps"
    
    import os
    os.makedirs(sweep_dir, exist_ok=True)
    
    sweep_file = os.path.join(sweep_dir, f"{sweep_id}.json")
    with open(sweep_file, 'w') as f:
        json.dump({
            "id": sweep_id,
            "config": sweep_config,
            "project": project,
            "entity": entity,
            "created_at": str(uuid.uuid4()),  # Placeholder timestamp
            "status": "created"
        }, f, indent=2)
    
    logger.info(f"Created sweep {sweep_id} in project {project}")
    
    return sweep_id

def agent(
    sweep_id: str,
    function: Optional[Callable] = None,
    entity: Optional[str] = None,
    project: Optional[str] = None,
    count: Optional[int] = None
) -> None:
    """
    Run a sweep agent
    
    Args:
        sweep_id: Sweep ID to run
        function: Function to run for each configuration
        entity: Entity name
        project: Project name
        count: Maximum number of runs
    """
    
    if not function:
        raise TrackLabError("Function is required for sweep agent")
    
    # Create sweep agent
    agent = SweepAgent(sweep_id, project)
    agent.max_runs = count
    
    logger.info(f"Starting sweep agent for {sweep_id}")
    
    # Run sweep
    try:
        while True:
            # Get next configuration
            config = agent.get_next_run_config()
            if config is None:
                logger.info("No more configurations to run")
                break
            
            logger.info(f"Running sweep experiment {agent.runs_completed + 1}")
            logger.debug(f"Configuration: {config}")
            
            # Run experiment
            agent.run_experiment(function, config)
            
            # Check if we've reached the limit
            if count and agent.runs_completed >= count:
                logger.info(f"Reached maximum runs ({count})")
                break
    
    except KeyboardInterrupt:
        logger.info("Sweep agent interrupted")
    except Exception as e:
        logger.error(f"Sweep agent failed: {e}")
        raise
    
    logger.info(f"Sweep agent completed {agent.runs_completed} runs")

def get_sweep_config(sweep_id: str) -> Dict[str, Any]:
    """Get sweep configuration by ID"""
    settings = get_settings()
    sweep_file = os.path.join(settings.tracklab_dir, "sweeps", f"{sweep_id}.json")
    
    try:
        with open(sweep_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise TrackLabError(f"Sweep {sweep_id} not found")
    except Exception as e:
        raise TrackLabError(f"Failed to load sweep {sweep_id}: {e}")

def list_sweeps(project: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all sweeps"""
    settings = get_settings()
    sweep_dir = os.path.join(settings.tracklab_dir, "sweeps")
    
    if not os.path.exists(sweep_dir):
        return []
    
    sweeps = []
    for filename in os.listdir(sweep_dir):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(sweep_dir, filename), 'r') as f:
                    sweep = json.load(f)
                    if project is None or sweep.get("project") == project:
                        sweeps.append(sweep)
            except Exception as e:
                logger.warning(f"Failed to load sweep {filename}: {e}")
    
    return sweeps