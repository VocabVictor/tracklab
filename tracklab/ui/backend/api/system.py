"""System API routes for TrackLab UI."""

from fastapi import APIRouter, Depends, HTTPException

from ..services.datastore_service import DatastoreService

router = APIRouter(prefix="/api/system", tags=["system"])


def get_datastore_service() -> DatastoreService:
    """Dependency to get datastore service instance."""
    return DatastoreService()


@router.get("/info")
async def get_system_info(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get system information.
    
    Returns:
        System information including platform, resources, etc.
    """
    try:
        info = await datastore.get_system_info()
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_system_metrics(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get current system metrics.
    
    Returns:
        Recent system metrics (CPU, memory, disk, GPU)
    """
    try:
        metrics = await datastore.get_system_metrics()
        return {"success": True, "data": metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_system_status():
    """Get system status.
    
    Returns:
        Overall system health status
    """
    try:
        # Check if datastore is accessible
        datastore = DatastoreService()
        
        # Try to list runs as a health check
        runs = await datastore.get_runs()
        
        status = {
            "status": "healthy",
            "datastore": "connected",
            "run_count": len(runs),
            "version": "0.0.1"
        }
        
        return {"success": True, "data": status}
    except Exception as e:
        return {
            "success": False,
            "data": {
                "status": "unhealthy",
                "error": str(e)
            }
        }