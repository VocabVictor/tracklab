"""
Local interface for TrackLab backend communication
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path

from ...util.logging import get_logger

logger = get_logger(__name__)

class LocalInterface:
    """
    Local interface for TrackLab backend communication
    
    This class provides a local implementation of the backend interface
    that communicates directly with the database without HTTP requests.
    """
    
    def __init__(self):
        self._db_manager = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the local interface"""
        if not self._initialized:
            try:
                from ..server.database import get_database_manager
                self._db_manager = get_database_manager()
                self._initialized = True
                logger.info("Local interface initialized")
            except Exception as e:
                logger.error(f"Failed to initialize local interface: {e}")
                raise
    
    def _get_db_ops(self):
        """Get database operations instance"""
        if not self._initialized:
            self.initialize()
        
        from ..server.database import DatabaseOperations
        db_session = self._db_manager.get_session()
        return DatabaseOperations(db_session), db_session
    
    def create_run(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new run"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                run = db_ops.create_run(run_data)
                
                result = {
                    "id": run.id,
                    "name": run.name,
                    "display_name": run.display_name,
                    "project": run.project.name,
                    "entity": run.project.entity,
                    "state": run.state,
                    "created_at": run.created_at.isoformat()
                }
                
                logger.debug(f"Created run: {run.id}")
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to create run: {e}")
            raise
    
    def get_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get run by ID"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                run = db_ops.get_run(run_id)
                
                if not run:
                    return None
                
                result = {
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
                
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to get run: {e}")
            raise
    
    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update run"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                run = db_ops.update_run(run_id, updates)
                
                if not run:
                    return None
                
                result = {
                    "id": run.id,
                    "name": run.name,
                    "state": run.state,
                    "updated_at": run.updated_at.isoformat()
                }
                
                logger.debug(f"Updated run: {run_id}")
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to update run: {e}")
            raise
    
    def log_metrics(self, run_id: str, metrics: Dict[str, Any], step: int = 0) -> List[Dict[str, Any]]:
        """Log metrics for a run"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                logged_metrics = []
                
                for key, value in metrics.items():
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
                
                logger.debug(f"Logged {len(logged_metrics)} metrics for run: {run_id}")
                return logged_metrics
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to log metrics: {e}")
            raise
    
    def get_run_metrics(self, run_id: str) -> List[Dict[str, Any]]:
        """Get metrics for a run"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                metrics = db_ops.get_run_metrics(run_id)
                
                result = [
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
                
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to get run metrics: {e}")
            raise
    
    def log_file(self, run_id: str, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a file for a run"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                file = db_ops.log_file(run_id, file_data)
                
                result = {
                    "id": file.id,
                    "name": file.name,
                    "path": file.path,
                    "size": file.size,
                    "mimetype": file.mimetype,
                    "policy": file.policy,
                    "uploaded_at": file.uploaded_at.isoformat()
                }
                
                logger.debug(f"Logged file: {file.name} for run: {run_id}")
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to log file: {e}")
            raise
    
    def get_run_files(self, run_id: str) -> List[Dict[str, Any]]:
        """Get files for a run"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                files = db_ops.get_run_files(run_id)
                
                result = [
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
                
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to get run files: {e}")
            raise
    
    def list_runs(self, project_name: str = None, entity: str = "default") -> List[Dict[str, Any]]:
        """List runs"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                runs = db_ops.list_runs(project_name, entity)
                
                result = [
                    {
                        "id": run.id,
                        "name": run.name,
                        "display_name": run.display_name,
                        "project": run.project.name,
                        "entity": run.project.entity,
                        "state": run.state,
                        "start_time": run.start_time.isoformat(),
                        "end_time": run.end_time.isoformat() if run.end_time else None,
                        "created_at": run.created_at.isoformat(),
                        "updated_at": run.updated_at.isoformat()
                    }
                    for run in runs
                ]
                
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to list runs: {e}")
            raise
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List projects"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                projects = db_ops.list_projects()
                
                result = [
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
                
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            raise
    
    def create_project(self, name: str, entity: str = "default", description: str = None) -> Dict[str, Any]:
        """Create a project"""
        try:
            db_ops, db_session = self._get_db_ops()
            
            try:
                project = db_ops.create_project(name, entity, description)
                
                result = {
                    "id": project.id,
                    "name": project.name,
                    "entity": project.entity,
                    "description": project.description,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat()
                }
                
                logger.debug(f"Created project: {name}")
                return result
                
            finally:
                db_session.close()
                
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    def close(self):
        """Close the interface"""
        if self._db_manager:
            self._db_manager.close()
        self._initialized = False

# Global interface instance
_local_interface: Optional[LocalInterface] = None

def get_local_interface() -> LocalInterface:
    """Get global local interface"""
    global _local_interface
    if _local_interface is None:
        _local_interface = LocalInterface()
    return _local_interface