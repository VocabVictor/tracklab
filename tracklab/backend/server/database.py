"""
Database models for TrackLab backend
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine

from ...util.logging import get_logger

logger = get_logger(__name__)

Base = declarative_base()

class Project(Base):
    """Project model"""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    entity = Column(String(255), nullable=False, default="default")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    runs = relationship("Run", back_populates="project", cascade="all, delete-orphan")
    sweeps = relationship("Sweep", back_populates="project", cascade="all, delete-orphan")

class Run(Base):
    """Run model"""
    __tablename__ = "runs"
    
    id = Column(String(255), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    notes = Column(Text)
    tags = Column(JSON)
    group_name = Column(String(255))
    job_type = Column(String(255))
    state = Column(String(50), default="running")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    exit_code = Column(Integer)
    config = Column(JSON)
    summary = Column(JSON)
    system_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="runs")
    metrics = relationship("Metric", back_populates="run", cascade="all, delete-orphan")
    files = relationship("File", back_populates="run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="run", cascade="all, delete-orphan")

class Metric(Base):
    """Metric model"""
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(255), ForeignKey("runs.id"), nullable=False)
    key = Column(String(255), nullable=False)
    value = Column(Float)
    string_value = Column(String(1000))
    json_value = Column(JSON)
    step = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="metrics")

class File(Base):
    """File model"""
    __tablename__ = "files"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(255), ForeignKey("runs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    path = Column(String(1000), nullable=False)
    size = Column(Integer)
    mimetype = Column(String(255))
    policy = Column(String(50), default="live")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="files")

class Artifact(Base):
    """Artifact model"""
    __tablename__ = "artifacts"
    
    id = Column(Integer, primary_key=True)
    run_id = Column(String(255), ForeignKey("runs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(String(100), nullable=False)
    description = Column(Text)
    metadata = Column(JSON)
    size = Column(Integer)
    digest = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    run = relationship("Run", back_populates="artifacts")

class Sweep(Base):
    """Sweep model"""
    __tablename__ = "sweeps"
    
    id = Column(String(255), primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255))
    method = Column(String(50), nullable=False)
    config = Column(JSON, nullable=False)
    metric = Column(JSON)
    state = Column(String(50), default="running")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    project = relationship("Project", back_populates="sweeps")

class DatabaseManager:
    """Database manager for TrackLab"""
    
    def __init__(self, database_url: str = "sqlite:///tracklab.db"):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
    def initialize(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False} if "sqlite" in self.database_url else {}
            )
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            
            # Create session factory
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            logger.info(f"Database initialized: {self.database_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_session(self):
        """Get database session"""
        if self.SessionLocal is None:
            raise RuntimeError("Database not initialized")
        
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def get_database_manager() -> DatabaseManager:
    """Get global database manager"""
    global _db_manager
    if _db_manager is None:
        from ...sdk.tracklab_settings import get_settings
        settings = get_settings()
        _db_manager = DatabaseManager(settings.database_url)
        _db_manager.initialize()
    return _db_manager

def get_db():
    """Get database session (for FastAPI dependency injection)"""
    db_manager = get_database_manager()
    db = db_manager.get_session()
    try:
        yield db
    finally:
        db.close()

# Database operations
class DatabaseOperations:
    """Database operations for TrackLab"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def create_project(self, name: str, entity: str = "default", description: str = None) -> Project:
        """Create a new project"""
        project = Project(name=name, entity=entity, description=description)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project
    
    def get_project(self, name: str, entity: str = "default") -> Optional[Project]:
        """Get project by name and entity"""
        return self.db.query(Project).filter(
            Project.name == name,
            Project.entity == entity
        ).first()
    
    def get_or_create_project(self, name: str, entity: str = "default") -> Project:
        """Get or create project"""
        project = self.get_project(name, entity)
        if not project:
            project = self.create_project(name, entity)
        return project
    
    def create_run(self, run_data: Dict[str, Any]) -> Run:
        """Create a new run"""
        # Ensure project exists
        project = self.get_or_create_project(
            run_data.get("project", "default"),
            run_data.get("entity", "default")
        )
        
        run = Run(
            id=run_data["id"],
            project_id=project.id,
            name=run_data.get("name", f"run-{run_data['id'][:8]}"),
            display_name=run_data.get("display_name"),
            notes=run_data.get("notes"),
            tags=run_data.get("tags"),
            group_name=run_data.get("group"),
            job_type=run_data.get("job_type"),
            state=run_data.get("state", "running"),
            start_time=run_data.get("start_time", datetime.utcnow()),
            config=run_data.get("config"),
            summary=run_data.get("summary")
        )
        
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run
    
    def get_run(self, run_id: str) -> Optional[Run]:
        """Get run by ID"""
        return self.db.query(Run).filter(Run.id == run_id).first()
    
    def update_run(self, run_id: str, updates: Dict[str, Any]) -> Optional[Run]:
        """Update run"""
        run = self.get_run(run_id)
        if run:
            for key, value in updates.items():
                if hasattr(run, key):
                    setattr(run, key, value)
            self.db.commit()
            self.db.refresh(run)
        return run
    
    def log_metric(self, run_id: str, key: str, value: Any, step: int = 0) -> Metric:
        """Log a metric"""
        metric = Metric(
            run_id=run_id,
            key=key,
            step=step,
            timestamp=datetime.utcnow()
        )
        
        # Handle different value types
        if isinstance(value, (int, float)):
            metric.value = float(value)
        elif isinstance(value, str):
            metric.string_value = value
        else:
            metric.json_value = value
        
        self.db.add(metric)
        self.db.commit()
        self.db.refresh(metric)
        return metric
    
    def get_run_metrics(self, run_id: str) -> List[Metric]:
        """Get all metrics for a run"""
        return self.db.query(Metric).filter(Metric.run_id == run_id).all()
    
    def log_file(self, run_id: str, file_data: Dict[str, Any]) -> File:
        """Log a file"""
        file = File(
            run_id=run_id,
            name=file_data["name"],
            path=file_data["path"],
            size=file_data.get("size"),
            mimetype=file_data.get("mimetype"),
            policy=file_data.get("policy", "live")
        )
        
        self.db.add(file)
        self.db.commit()
        self.db.refresh(file)
        return file
    
    def get_run_files(self, run_id: str) -> List[File]:
        """Get all files for a run"""
        return self.db.query(File).filter(File.run_id == run_id).all()
    
    def list_projects(self) -> List[Project]:
        """List all projects"""
        return self.db.query(Project).all()
    
    def list_runs(self, project_name: str = None, entity: str = "default") -> List[Run]:
        """List runs"""
        query = self.db.query(Run)
        
        if project_name:
            project = self.get_project(project_name, entity)
            if project:
                query = query.filter(Run.project_id == project.id)
        
        return query.order_by(Run.created_at.desc()).all()
    
    def delete_run(self, run_id: str) -> bool:
        """Delete a run"""
        run = self.get_run(run_id)
        if run:
            self.db.delete(run)
            self.db.commit()
            return True
        return False