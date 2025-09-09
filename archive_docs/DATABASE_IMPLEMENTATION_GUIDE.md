# Style Guide AI - Database Implementation Guide

## Overview

This document provides a comprehensive, end-to-end implementation guide for integrating a full database system into the Style Guide AI application. The implementation replaces the current file-based storage with a robust SQLAlchemy-based database system.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [SQLAlchemy Models](#sqlalchemy-models)
4. [Data Access Layer](#data-access-layer)
5. [Service Layer Integration](#service-layer-integration)
6. [API Route Modifications](#api-route-modifications)
7. [Migration Scripts](#migration-scripts)
8. [Testing Implementation](#testing-implementation)
9. [Deployment Guide](#deployment-guide)
10. [Performance Optimization](#performance-optimization)

## Prerequisites

### Required Packages
Add to your `requirements.txt`:
```
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
alembic==1.12.1
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9  # For PostgreSQL
```

### Environment Variables
Update your `.env` file:
```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/style_guide_ai
# For development, you can use SQLite:
# DATABASE_URL=sqlite:///style_guide_ai.db

# Migration Configuration
FLASK_APP=app.py
FLASK_ENV=development
```

## Database Setup

### 1. Database Initialization

Create `database/__init__.py`:
```python
"""
Database package initialization
Handles SQLAlchemy setup and database initialization.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import all models to ensure they're registered
    from . import models
    
    return db

def create_tables():
    """Create all tables."""
    db.create_all()

def drop_tables():
    """Drop all tables (use with caution)."""
    db.drop_all()
```

### 2. Database Models

Create `database/models.py`:
```python
"""
SQLAlchemy Models for Style Guide AI
Complete database models matching the schema design.
"""

import json
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import ENUM
from database import db

# Enums for better type safety
class DocumentStatus(Enum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"

class SessionStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"

class AnalysisMode(Enum):
    GRAMMAR = "grammar"
    READABILITY = "readability"
    STYLE = "style"
    COMPREHENSIVE = "comprehensive"

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FeedbackType(Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIALLY_CORRECT = "partially_correct"

class ValidationDecision(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    UNCERTAIN = "uncertain"

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Core Models
class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_agent = Column(Text)
    ip_hash = Column(String(32))
    status = Column(ENUM(SessionStatus), default=SessionStatus.ACTIVE)
    metadata = Column(JSON)
    
    # Relationships
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="session")
    rewrite_sessions = relationship("RewriteSession", back_populates="session")
    feedback_entries = relationship("UserFeedback", back_populates="session")

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('user_sessions.session_id'), nullable=False)
    document_id = Column(String(255), unique=True, nullable=False, index=True)
    filename = Column(String(500))
    content_type = Column(String(100))
    file_size = Column(Integer)
    original_content = Column(Text, nullable=False)
    extracted_text = Column(Text)
    document_format = Column(String(50))
    processing_status = Column(ENUM(DocumentStatus), default=DocumentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)
    metadata = Column(JSON)
    
    # Relationships
    session = relationship("UserSession", back_populates="documents")
    blocks = relationship("DocumentBlock", back_populates="document", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="document")
    violations = relationship("RuleViolation", back_populates="document")

class DocumentBlock(db.Model):
    __tablename__ = 'document_blocks'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    block_id = Column(String(255), nullable=False, index=True)
    block_type = Column(String(50))
    block_order = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    start_position = Column(Integer)
    end_position = Column(Integer)
    structural_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="blocks")
    violations = relationship("RuleViolation", back_populates="block")
    rewrite_results = relationship("RewriteResult", back_populates="block")

# Analysis Models
class AnalysisSession(db.Model):
    __tablename__ = 'analysis_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('user_sessions.session_id'), nullable=False)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    analysis_id = Column(String(255), unique=True, nullable=False, index=True)
    analysis_mode = Column(ENUM(AnalysisMode), default=AnalysisMode.COMPREHENSIVE)
    format_hint = Column(String(50))
    content_type = Column(String(50))
    status = Column(ENUM(ProcessingStatus), default=ProcessingStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    total_processing_time = Column(Float)  # Stored for performance (could be calculated)
    total_errors_found = Column(Integer, default=0)  # Stored for performance
    total_blocks_analyzed = Column(Integer, default=0)
    configuration = Column(JSON)
    
    # Relationships
    session = relationship("UserSession", back_populates="analysis_sessions")
    document = relationship("Document", back_populates="analysis_sessions")
    violations = relationship("RuleViolation", back_populates="analysis")

class StyleRule(db.Model):
    __tablename__ = 'style_rules'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(String(255), unique=True, nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    rule_category = Column(String(100))
    rule_subcategory = Column(String(255))
    description = Column(Text)
    severity = Column(ENUM(SeverityLevel), default=SeverityLevel.MEDIUM)
    is_enabled = Column(Boolean, default=True)
    configuration = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    violations = relationship("RuleViolation", back_populates="rule")

class RuleViolation(db.Model):
    __tablename__ = 'rule_violations'
    
    id = Column(Integer, primary_key=True)
    analysis_id = Column(String(255), ForeignKey('analysis_sessions.analysis_id'), nullable=False)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    block_id = Column(String(255), ForeignKey('document_blocks.block_id'))
    violation_id = Column(String(255), unique=True, nullable=False, index=True)
    rule_id = Column(String(255), ForeignKey('style_rules.rule_id'), nullable=False)
    error_text = Column(Text, nullable=False)
    error_message = Column(Text, nullable=False)
    error_position = Column(Integer, nullable=False)
    end_position = Column(Integer)
    line_number = Column(Integer)
    column_number = Column(Integer)
    severity = Column(ENUM(SeverityLevel))
    confidence_score = Column(Float, default=0.5)
    suggestion = Column(Text)
    context_before = Column(Text)
    context_after = Column(Text)
    rule_metadata = Column(JSON)
    validation_status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("AnalysisSession", back_populates="violations")
    document = relationship("Document", back_populates="violations")
    block = relationship("DocumentBlock", back_populates="violations")
    rule = relationship("StyleRule", back_populates="violations")
    validation_results = relationship("ValidationResult", back_populates="violation")
    feedback_entries = relationship("UserFeedback", back_populates="violation")

# Validation Models
class ValidationResult(db.Model):
    __tablename__ = 'validation_results'
    
    id = Column(Integer, primary_key=True)
    violation_id = Column(String(255), ForeignKey('rule_violations.violation_id'), nullable=False)
    validator_name = Column(String(255), nullable=False)
    validation_decision = Column(ENUM(ValidationDecision), nullable=False)
    confidence_level = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text)
    validation_time = Column(Float)
    evidence = Column(JSON)
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    violation = relationship("RuleViolation", back_populates="validation_results")

# AI Rewriting Models
class RewriteSession(db.Model):
    __tablename__ = 'rewrite_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('user_sessions.session_id'), nullable=False)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    rewrite_id = Column(String(255), unique=True, nullable=False, index=True)
    rewrite_type = Column(String(50))
    rewrite_mode = Column(String(50))
    status = Column(ENUM(ProcessingStatus), default=ProcessingStatus.PENDING)
    pass_number = Column(Integer, default=1)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    total_processing_time = Column(Float)
    model_provider = Column(String(100))
    model_name = Column(String(100))
    configuration = Column(JSON)
    
    # Relationships
    session = relationship("UserSession", back_populates="rewrite_sessions")
    document = relationship("Document")
    results = relationship("RewriteResult", back_populates="rewrite_session")

class RewriteResult(db.Model):
    __tablename__ = 'rewrite_results'
    
    id = Column(Integer, primary_key=True)
    rewrite_id = Column(String(255), ForeignKey('rewrite_sessions.rewrite_id'), nullable=False)
    block_id = Column(String(255), ForeignKey('document_blocks.block_id'))
    original_text = Column(Text, nullable=False)
    rewritten_text = Column(Text, nullable=False)
    improvements_made = Column(JSON)
    quality_score = Column(Float)
    processing_time = Column(Float)
    tokens_used = Column(Integer)
    evaluation_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rewrite_session = relationship("RewriteSession", back_populates="results")
    block = relationship("DocumentBlock", back_populates="rewrite_results")

# Feedback Models
class UserFeedback(db.Model):
    __tablename__ = 'user_feedback'
    
    id = Column(Integer, primary_key=True)
    feedback_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), ForeignKey('user_sessions.session_id'), nullable=False)
    violation_id = Column(String(255), ForeignKey('rule_violations.violation_id'), nullable=False)
    error_type = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=False)
    feedback_type = Column(ENUM(FeedbackType), nullable=False)
    confidence_score = Column(Float, default=0.5)
    user_reason = Column(Text)
    user_agent = Column(Text)
    ip_hash = Column(String(32))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("UserSession", back_populates="feedback_entries")
    violation = relationship("RuleViolation", back_populates="feedback_entries")

# Performance Models
class PerformanceMetric(db.Model):
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_type = Column(String(100))
    session_id = Column(String(255), ForeignKey('user_sessions.session_id'))
    document_id = Column(String(255), ForeignKey('documents.document_id'))
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))
    metadata = Column(JSON)
    recorded_at = Column(DateTime, default=datetime.utcnow)

# Model Configuration
class ModelConfiguration(db.Model):
    __tablename__ = 'model_configurations'
    
    id = Column(Integer, primary_key=True)
    config_id = Column(String(255), unique=True, nullable=False, index=True)
    provider_type = Column(String(50), nullable=False)
    model_name = Column(String(255), nullable=False)
    base_url = Column(String(500))
    api_key_hash = Column(String(255))
    configuration = Column(JSON)
    is_active = Column(Boolean, default=False)
    performance_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ModelUsageLog(db.Model):
    __tablename__ = 'model_usage_logs'
    
    id = Column(Integer, primary_key=True)
    log_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), ForeignKey('user_sessions.session_id'))
    operation_type = Column(String(50), nullable=False)  # 'analysis', 'rewrite', 'validation'
    model_provider = Column(String(100))
    model_name = Column(String(100))
    tokens_used = Column(Integer)
    processing_time_ms = Column(Integer)
    cost_estimate = Column(Float)  # Estimated cost in USD
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("UserSession")
```

## Data Access Layer

Create `database/dao.py`:
```python
"""
Data Access Objects (DAO) for Style Guide AI
Provides high-level database operations with proper error handling.
"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, func

from database import db
from database.models import (
    UserSession, Document, DocumentBlock, AnalysisSession,
    StyleRule, RuleViolation, ValidationResult, RewriteSession,
    RewriteResult, UserFeedback, PerformanceMetric, ModelConfiguration,
    ProcessingStatus, SessionStatus, FeedbackType
)

logger = logging.getLogger(__name__)

class BaseDAO:
    """Base DAO with common functionality."""
    
    @staticmethod
    def generate_id() -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())
    
    @staticmethod
    def handle_db_error(operation: str):
        """Decorator for handling database errors."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except SQLAlchemyError as e:
                    logger.error(f"Database error in {operation}: {e}")
                    db.session.rollback()
                    raise
                except Exception as e:
                    logger.error(f"Unexpected error in {operation}: {e}")
                    db.session.rollback()
                    raise
            return wrapper
        return decorator

class SessionDAO(BaseDAO):
    """DAO for user session operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("create_session")
    def create_session(user_agent: str = None, ip_hash: str = None) -> UserSession:
        """Create a new user session."""
        session = UserSession(
            session_id=BaseDAO.generate_id(),
            user_agent=user_agent,
            ip_hash=ip_hash,
            status=SessionStatus.ACTIVE
        )
        db.session.add(session)
        db.session.commit()
        logger.info(f"Created session: {session.session_id}")
        return session
    
    @staticmethod
    @BaseDAO.handle_db_error("get_session")
    def get_session(session_id: str) -> Optional[UserSession]:
        """Get session by ID."""
        return UserSession.query.filter_by(session_id=session_id).first()
    
    @staticmethod
    @BaseDAO.handle_db_error("update_session_status")
    def update_session_status(session_id: str, status: SessionStatus) -> bool:
        """Update session status."""
        session = UserSession.query.filter_by(session_id=session_id).first()
        if session:
            session.status = status
            session.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

class DocumentDAO(BaseDAO):
    """DAO for document operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("store_document")
    def store_document(
        session_id: str,
        filename: str,
        content: str,
        content_type: str = None,
        document_format: str = None,
        file_size: int = None
    ) -> Document:
        """Store a new document."""
        document = Document(
            session_id=session_id,
            document_id=BaseDAO.generate_id(),
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            original_content=content,
            extracted_text=content,  # For now, same as original
            document_format=document_format,
            processing_status=ProcessingStatus.PROCESSED
        )
        db.session.add(document)
        db.session.commit()
        logger.info(f"Stored document: {document.document_id}")
        return document
    
    @staticmethod
    @BaseDAO.handle_db_error("get_document")
    def get_document(document_id: str) -> Optional[Document]:
        """Get document by ID."""
        return Document.query.filter_by(document_id=document_id).first()
    
    @staticmethod
    @BaseDAO.handle_db_error("get_session_documents")
    def get_session_documents(session_id: str) -> List[Document]:
        """Get all documents for a session."""
        return Document.query.filter_by(session_id=session_id).all()

class BlockDAO(BaseDAO):
    """DAO for document block operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("store_blocks")
    def store_blocks(document_id: str, blocks: List[Dict[str, Any]]) -> List[DocumentBlock]:
        """Store document blocks."""
        db_blocks = []
        for i, block_data in enumerate(blocks):
            block = DocumentBlock(
                document_id=document_id,
                block_id=f"{document_id}_block_{i}",
                block_type=block_data.get('type', 'paragraph'),
                block_order=i,
                content=block_data['content'],
                start_position=block_data.get('start_position'),
                end_position=block_data.get('end_position'),
                structural_metadata=block_data.get('metadata')
            )
            db_blocks.append(block)
        
        db.session.add_all(db_blocks)
        db.session.commit()
        logger.info(f"Stored {len(db_blocks)} blocks for document {document_id}")
        return db_blocks
    
    @staticmethod
    @BaseDAO.handle_db_error("get_document_blocks")
    def get_document_blocks(document_id: str) -> List[DocumentBlock]:
        """Get all blocks for a document."""
        return DocumentBlock.query.filter_by(document_id=document_id).order_by(DocumentBlock.block_order).all()

class AnalysisDAO(BaseDAO):
    """DAO for analysis operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("create_analysis_session")
    def create_analysis_session(
        session_id: str,
        document_id: str,
        analysis_mode: str = "comprehensive",
        configuration: Dict[str, Any] = None
    ) -> AnalysisSession:
        """Create a new analysis session."""
        analysis = AnalysisSession(
            session_id=session_id,
            document_id=document_id,
            analysis_id=BaseDAO.generate_id(),
            analysis_mode=analysis_mode,
            status=ProcessingStatus.PENDING,
            configuration=configuration or {}
        )
        db.session.add(analysis)
        db.session.commit()
        logger.info(f"Created analysis session: {analysis.analysis_id}")
        return analysis
    
    @staticmethod
    @BaseDAO.handle_db_error("update_analysis_status")
    def update_analysis_status(
        analysis_id: str,
        status: ProcessingStatus,
        total_errors: int = None,
        total_blocks: int = None,
        processing_time: float = None
    ) -> bool:
        """Update analysis session status."""
        analysis = AnalysisSession.query.filter_by(analysis_id=analysis_id).first()
        if analysis:
            analysis.status = status
            if status == ProcessingStatus.COMPLETED:
                analysis.completed_at = datetime.utcnow()
            if total_errors is not None:
                analysis.total_errors_found = total_errors
            if total_blocks is not None:
                analysis.total_blocks_analyzed = total_blocks
            if processing_time is not None:
                analysis.total_processing_time = processing_time
            
            db.session.commit()
            return True
        return False

class ViolationDAO(BaseDAO):
    """DAO for rule violation operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("store_violations")
    def store_violations(
        analysis_id: str,
        document_id: str,
        violations: List[Dict[str, Any]]
    ) -> List[RuleViolation]:
        """Store rule violations."""
        db_violations = []
        for violation_data in violations:
            violation = RuleViolation(
                analysis_id=analysis_id,
                document_id=document_id,
                block_id=violation_data.get('block_id'),
                violation_id=BaseDAO.generate_id(),
                rule_id=violation_data['rule_id'],
                error_text=violation_data['error_text'],
                error_message=violation_data['error_message'],
                error_position=violation_data['error_position'],
                end_position=violation_data.get('end_position'),
                line_number=violation_data.get('line_number'),
                column_number=violation_data.get('column_number'),
                severity=violation_data.get('severity'),
                confidence_score=violation_data.get('confidence_score', 0.5),
                suggestion=violation_data.get('suggestion'),
                context_before=violation_data.get('context_before'),
                context_after=violation_data.get('context_after'),
                rule_metadata=violation_data.get('metadata')
            )
            db_violations.append(violation)
        
        db.session.add_all(db_violations)
        db.session.commit()
        logger.info(f"Stored {len(db_violations)} violations for analysis {analysis_id}")
        return db_violations
    
    @staticmethod
    @BaseDAO.handle_db_error("get_analysis_violations")
    def get_analysis_violations(analysis_id: str) -> List[RuleViolation]:
        """Get all violations for an analysis."""
        return RuleViolation.query.filter_by(analysis_id=analysis_id).all()

class FeedbackDAO(BaseDAO):
    """DAO for feedback operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("store_feedback")
    def store_feedback(
        session_id: str,
        violation_id: str,
        feedback_data: Dict[str, Any],
        user_agent: str = None,
        ip_hash: str = None
    ) -> UserFeedback:
        """Store user feedback."""
        feedback = UserFeedback(
            feedback_id=BaseDAO.generate_id(),
            session_id=session_id,
            violation_id=violation_id,
            error_type=feedback_data['error_type'],
            error_message=feedback_data['error_message'],
            feedback_type=FeedbackType(feedback_data['feedback_type']),
            confidence_score=feedback_data.get('confidence_score', 0.5),
            user_reason=feedback_data.get('user_reason'),
            user_agent=user_agent,
            ip_hash=ip_hash
        )
        db.session.add(feedback)
        db.session.commit()
        logger.info(f"Stored feedback: {feedback.feedback_id}")
        return feedback
    
    @staticmethod
    @BaseDAO.handle_db_error("get_session_feedback")
    def get_session_feedback(session_id: str) -> List[UserFeedback]:
        """Get all feedback for a session."""
        return UserFeedback.query.filter_by(session_id=session_id).all()

class PerformanceDAO(BaseDAO):
    """DAO for performance metrics."""
    
    @staticmethod
    @BaseDAO.handle_db_error("record_metric")
    def record_metric(
        metric_type: str,
        metric_name: str,
        metric_value: float,
        metric_unit: str = None,
        session_id: str = None,
        document_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> PerformanceMetric:
        """Record a performance metric."""
        metric = PerformanceMetric(
            metric_type=metric_type,
            session_id=session_id,
            document_id=document_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            metadata=metadata
        )
        db.session.add(metric)
        db.session.commit()
        return metric
```

## Service Layer Integration

Create `database/services.py`:
```python
"""
Service layer for database operations
Provides business logic and integrates with existing services.
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from database.dao import (
    SessionDAO, DocumentDAO, BlockDAO, AnalysisDAO, 
    ViolationDAO, FeedbackDAO, PerformanceDAO
)
from database.models import ProcessingStatus, SessionStatus

logger = logging.getLogger(__name__)

class DatabaseService:
    """Main service for database operations."""
    
    def __init__(self):
        self.session_dao = SessionDAO()
        self.document_dao = DocumentDAO()
        self.block_dao = BlockDAO()
        self.analysis_dao = AnalysisDAO()
        self.violation_dao = ViolationDAO()
        self.feedback_dao = FeedbackDAO()
        self.performance_dao = PerformanceDAO()
    
    def create_user_session(self, user_agent: str = None, ip_address: str = None) -> str:
        """Create a new user session and return session ID."""
        # Hash IP for privacy
        ip_hash = self._hash_ip(ip_address) if ip_address else None
        
        session = self.session_dao.create_session(user_agent=user_agent, ip_hash=ip_hash)
        return session.session_id
    
    def process_document_upload(
        self, 
        session_id: str, 
        content: str, 
        filename: str = None,
        document_format: str = None,
        blocks: List[Dict[str, Any]] = None
    ) -> Tuple[str, str]:  # Returns (document_id, analysis_id)
        """Process document upload and create initial analysis session."""
        
        # Store document
        document = self.document_dao.store_document(
            session_id=session_id,
            filename=filename,
            content=content,
            document_format=document_format,
            file_size=len(content.encode('utf-8'))
        )
        
        # Store blocks if provided
        if blocks:
            self.block_dao.store_blocks(document.document_id, blocks)
        
        # Create initial analysis session
        analysis = self.analysis_dao.create_analysis_session(
            session_id=session_id,
            document_id=document.document_id
        )
        
        logger.info(f"Processed document upload: doc={document.document_id}, analysis={analysis.analysis_id}")
        return document.document_id, analysis.analysis_id
    
    def store_analysis_results(
        self,
        analysis_id: str,
        document_id: str,
        violations: List[Dict[str, Any]],
        processing_time: float = None,
        total_blocks_analyzed: int = None
    ) -> bool:
        """Store analysis results and update analysis status."""
        
        # Store violations
        stored_violations = self.violation_dao.store_violations(
            analysis_id=analysis_id,
            document_id=document_id,
            violations=violations
        )
        
        # Update analysis status
        success = self.analysis_dao.update_analysis_status(
            analysis_id=analysis_id,
            status=ProcessingStatus.COMPLETED,
            total_errors=len(stored_violations),
            total_blocks=total_blocks_analyzed,
            processing_time=processing_time
        )
        
        # Record performance metrics
        if processing_time:
            self.performance_dao.record_metric(
                metric_type="analysis_time",
                metric_name="total_analysis_time",
                metric_value=processing_time,
                metric_unit="seconds"
            )
        
        return success
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """Get complete analysis results."""
        violations = self.violation_dao.get_analysis_violations(analysis_id)
        
        # Convert to format expected by frontend
        results = {
            'analysis_id': analysis_id,
            'violations': [
                {
                    'violation_id': v.violation_id,
                    'rule_id': v.rule_id,
                    'error_text': v.error_text,
                    'error_message': v.error_message,
                    'error_position': v.error_position,
                    'end_position': v.end_position,
                    'line_number': v.line_number,
                    'column_number': v.column_number,
                    'severity': v.severity.value if v.severity else None,
                    'confidence_score': v.confidence_score,
                    'suggestion': v.suggestion,
                    'context_before': v.context_before,
                    'context_after': v.context_after
                }
                for v in violations
            ],
            'total_violations': len(violations),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return results
    
    def store_user_feedback(
        self,
        session_id: str,
        violation_id: str,
        feedback_data: Dict[str, Any],
        user_agent: str = None,
        ip_address: str = None
    ) -> Tuple[bool, str]:
        """Store user feedback."""
        try:
            ip_hash = self._hash_ip(ip_address) if ip_address else None
            
            feedback = self.feedback_dao.store_feedback(
                session_id=session_id,
                violation_id=violation_id,
                feedback_data=feedback_data,
                user_agent=user_agent,
                ip_hash=ip_hash
            )
            
            return True, feedback.feedback_id
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
            return False, str(e)
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a session."""
        session = self.session_dao.get_session(session_id)
        if not session:
            return {}
        
        documents = self.document_dao.get_session_documents(session_id)
        feedback_entries = self.feedback_dao.get_session_feedback(session_id)
        
        return {
            'session_id': session_id,
            'session_status': session.status.value,
            'created_at': session.created_at.isoformat(),
            'total_documents': len(documents),
            'total_feedback': len(feedback_entries),
            'feedback_breakdown': self._analyze_feedback(feedback_entries)
        }
    
    def cleanup_expired_sessions(self, days_old: int = 7) -> int:
        """Clean up old sessions and related data."""
        # This would implement cleanup logic
        # For now, just return 0
        return 0
    
    def _hash_ip(self, ip_address: str) -> str:
        """Hash IP address for privacy."""
        import hashlib
        salt = "style_guide_privacy_salt_2024"
        return hashlib.sha256(f"{salt}:{ip_address}".encode()).hexdigest()[:16]
    
    def _analyze_feedback(self, feedback_entries: List) -> Dict[str, int]:
        """Analyze feedback entries."""
        breakdown = {'correct': 0, 'incorrect': 0, 'partially_correct': 0}
        for feedback in feedback_entries:
            feedback_type = feedback.feedback_type.value
            if feedback_type in breakdown:
                breakdown[feedback_type] += 1
        return breakdown

# Global service instance
database_service = DatabaseService()
```

## API Route Modifications

Update `app_modules/api_routes.py`:
```python
"""
Updated API routes with database integration
"""

import logging
import time
from flask import request, jsonify, session, make_response
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from database.services import database_service

logger = logging.getLogger(__name__)

def setup_routes(app, document_processor, style_analyzer, ai_rewriter):
    """Setup all API routes with database integration."""
    
    @app.before_request
    def ensure_session():
        """Ensure each request has a session."""
        if 'session_id' not in session:
            # Create new database session
            session_id = database_service.create_user_session(
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
            session['session_id'] = session_id
            logger.info(f"Created new session: {session_id}")
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Handle file upload with database storage."""
        try:
            session_id = session.get('session_id')
            
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if file and document_processor.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Extract text using existing processor
                content = document_processor.extract_text_from_upload(file)
                
                if content:
                    # Store in database
                    document_id, analysis_id = database_service.process_document_upload(
                        session_id=session_id,
                        content=content,
                        filename=filename,
                        document_format=document_processor.detect_format(filename)
                    )
                    
                    return jsonify({
                        'success': True,
                        'content': content,
                        'filename': filename,
                        'document_id': document_id,
                        'analysis_id': analysis_id,
                        'session_id': session_id
                    })
                else:
                    return jsonify({'error': 'Failed to extract text from file'}), 400
            else:
                return jsonify({'error': 'File type not supported'}), 400
                
        except RequestEntityTooLarge:
            return jsonify({'error': 'File too large'}), 413
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    @app.route('/analyze', methods=['POST'])
    def analyze_content():
        """Analyze content with database storage."""
        try:
            session_id = session.get('session_id')
            data = request.get_json()
            
            if not data or 'content' not in data:
                return jsonify({'error': 'No content provided'}), 400
            
            content = data['content']
            format_hint = data.get('format_hint', 'auto')
            content_type = data.get('content_type', 'concept')
            
            # Store document if not already stored
            document_id = data.get('document_id')
            analysis_id = data.get('analysis_id')
            
            if not document_id:
                document_id, analysis_id = database_service.process_document_upload(
                    session_id=session_id,
                    content=content,
                    filename="direct_input.txt",
                    document_format=format_hint
                )
            
            # Perform analysis
            start_time = time.time()
            analysis_result = style_analyzer.analyze_with_blocks(
                content, 
                format_hint=format_hint,
                content_type=content_type
            )
            processing_time = time.time() - start_time
            
            # Convert analysis result to database format
            violations = []
            if 'errors' in analysis_result:
                for error in analysis_result['errors']:
                    violations.append({
                        'rule_id': error.get('rule_id', 'unknown'),
                        'error_text': error.get('text', ''),
                        'error_message': error.get('message', ''),
                        'error_position': error.get('start', 0),
                        'end_position': error.get('end'),
                        'line_number': error.get('line'),
                        'column_number': error.get('column'),
                        'severity': error.get('severity', 'medium'),
                        'confidence_score': error.get('confidence', 0.5),
                        'suggestion': error.get('suggestion'),
                        'context_before': error.get('context_before'),
                        'context_after': error.get('context_after'),
                        'metadata': error.get('metadata', {})
                    })
            
            # Store results in database
            database_service.store_analysis_results(
                analysis_id=analysis_id,
                document_id=document_id,
                violations=violations,
                processing_time=processing_time,
                total_blocks_analyzed=len(analysis_result.get('blocks', []))
            )
            
            # Return enhanced result with database IDs
            analysis_result.update({
                'document_id': document_id,
                'analysis_id': analysis_id,
                'session_id': session_id,
                'processing_time': processing_time
            })
            
            return jsonify(analysis_result)
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    
    @app.route('/feedback', methods=['POST'])
    def submit_feedback():
        """Submit user feedback with database storage."""
        try:
            session_id = session.get('session_id')
            data = request.get_json()
            
            required_fields = ['violation_id', 'error_type', 'error_message', 'feedback_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Store feedback in database
            success, result = database_service.store_user_feedback(
                session_id=session_id,
                violation_id=data['violation_id'],
                feedback_data={
                    'error_type': data['error_type'],
                    'error_message': data['error_message'],
                    'feedback_type': data['feedback_type'],
                    'confidence_score': data.get('confidence_score', 0.5),
                    'user_reason': data.get('user_reason')
                },
                user_agent=request.headers.get('User-Agent'),
                ip_address=request.remote_addr
            )
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Feedback stored successfully',
                    'feedback_id': result
                })
            else:
                return jsonify({'error': result}), 500
                
        except Exception as e:
            logger.error(f"Feedback error: {str(e)}")
            return jsonify({'error': f'Feedback submission failed: {str(e)}'}), 500
    
    @app.route('/analytics')
    def get_analytics():
        """Get session analytics."""
        try:
            session_id = session.get('session_id')
            analytics = database_service.get_session_analytics(session_id)
            return jsonify(analytics)
        except Exception as e:
            logger.error(f"Analytics error: {str(e)}")
            return jsonify({'error': f'Failed to get analytics: {str(e)}'}), 500
```

## Migration Scripts

Create `migrations/init_database.py`:
```python
"""
Database initialization and migration script
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from database import init_db, db
from database.models import *  # Import all models
from config import Config

def create_app():
    """Create Flask app for migration."""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def init_database():
    """Initialize database with all tables."""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Insert default rules
        insert_default_rules()
        print("✅ Default rules inserted!")

def insert_default_rules():
    """Insert default style rules."""
    from database.models import StyleRule, SeverityLevel
    
    default_rules = [
        {
            'rule_id': 'passive_voice',
            'rule_name': 'Passive Voice Detection',
            'rule_category': 'grammar',
            'description': 'Detects passive voice constructions',
            'severity': SeverityLevel.MEDIUM
        },
        {
            'rule_id': 'sentence_length',
            'rule_name': 'Sentence Length Check',
            'rule_category': 'language',
            'description': 'Checks for overly long sentences',
            'severity': SeverityLevel.LOW
        },
        {
            'rule_id': 'anthropomorphism',
            'rule_name': 'Anthropomorphism Detection',
            'rule_category': 'language',
            'description': 'Detects anthropomorphic language',
            'severity': SeverityLevel.HIGH
        },
        # Add more default rules as needed
    ]
    
    for rule_data in default_rules:
        existing_rule = StyleRule.query.filter_by(rule_id=rule_data['rule_id']).first()
        if not existing_rule:
            rule = StyleRule(**rule_data)
            db.session.add(rule)
    
    db.session.commit()

if __name__ == '__main__':
    init_database()
```

Create `migrations/migrate_existing_data.py`:
```python
"""
Migration script to move existing file-based data to database
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from database import init_db, db
from database.services import database_service
from config import Config

def create_app():
    """Create Flask app for migration."""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def migrate_feedback_data():
    """Migrate existing feedback data from JSONL files to database."""
    app = create_app()
    
    with app.app_context():
        feedback_dir = Path("feedback_data/daily")
        if not feedback_dir.exists():
            print("No existing feedback data found.")
            return
        
        migrated_count = 0
        
        for jsonl_file in feedback_dir.glob("*.jsonl"):
            print(f"Processing {jsonl_file.name}...")
            
            with open(jsonl_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            feedback_data = json.loads(line.strip())
                            
                            # Convert to new format
                            success, result = database_service.store_user_feedback(
                                session_id=feedback_data['session_id'],
                                violation_id=feedback_data['error_id'],  # Using error_id as violation_id
                                feedback_data={
                                    'error_type': feedback_data['error_type'],
                                    'error_message': feedback_data['error_message'],
                                    'feedback_type': feedback_data['feedback_type'],
                                    'confidence_score': feedback_data.get('confidence_score', 0.5),
                                    'user_reason': feedback_data.get('user_reason')
                                },
                                user_agent=feedback_data.get('user_agent'),
                                ip_address=None  # IP hash already in data
                            )
                            
                            if success:
                                migrated_count += 1
                            
                        except Exception as e:
                            print(f"Error processing feedback entry: {e}")
        
        print(f"✅ Migrated {migrated_count} feedback entries to database")

if __name__ == '__main__':
    migrate_feedback_data()
```

## Testing Implementation

Create `tests/test_database_integration.py`:
```python
"""
Integration tests for database functionality
"""

import pytest
import tempfile
import os
from flask import Flask
from database import init_db, db
from database.services import database_service
from database.models import UserSession, Document, RuleViolation
from config import Config

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

@pytest.fixture
def app():
    """Create test Flask app."""
    app = Flask(__name__)
    app.config.from_object(TestConfig)
    init_db(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

def test_session_creation(app):
    """Test user session creation."""
    with app.app_context():
        session_id = database_service.create_user_session(
            user_agent="test-agent",
            ip_address="127.0.0.1"
        )
        
        assert session_id is not None
        session = UserSession.query.filter_by(session_id=session_id).first()
        assert session is not None
        assert session.user_agent == "test-agent"

def test_document_storage(app):
    """Test document storage."""
    with app.app_context():
        session_id = database_service.create_user_session()
        
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test document content",
            filename="test.txt",
            document_format="txt"
        )
        
        assert document_id is not None
        assert analysis_id is not None
        
        document = Document.query.filter_by(document_id=document_id).first()
        assert document is not None
        assert document.original_content == "Test document content"

def test_violation_storage(app):
    """Test rule violation storage."""
    with app.app_context():
        session_id = database_service.create_user_session()
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test content",
            filename="test.txt"
        )
        
        violations = [
            {
                'rule_id': 'test_rule',
                'error_text': 'test error',
                'error_message': 'Test error message',
                'error_position': 0,
                'severity': 'medium'
            }
        ]
        
        success = database_service.store_analysis_results(
            analysis_id=analysis_id,
            document_id=document_id,
            violations=violations
        )
        
        assert success is True
        
        stored_violations = RuleViolation.query.filter_by(analysis_id=analysis_id).all()
        assert len(stored_violations) == 1
        assert stored_violations[0].error_text == 'test error'

def test_feedback_storage(app):
    """Test feedback storage."""
    with app.app_context():
        session_id = database_service.create_user_session()
        
        # Create a violation first
        document_id, analysis_id = database_service.process_document_upload(
            session_id=session_id,
            content="Test content",
            filename="test.txt"
        )
        
        violations = [
            {
                'rule_id': 'test_rule',
                'error_text': 'test error',
                'error_message': 'Test error message',
                'error_position': 0
            }
        ]
        
        database_service.store_analysis_results(
            analysis_id=analysis_id,
            document_id=document_id,
            violations=violations
        )
        
        violation = RuleViolation.query.filter_by(analysis_id=analysis_id).first()
        
        # Store feedback
        success, feedback_id = database_service.store_user_feedback(
            session_id=session_id,
            violation_id=violation.violation_id,
            feedback_data={
                'error_type': 'test_rule',
                'error_message': 'Test error message',
                'feedback_type': 'correct',
                'confidence_score': 0.8
            }
        )
        
        assert success is True
        assert feedback_id is not None
```

## Deployment Guide

### 1. Production Database Setup

For production, use PostgreSQL:

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE style_guide_ai;
CREATE USER style_guide_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE style_guide_ai TO style_guide_user;
\q
```

### 2. Environment Configuration

Create `.env.production`:
```env
DATABASE_URL=postgresql://style_guide_user:your_secure_password@localhost:5432/style_guide_ai
FLASK_ENV=production
SECRET_KEY=your_production_secret_key
```

### 3. Migration Commands

```bash
# Initialize migration repository
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade

# For new changes
flask db migrate -m "Description of changes"
flask db upgrade
```

### 4. Application Updates

Update `app.py`:
```python
from app_modules.app_factory import create_app
from config import Config
from database import init_db

app, socketio = create_app(Config)

# Initialize database
init_db(app)

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist
        from database import db
        db.create_all()
    
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
```

## Performance Optimization

### 1. Database Indexing
```sql
-- Add indexes for common queries
CREATE INDEX idx_user_sessions_status ON user_sessions(status, created_at);
CREATE INDEX idx_documents_session_processing ON documents(session_id, processing_status);
CREATE INDEX idx_violations_analysis_confidence ON rule_violations(analysis_id, confidence_score);
CREATE INDEX idx_feedback_session_type ON user_feedback(session_id, feedback_type, created_at);
```

### 2. Query Optimization
```python
# Use eager loading for relationships
violations = RuleViolation.query.options(
    db.joinedload(RuleViolation.rule),
    db.joinedload(RuleViolation.block)
).filter_by(analysis_id=analysis_id).all()

# Use pagination for large result sets
violations = RuleViolation.query.filter_by(
    analysis_id=analysis_id
).paginate(page=1, per_page=50, error_out=False)
```

### 3. Connection Pooling
Add to `config.py`:
```python
# Database connection pooling
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True
}
```

## Implementation Checklist

- [ ] Install required packages
- [ ] Create database models
- [ ] Implement DAO layer
- [ ] Create service layer
- [ ] Update API routes
- [ ] Create migration scripts
- [ ] Write tests
- [ ] Set up production database
- [ ] Update application configuration
- [ ] Test end-to-end functionality
- [ ] Deploy to production
- [ ] Monitor performance

## Next Steps

1. **Phase 1**: Implement core models and basic CRUD operations
2. **Phase 2**: Integrate with existing analysis pipeline
3. **Phase 3**: Migrate existing file-based data
4. **Phase 4**: Add advanced analytics and reporting
5. **Phase 5**: Optimize performance and add monitoring

This implementation provides a solid foundation for transitioning from file-based storage to a comprehensive database system while maintaining compatibility with your existing codebase.
