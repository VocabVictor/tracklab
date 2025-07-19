"""Project related API methods."""

import logging
from typing import Any, Dict, List, Optional

from tracklab.apis.normalize import normalize_exceptions

logger = logging.getLogger(__name__)


class ProjectsMixin:
    """Project related API methods."""
    
    @normalize_exceptions
    def list_projects(self, entity: Optional[str] = None) -> List[Dict[str, str]]:
        """List projects in TrackLab scoped by entity.
        
        For local TrackLab, returns empty list.
        """
        return []
        
    @normalize_exceptions
    def project(self, project: str, entity: Optional[str] = None) -> Dict[str, Any]:
        """Retrieve project information.
        
        For local TrackLab, returns mock data.
        """
        return {
            "id": f"local-project-{project}",
            "name": project,
            "entity": {"name": entity or self.default_entity},
            "entityName": entity or self.default_entity,
            "isBenchmark": False,
            "state": "available",
            "access": "private",
            "views": {},
        }
        
    def get_project(self) -> str:
        """Get current project name."""
        if hasattr(self, 'default_settings') and isinstance(self.default_settings, dict):
            project = self.default_settings.get("project")
        else:
            project = None
            
        if not project and hasattr(self, 'settings'):
            project = self.settings("project")
            
        return project or "uncategorized"
        
    @normalize_exceptions
    def upsert_project(
        self,
        project: str,
        entity: Optional[str] = None,
        description: Optional[str] = None,
        display_name: Optional[str] = None,
        framework: Optional[str] = None,
        access: Optional[str] = None,
    ) -> str:
        """Create or update a project.
        
        For local TrackLab, just formats and returns the project name.
        """
        if hasattr(self, 'format_project'):
            formatted_project = self.format_project(project)
        else:
            import re
            formatted_project = re.sub(r"\W+", "-", project.lower()).strip("-_")
            
        logger.info(f"Local project created/updated: {formatted_project}")
        return formatted_project
        
    @normalize_exceptions
    def get_project_run_queues(self, entity: str, project: str) -> List[Dict[str, str]]:
        """Get run queues for a project.
        
        For local TrackLab, returns empty list.
        """
        return []