"""Automation scopes."""

from typing import List, Dict, Any
from enum import Enum


class ScopeType(Enum):
    """Types of automation scopes."""
    PROJECT = "project"
    RUN = "run"
    USER = "user"
    GLOBAL = "global"


class Scope:
    """Defines the scope for automation rules."""
    
    def __init__(self, scope_type: ScopeType, identifiers: List[str]):
        self.scope_type = scope_type
        self.identifiers = identifiers
        
    def matches(self, context: Dict[str, Any]) -> bool:
        """Check if context matches this scope."""
        # Basic implementation
        return True
        
    def __repr__(self) -> str:
        return f"Scope({self.scope_type.value}, {self.identifiers})"