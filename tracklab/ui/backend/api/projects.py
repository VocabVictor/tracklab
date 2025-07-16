"""Project API routes for TrackLab UI."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from ..services.datastore_service import DatastoreService

router = APIRouter(prefix="/api/projects", tags=["projects"])


def get_datastore_service() -> DatastoreService:
    """Dependency to get datastore service instance."""
    return DatastoreService()


@router.get("")
async def get_projects(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get all projects.
    
    Returns:
        List of project metadata
    """
    try:
        projects = await datastore.get_projects()
        return {"success": True, "data": projects}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get a specific project.
    
    Args:
        project_id: Project ID
        
    Returns:
        Project metadata
    """
    try:
        projects = await datastore.get_projects()
        project = next((p for p in projects if p["id"] == project_id), None)
        
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
            
        return {"success": True, "data": project}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{project_id}/runs")
async def get_project_runs(
    project_id: str,
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get runs for a specific project.
    
    Args:
        project_id: Project ID
        
    Returns:
        List of runs in the project
    """
    try:
        runs = await datastore.get_runs(project=project_id)
        return {"success": True, "data": runs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))