# backend/db/models.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship to the SwingJobs table
    swings = relationship("SwingJob", back_populates="owner")


class SwingJob(Base):
    __tablename__ = "swing_jobs"

    # UUIDs are often better for job IDs to prevent users from guessing sequential numbers,
    # but we'll use string here to match your API documentation's job_id format.
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    status = Column(String, default="pending") # pending, processing, complete, failed
    error_message = Column(String, nullable=True)
    
    # Store the paths to the uploaded videos in S3/Local Storage
    video_path_dtl = Column(String, nullable=True)
    video_path_fo = Column(String, nullable=True)
    
    # THE BEST PART: Dump the entire AI JSON output directly here!
    analysis_results = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship back to the User
    owner = relationship("User", back_populates="swings")