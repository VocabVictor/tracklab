"""Experimental workflow functionality."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    name: str
    action: str
    config: Dict[str, Any]
    

class Workflow:
    """Experimental workflow management.
    
    This is a beta feature for managing complex experiment workflows.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.steps: List[WorkflowStep] = []
        self._executed_steps = 0
        
    def add_step(self, name: str, action: str, config: Optional[Dict[str, Any]] = None):
        """Add a step to the workflow."""
        step = WorkflowStep(
            name=name,
            action=action,
            config=config or {}
        )
        self.steps.append(step)
        
    def execute(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute the workflow."""
        context = context or {}
        results = []
        
        for step in self.steps:
            try:
                # Basic step execution
                result = {
                    "step": step.name,
                    "action": step.action,
                    "status": "completed",
                    "config": step.config
                }
                results.append(result)
                self._executed_steps += 1
            except Exception as e:
                result = {
                    "step": step.name,
                    "action": step.action,
                    "status": "failed",
                    "error": str(e)
                }
                results.append(result)
                break
                
        return {
            "workflow": self.name,
            "total_steps": len(self.steps),
            "executed_steps": self._executed_steps,
            "results": results
        }
        
    def reset(self):
        """Reset workflow execution state."""
        self._executed_steps = 0
        
    def __repr__(self) -> str:
        return f"Workflow('{self.name}', steps={len(self.steps)})"