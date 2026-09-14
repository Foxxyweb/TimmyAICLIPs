"""
AI Video Clipper — SQLAlchemy Models
======================================
Model database untuk Job (pekerjaan processing) dan Clip (hasil klip).
"""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, Enum, inspect
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from database import Base


def generate_uuid():
    return str(uuid.uuid4())


# ── Enums ────────────────────────────────────────────────────
class JobStatus(str, enum.Enum):
    PENDING     = "pending"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    ANALYZING   = "analyzing"
    RENDERING   = "rendering"
    COMPLETED   = "completed"
    FAILED      = "failed"
    CANCELLED   = "cancelled"


# ── Job Model ────────────────────────────────────────────────
class Job(Base):
    """Represents a video processing job."""
    __tablename__ = "jobs"

    id             = Column(String, primary_key=True, default=generate_uuid)
    youtube_url    = Column(String, nullable=False)
    video_title    = Column(String, nullable=True)
    video_duration = Column(Integer, nullable=True)    # seconds
    thumbnail_url  = Column(String, nullable=True)
    
    status         = Column(
        Enum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False
    )
    progress       = Column(Integer, default=0)        # 0-100 percent
    status_message = Column(String, default="Menunggu antrian...")
    error_message  = Column(Text, nullable=True)
    
    celery_task_id = Column(String, nullable=True)
    
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at   = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    clips = relationship("Clip", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        # Mencegah error MissingGreenlet saat meng-akses relasi clips di Async SQLAlchemy
        state = inspect(self)
        clips_data = []
        if "clips" in state.dict:
            clips_data = [c.to_dict() for c in self.clips] if self.clips else []

        status_val = self.status.value if hasattr(self.status, "value") else str(self.status)

        return {
            "id": self.id,
            "youtube_url": self.youtube_url,
            "video_title": self.video_title,
            "video_duration": self.video_duration,
            "thumbnail_url": self.thumbnail_url,
            "status": status_val,
            "progress": self.progress,
            "status_message": self.status_message,
            "error_message": self.error_message,
            "clips": clips_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ── Clip Model ───────────────────────────────────────────────
class Clip(Base):
    """Represents a single viral clip extracted from a video."""
    __tablename__ = "clips"

    id           = Column(String, primary_key=True, default=generate_uuid)
    job_id       = Column(String, ForeignKey("jobs.id"), nullable=False)
    
    clip_index   = Column(Integer, nullable=False)    # 1, 2, 3, ...
    title        = Column(String, nullable=True)       # AI-generated title
    description  = Column(Text, nullable=True)         # Why it's viral
    
    start_time   = Column(Float, nullable=False)       # seconds
    end_time     = Column(Float, nullable=False)       # seconds
    duration     = Column(Float, nullable=False)       # seconds
    
    viral_score  = Column(Integer, default=0)          # 0-100 AI score
    
    # File paths (relative ke CLIPS_DIR)
    filename     = Column(String, nullable=True)       # final_clip_001.mp4
    file_size    = Column(Integer, nullable=True)      # bytes
    
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="clips")

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "clip_index": self.clip_index,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "viral_score": self.viral_score,
            "filename": self.filename,
            "file_size": self.file_size,
            "video_url": f"/clips/{self.filename}" if self.filename else None,
        }