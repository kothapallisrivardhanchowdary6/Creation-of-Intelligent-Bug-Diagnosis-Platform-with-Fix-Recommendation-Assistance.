"""SQLAlchemy models for bug reports and analysis results."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from database.connection import Base

class BugReport(Base):
    __tablename__ = "bug_reports"

    id = Column(String(32), primary_key=True, default=lambda: f"BUG-{uuid.uuid4().hex[:12].upper()}")
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    error_logs = Column(Text, nullable=True)
    environment = Column(String(500), nullable=True)
    files = Column(JSON, nullable=True)
    status = Column(String(20), default="submitted")  # submitted, analyzing, analyzed, error
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex[:16])
    bug_id = Column(String(32), nullable=False, index=True)
    triage = Column(JSON, nullable=True)
    log_analysis = Column(JSON, nullable=True)
    root_cause = Column(JSON, nullable=True)
    duplicate_detection = Column(JSON, nullable=True)
    remediation = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class HistoricalDefect(Base):
    __tablename__ = "historical_defects"

    id = Column(String(32), primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    project = Column(String(100), nullable=False)
    component = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=True)
    resolution = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
