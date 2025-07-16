"""Project data models for TrackLab UI."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class Project(BaseModel):
    """Project model."""
    id: str
    name: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    run_count: int = 0
    
    class Config:
        schema_extra = {
            "example": {
                "id": "my-project",
                "name": "My Project",
                "description": "ML experiments for my project",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-02T00:00:00",
                "run_count": 42
            }
        }