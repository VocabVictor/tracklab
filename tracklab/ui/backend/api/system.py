"""System API routes for TrackLab UI."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

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
    node_id: Optional[str] = None,
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get current system metrics.
    
    Args:
        node_id: Optional node ID filter for cluster environments
    
    Returns:
        Recent system metrics (CPU, memory, disk, accelerators)
    """
    try:
        metrics = await datastore.get_system_metrics(node_id)
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


# Cluster-specific endpoints
@router.get("/cluster/info")
async def get_cluster_info(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get cluster information.
    
    Returns:
        Cluster nodes and resource information
    """
    try:
        cluster_info = await datastore.get_cluster_info()
        return {"success": True, "data": cluster_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cluster/metrics")
async def get_cluster_metrics(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get cluster-wide metrics.
    
    Returns:
        Metrics for all nodes in the cluster
    """
    try:
        cluster_metrics = await datastore.get_cluster_metrics()
        return {"success": True, "data": cluster_metrics}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hardware/accelerators")
async def get_accelerator_info(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get detailed accelerator information.
    
    Returns:
        Detailed information about GPU/NPU/TPU devices
    """
    try:
        accelerator_info = await datastore.get_accelerator_info()
        return {"success": True, "data": accelerator_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hardware/cpu")
async def get_cpu_info(
    datastore: DatastoreService = Depends(get_datastore_service)
):
    """Get detailed CPU information.
    
    Returns:
        Per-core CPU information and statistics
    """
    try:
        cpu_info = await datastore.get_cpu_info()
        return {"success": True, "data": cpu_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))