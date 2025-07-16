"""Run API routes for TrackLab UI."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from ..services.datastore_service import DatastoreService

router = APIRouter(prefix="/api/runs", tags=["runs"])


def get_datastore_service() -> DatastoreService:
    """Dependency to get datastore service instance."""
    return DatastoreService()


@router.get("")
async def get_runs(
    project: Optional[str] = Query(None, description="Filter by project"),
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get all runs, optionally filtered by project.
    
    Args:
        project: Optional project filter
        
    Returns:
        List of run metadata
    """
    try:
        runs = await datastore.get_runs(project=project)
        return {"success": True, "data": runs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}")
async def get_run(
    run_id: str,
    project: str = Query("default", description="Project name"),
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get detailed run data.
    
    Args:
        run_id: Run ID
        project: Project name
        
    Returns:
        Complete run data
    """
    try:
        run_data = await datastore.get_run(run_id, project)
        return {"success": True, "data": run_data}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/metrics")
async def get_run_metrics(
    run_id: str,
    project: str = Query("default", description="Project name"),
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get metrics for a specific run.
    
    Args:
        run_id: Run ID
        project: Project name
        
    Returns:
        Metrics data
    """
    try:
        metrics = await datastore.get_run_metrics(run_id, project)
        return {"success": True, "data": metrics}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{run_id}")
async def delete_run(
    run_id: str,
    project: str = Query("default", description="Project name")
):
    """Delete a run (not implemented for LevelDB backend).
    
    Args:
        run_id: Run ID
        project: Project name
    """
    # For LevelDB backend, we don't support deletion
    # Could be implemented by marking runs as deleted in metadata
    raise HTTPException(
        status_code=501, 
        detail="Run deletion not supported in LevelDB backend"
    )


@router.patch("/{run_id}")
async def update_run(
    run_id: str,
    project: str = Query("default", description="Project name"),
    update_data: dict = {}
):
    """Update run metadata (not implemented for LevelDB backend).
    
    Args:
        run_id: Run ID
        project: Project name
        update_data: Data to update
    """
    # For LevelDB backend, we don't support updates
    # The SDK is responsible for all writes
    raise HTTPException(
        status_code=501,
        detail="Run updates not supported in LevelDB backend. Use TrackLab SDK for modifications."
    )