"""
SQLAlchemy Models for Style Guide AI
Complete database models matching the schema design.
"""

import json
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
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

class ProcessingStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class FeedbackType(Enum):
    CORRECT = "correct"
    INCORRECT = "incorrect"
    PARTIALLY_CORRECT = "partially_correct"

class SeverityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BlockType(Enum):
    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST = "list"
    CODE = "code"
    TABLE = "table"
    QUOTE = "quote"
    OTHER = "other"

# Core Models
class UserSession(db.Model):
    """Records individual user sessions to track usage and associate related data."""
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_agent = Column(Text)
    ip_hash = Column(String(32))  # Hashed for privacy
    status = Column(ENUM(SessionStatus), default=SessionStatus.ACTIVE)
    
    # Relationships
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="session")
    feedback_entries = relationship("UserFeedback", back_populates="session")
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'

class Document(db.Model):
    """Stores the content uploaded by users for analysis."""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id'), nullable=False)
    document_id = Column(String(255), unique=True, nullable=False, index=True)
    filename = Column(String(500))
    content_type = Column(String(100))  # concept, procedure, reference, etc.
    file_size = Column(Integer)
    original_content = Column(Text, nullable=False)  # Original text (or binary for PDF/DOCX)
    extracted_text = Column(Text)  # Extracted text from PDF/DOCX, same as original for text formats
    document_format = Column(String(50))  # 'adoc', 'md', 'dita', 'docx', 'pdf', 'txt'
    processing_status = Column(ENUM(DocumentStatus), default=DocumentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    
    # Relationships
    session = relationship("UserSession", back_populates="documents")
    blocks = relationship("DocumentBlock", back_populates="document", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="document")
    violations = relationship("RuleViolation", back_populates="document")
    
    def __repr__(self):
        return f'<Document {self.document_id}>'

class DocumentBlock(db.Model):
    """Represents individual blocks within a document for granular analysis."""
    __tablename__ = 'document_blocks'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    block_id = Column(String(255), unique=True, nullable=False, index=True)
    block_type = Column(ENUM(BlockType), default=BlockType.PARAGRAPH)
    block_order = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    start_position = Column(Integer)  # Character position where block starts in original document
    end_position = Column(Integer)  # Character position where block ends in original document
    structural_metadata = Column(JSON)  # Block-level parsing info (heading level, list type, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="blocks")
    violations = relationship("RuleViolation", back_populates="block")
    
    def __repr__(self):
        return f'<DocumentBlock {self.block_id}>'

# Analysis Models
class AnalysisSession(db.Model):
    """Records each analysis run, linking a user session to a specific document and its results."""
    __tablename__ = 'analysis_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id'), nullable=False)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    analysis_id = Column(String(255), unique=True, nullable=False, index=True)
    content_type = Column(String(50))
    format_hint = Column(String(50))  # Document format hint provided during analysis (e.g., adoc, md, auto)
    status = Column(ENUM(ProcessingStatus), default=ProcessingStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    total_errors_found = Column(Integer, default=0)  # Stored for performance
    total_blocks_analyzed = Column(Integer, default=0)
    
    # Relationships
    session = relationship("UserSession", back_populates="analysis_sessions")
    document = relationship("Document", back_populates="analysis_sessions")
    violations = relationship("RuleViolation", back_populates="analysis")
    
    def __repr__(self):
        return f'<AnalysisSession {self.analysis_id}>'

class StyleRule(db.Model):
    """Master catalog of all style rules available in the system."""
    __tablename__ = 'style_rules'
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(String(255), unique=True, nullable=False, index=True)
    rule_name = Column(String(255), nullable=False)
    rule_category = Column(String(100))  # 'grammar', 'language', 'punctuation', etc.
    rule_subcategory = Column(String(255))  # More granular categorization (e.g., 'subject-verb agreement')
    description = Column(Text)
    severity = Column(ENUM(SeverityLevel), default=SeverityLevel.MEDIUM)
    is_enabled = Column(Boolean, default=True)
    configuration = Column(JSON)  # Rule-specific settings and parameters
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    violations = relationship("RuleViolation", back_populates="rule")
    
    def __repr__(self):
        return f'<StyleRule {self.rule_id}>'

class RuleViolation(db.Model):
    """Stores every individual style violation found during an analysis session."""
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
    confidence_score = Column(Float, default=0.5, nullable=False)
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
    feedback_entries = relationship("UserFeedback", back_populates="violation")
    
    def __repr__(self):
        return f'<RuleViolation {self.violation_id}>'

# Feedback Models
class UserFeedback(db.Model):
    """Records all user feedback submitted for specific rule violations."""
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    feedback_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id'), nullable=False)
    violation_id = Column(String(255), ForeignKey('rule_violations.violation_id'), nullable=False)
    error_type = Column(String(255), nullable=False, index=True)  # Indexed for rule improvement queries
    error_message = Column(Text, nullable=False)
    feedback_type = Column(ENUM(FeedbackType), nullable=False, index=True)  # Indexed: 'correct', 'incorrect', 'partially_correct'
    confidence_score = Column(Float, default=0.5)
    user_reason = Column(Text)  # Optional plain text field for additional user comments
    
    # Content fields for rule improvement (directly stored for easy querying)
    error_text = Column(Text)  # The actual flagged text
    context_before = Column(Text)  # Text before the error for context
    context_after = Column(Text)  # Text after the error for context
    suggestion = Column(Text)  # The suggestion that was shown to user
    rule_id = Column(String(255), index=True)  # Direct reference to rule for quick filtering
    
    # Timestamp (user_agent/ip_hash tracked at session level)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    session = relationship("UserSession", back_populates="feedback_entries")
    violation = relationship("RuleViolation", back_populates="feedback_entries")
    
    # Unique constraint to ensure one feedback per violation per session
    __table_args__ = (
        UniqueConstraint('session_id', 'violation_id', name='unique_session_violation_feedback'),
    )
    
    def __repr__(self):
        return f'<UserFeedback {self.feedback_id}>'

# Performance and Monitoring Models
class PerformanceMetric(db.Model):
    """Tracks performance metrics for system monitoring."""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_type = Column(String(100))  # 'block_processing', 'analysis_time', 'rewrite_time'
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))  # 'seconds', 'milliseconds', 'count', etc.
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<PerformanceMetric {self.metric_name}>'
