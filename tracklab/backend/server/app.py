"""
FastAPI application for TrackLab backend
"""

from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional
import os
from pathlib import Path

from .database import get_db, DatabaseOperations, Project, Run, Metric, File
from ...util.logging import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TrackLab API",
    description="Local experiment tracking API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# API Routes

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TrackLab API", "version": "0.1.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "tracklab-api"}

# Project endpoints

@app.get("/api/projects")
async def list_projects(db: Session = Depends(get_db)):
    """List all projects"""
    db_ops = DatabaseOperations(db)
    projects = db_ops.list_projects()
    
    return [
        {
            "id": project.id,
            "name": project.name,
            "entity": project.entity,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
        for project in projects
    ]

@app.post("/api/projects")
async def create_project(
    project_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new project"""
    db_ops = DatabaseOperations(db)
    
    try:
        project = db_ops.create_project(
            name=project_data["name"],
            entity=project_data.get("entity", "default"),
            description=project_data.get("description")
        )
        
        return {
            "id": project.id,
            "name": project.name,
            "entity": project.entity,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to create project: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/projects/{project_name}")
async def get_project(
    project_name: str,
    entity: str = "default",
    db: Session = Depends(get_db)
):
    """Get project by name"""
    db_ops = DatabaseOperations(db)
    project = db_ops.get_project(project_name, entity)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "id": project.id,
        "name": project.name,
        "entity": project.entity,
        "description": project.description,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat()
    }

# Run endpoints

@app.get("/api/runs")
async def list_runs(
    project: Optional[str] = None,
    entity: str = "default",
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """List runs"""
    db_ops = DatabaseOperations(db)
    runs = db_ops.list_runs(project, entity)
    
    # Apply pagination
    runs = runs[offset:offset + limit]
    
    return [
        {
            "id": run.id,
            "name": run.name,
            "display_name": run.display_name,
            "project": run.project.name,
            "entity": run.project.entity,
            "notes": run.notes,
            "tags": run.tags,
            "group": run.group_name,
            "job_type": run.job_type,
            "state": run.state,
            "start_time": run.start_time.isoformat(),
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "exit_code": run.exit_code,
            "config": run.config,
            "summary": run.summary,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat()
        }
        for run in runs
    ]

@app.post("/api/runs")
async def create_run(
    run_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Create a new run"""
    db_ops = DatabaseOperations(db)
    
    try:
        run = db_ops.create_run(run_data)
        
        return {
            "id": run.id,
            "name": run.name,
            "display_name": run.display_name,
            "project": run.project.name,
            "entity": run.project.entity,
            "state": run.state,
            "created_at": run.created_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to create run: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/runs/{run_id}")
async def get_run(run_id: str, db: Session = Depends(get_db)):
    """Get run by ID"""
    db_ops = DatabaseOperations(db)
    run = db_ops.get_run(run_id)
    
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "id": run.id,
        "name": run.name,
        "display_name": run.display_name,
        "project": run.project.name,
        "entity": run.project.entity,
        "notes": run.notes,
        "tags": run.tags,
        "group": run.group_name,
        "job_type": run.job_type,
        "state": run.state,
        "start_time": run.start_time.isoformat(),
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "exit_code": run.exit_code,
        "config": run.config,
        "summary": run.summary,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat()
    }

@app.put("/api/runs/{run_id}")
async def update_run(
    run_id: str,
    updates: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update run"""
    db_ops = DatabaseOperations(db)
    
    try:
        run = db_ops.update_run(run_id, updates)
        
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        
        return {
            "id": run.id,
            "name": run.name,
            "state": run.state,
            "updated_at": run.updated_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to update run: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/runs/{run_id}")
async def delete_run(run_id: str, db: Session = Depends(get_db)):
    """Delete run"""
    db_ops = DatabaseOperations(db)
    
    success = db_ops.delete_run(run_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {"message": "Run deleted successfully"}

# Metrics endpoints

@app.get("/api/runs/{run_id}/metrics")
async def get_run_metrics(run_id: str, db: Session = Depends(get_db)):
    """Get metrics for a run"""
    db_ops = DatabaseOperations(db)
    
    # Check if run exists
    run = db_ops.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    metrics = db_ops.get_run_metrics(run_id)
    
    return [
        {
            "id": metric.id,
            "key": metric.key,
            "value": metric.value,
            "string_value": metric.string_value,
            "json_value": metric.json_value,
            "step": metric.step,
            "timestamp": metric.timestamp.isoformat()
        }
        for metric in metrics
    ]

@app.post("/api/runs/{run_id}/metrics")
async def log_metrics(
    run_id: str,
    metrics_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Log metrics for a run"""
    db_ops = DatabaseOperations(db)
    
    # Check if run exists
    run = db_ops.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        step = metrics_data.get("step", 0)
        logged_metrics = []
        
        for key, value in metrics_data.get("data", {}).items():
            metric = db_ops.log_metric(run_id, key, value, step)
            logged_metrics.append({
                "id": metric.id,
                "key": metric.key,
                "value": metric.value,
                "string_value": metric.string_value,
                "json_value": metric.json_value,
                "step": metric.step,
                "timestamp": metric.timestamp.isoformat()
            })
        
        return {"metrics": logged_metrics}
    
    except Exception as e:
        logger.error(f"Failed to log metrics: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# Files endpoints

@app.get("/api/runs/{run_id}/files")
async def get_run_files(run_id: str, db: Session = Depends(get_db)):
    """Get files for a run"""
    db_ops = DatabaseOperations(db)
    
    # Check if run exists
    run = db_ops.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    files = db_ops.get_run_files(run_id)
    
    return [
        {
            "id": file.id,
            "name": file.name,
            "path": file.path,
            "size": file.size,
            "mimetype": file.mimetype,
            "policy": file.policy,
            "uploaded_at": file.uploaded_at.isoformat()
        }
        for file in files
    ]

@app.post("/api/runs/{run_id}/files")
async def upload_file(
    run_id: str,
    file_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Upload file for a run"""
    db_ops = DatabaseOperations(db)
    
    # Check if run exists
    run = db_ops.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    
    try:
        file = db_ops.log_file(run_id, file_data)
        
        return {
            "id": file.id,
            "name": file.name,
            "path": file.path,
            "size": file.size,
            "mimetype": file.mimetype,
            "policy": file.policy,
            "uploaded_at": file.uploaded_at.isoformat()
        }
    
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/files/{file_id}")
async def download_file(file_id: int, db: Session = Depends(get_db)):
    """Download file by ID"""
    db_ops = DatabaseOperations(db)
    
    file = db.query(File).filter(File.id == file_id).first()
    
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(file.path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=file.name,
        media_type=file.mimetype
    )

# Dashboard endpoints

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve dashboard HTML"""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        # Return a basic HTML page if frontend not built
        return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TrackLab Dashboard</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 40px;
                    background-color: #f5f5f5;
                }
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 {
                    color: #333;
                    text-align: center;
                }
                .info {
                    background-color: #e3f2fd;
                    padding: 20px;
                    border-radius: 4px;
                    margin: 20px 0;
                }
                .links {
                    text-align: center;
                    margin-top: 30px;
                }
                .links a {
                    display: inline-block;
                    margin: 0 10px;
                    padding: 10px 20px;
                    background-color: #1976d2;
                    color: white;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .links a:hover {
                    background-color: #1565c0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 TrackLab Dashboard</h1>
                <div class="info">
                    <h3>Welcome to TrackLab!</h3>
                    <p>Your local experiment tracking system is running successfully.</p>
                    <p>The frontend is not yet built. You can access the API directly or build the frontend using:</p>
                    <code>make frontend</code>
                </div>
                <div class="links">
                    <a href="/api/docs">API Documentation</a>
                    <a href="/api/projects">View Projects</a>
                    <a href="/api/runs">View Runs</a>
                </div>
            </div>
        </body>
        </html>
        """)

# Startup and shutdown events

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        from .database import get_database_manager
        db_manager = get_database_manager()
        logger.info("TrackLab API started successfully")
    except Exception as e:
        logger.error(f"Failed to start TrackLab API: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        from .database import _db_manager
        if _db_manager:
            _db_manager.close()
        logger.info("TrackLab API shut down successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Exception handlers

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)