"""Research API routes for TrackLab UI - using research/experiment/run hierarchy."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException

from ..services.datastore_service import DatastoreService

router = APIRouter(prefix="/api/research", tags=["research"])


def get_datastore_service() -> DatastoreService:
    """Dependency to get datastore service instance."""
    return DatastoreService()


@router.get("")
async def get_research(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get all research projects.
    
    Returns:
        List of research metadata
    """
    try:
        research = await datastore.get_research()
        return {"success": True, "data": research}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{research_id}")
async def get_research_by_id(
    research_id: str,
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get a specific research project.
    
    Args:
        research_id: Research ID
        
    Returns:
        Research metadata
    """
    try:
        research_list = await datastore.get_research()
        research = next((r for r in research_list if r["id"] == research_id), None)
        
        if not research:
            raise HTTPException(status_code=404, detail="Research project not found")
            
        return {"success": True, "data": research}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{research_id}/experiments")
async def get_research_experiments(
    research_id: str,
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get experiments for a specific research project.
    
    Args:
        research_id: Research ID
        
    Returns:
        List of experiments in the research project
    """
    try:
        experiments = await datastore.get_experiments(research=research_id)
        return {"success": True, "data": experiments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{research_id}/experiments/{experiment_id}/runs")
async def get_experiment_runs(
    research_id: str,
    experiment_id: str,
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get runs for a specific experiment.
    
    Args:
        research_id: Research ID
        experiment_id: Experiment ID
        
    Returns:
        List of runs in the experiment
    """
    try:
        runs = await datastore.get_runs(research=research_id, experiment=experiment_id)
        return {"success": True, "data": runs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))