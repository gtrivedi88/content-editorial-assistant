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
    session_metadata = Column(JSON)
    
    # Relationships
    documents = relationship("Document", back_populates="session", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="session")
    rewrite_sessions = relationship("RewriteSession", back_populates="session")
    feedback_entries = relationship("UserFeedback", back_populates="session")
    performance_metrics = relationship("PerformanceMetric", back_populates="session")
    
    def __repr__(self):
        return f'<UserSession {self.session_id}>'

class Document(db.Model):
    """Stores the content uploaded by users for analysis."""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id'), nullable=False)
    document_id = Column(String(255), unique=True, nullable=False, index=True)
    filename = Column(String(500))
    content_type = Column(String(100))
    file_size = Column(Integer)
    original_content = Column(Text, nullable=False)
    extracted_text = Column(Text)
    document_format = Column(String(50))  # 'adoc', 'md', 'dita', 'docx', 'pdf', 'txt'
    processing_status = Column(ENUM(DocumentStatus), default=DocumentStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime)
    document_metadata = Column(JSON)
    
    # Relationships
    session = relationship("UserSession", back_populates="documents")
    blocks = relationship("DocumentBlock", back_populates="document", cascade="all, delete-orphan")
    analysis_sessions = relationship("AnalysisSession", back_populates="document")
    violations = relationship("RuleViolation", back_populates="document")
    rewrite_sessions = relationship("RewriteSession", back_populates="document")
    performance_metrics = relationship("PerformanceMetric", back_populates="document")
    
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
    start_position = Column(Integer)
    end_position = Column(Integer)
    structural_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document", back_populates="blocks")
    violations = relationship("RuleViolation", back_populates="block")
    rewrite_results = relationship("RewriteResult", back_populates="block")
    rewrite_sessions = relationship("RewriteSession", back_populates="block")
    
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
    analysis_mode = Column(ENUM(AnalysisMode), default=AnalysisMode.COMPREHENSIVE)
    format_hint = Column(String(50))
    content_type = Column(String(50))
    status = Column(ENUM(ProcessingStatus), default=ProcessingStatus.PENDING)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime)
    total_errors_found = Column(Integer, default=0)  # Stored for performance
    total_blocks_analyzed = Column(Integer, default=0)
    configuration = Column(JSON)
    
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
    rule_subcategory = Column(String(255))
    description = Column(Text)
    severity = Column(ENUM(SeverityLevel), default=SeverityLevel.MEDIUM)
    is_enabled = Column(Boolean, default=True)
    configuration = Column(JSON)
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
    validation_results = relationship("ValidationResult", back_populates="violation")
    feedback_entries = relationship("UserFeedback", back_populates="violation")
    
    def __repr__(self):
        return f'<RuleViolation {self.violation_id}>'

# Validation Models
class ValidationResult(db.Model):
    """Stores results from multi-pass validation system."""
    __tablename__ = 'validation_results'
    
    id = Column(Integer, primary_key=True)
    violation_id = Column(String(255), ForeignKey('rule_violations.violation_id'), nullable=False)
    validator_name = Column(String(255), nullable=False)
    validation_decision = Column(ENUM(ValidationDecision), nullable=False)
    confidence_level = Column(String(50), nullable=False)  # 'high', 'medium', 'low'
    confidence_score = Column(Float, nullable=False)
    reasoning = Column(Text)
    validation_time = Column(Float)
    evidence = Column(JSON)  # ValidationEvidence data
    validation_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    violation = relationship("RuleViolation", back_populates="validation_results")
    
    def __repr__(self):
        return f'<ValidationResult {self.validator_name}:{self.violation_id}>'

class AmbiguityDetection(db.Model):
    """Records ambiguity detection results."""
    __tablename__ = 'ambiguity_detections'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    block_id = Column(String(255), ForeignKey('document_blocks.block_id'))
    ambiguity_id = Column(String(255), unique=True, nullable=False, index=True)
    ambiguity_type = Column(String(50))  # 'referential', 'lexical', 'syntactic', 'semantic'
    ambiguous_text = Column(Text, nullable=False)
    position = Column(Integer, nullable=False)
    end_position = Column(Integer)
    confidence_score = Column(Float)
    context_analysis = Column(JSON)
    resolution_suggestions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document")
    block = relationship("DocumentBlock")
    
    def __repr__(self):
        return f'<AmbiguityDetection {self.ambiguity_id}>'

# AI Rewriting Models
class RewriteSession(db.Model):
    """Records AI-powered block-level rewriting operations using assembly line approach."""
    __tablename__ = 'rewrite_sessions'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id'), nullable=False)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    block_id = Column(String(255), ForeignKey('document_blocks.block_id'), nullable=False)
    rewrite_id = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(ENUM(ProcessingStatus), default=ProcessingStatus.PENDING)
    pass_number = Column(Integer, default=1)  # For multi-pass rewriting
    completed_at = Column(DateTime)
    processing_time_ms = Column(Integer)  # Processing time in milliseconds
    tokens_used = Column(Integer)  # Total tokens consumed
    configuration = Column(JSON)
    
    # Relationships
    session = relationship("UserSession", back_populates="rewrite_sessions")
    document = relationship("Document", back_populates="rewrite_sessions")
    block = relationship("DocumentBlock", back_populates="rewrite_sessions")
    results = relationship("RewriteResult", back_populates="rewrite_session")
    
    def __repr__(self):
        return f'<RewriteSession {self.rewrite_id}>'

class RewriteResult(db.Model):
    """Stores the actual rewritten content and quality metrics for each rewrite operation."""
    __tablename__ = 'rewrite_results'
    
    id = Column(Integer, primary_key=True)
    rewrite_id = Column(String(255), ForeignKey('rewrite_sessions.rewrite_id'), nullable=False)
    block_id = Column(String(255), ForeignKey('document_blocks.block_id'))
    result_id = Column(String(255), unique=True, nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    rewritten_text = Column(Text, nullable=False)
    improvements_made = Column(JSON)  # List of specific improvements
    quality_score = Column(Float)  # Calculated quality improvement score (0.0 to 1.0)
    processing_time = Column(Float)
    tokens_used = Column(Integer)
    readability_before = Column(Float)  # Readability score of original text
    readability_after = Column(Float)  # Readability score of rewritten text
    evaluation_metrics = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    rewrite_session = relationship("RewriteSession", back_populates="results")
    block = relationship("DocumentBlock", back_populates="rewrite_results")
    
    def __repr__(self):
        return f'<RewriteResult {self.result_id}>'

# Feedback Models
class UserFeedback(db.Model):
    """Records all user feedback submitted for specific rule violations."""
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    feedback_id = Column(String(255), unique=True, nullable=False, index=True)
    session_id = Column(String(255), ForeignKey('sessions.session_id'), nullable=False)
    violation_id = Column(String(255), ForeignKey('rule_violations.violation_id'), nullable=False)
    error_type = Column(String(255), nullable=False)
    error_message = Column(Text, nullable=False)
    feedback_type = Column(ENUM(FeedbackType), nullable=False)  # 'correct', 'incorrect', 'partially_correct'
    confidence_score = Column(Float, default=0.5)
    user_reason = Column(Text)  # Optional plain text field for additional user comments
    user_agent = Column(Text)
    ip_hash = Column(String(32))
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
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
    session_id = Column(String(255), ForeignKey('sessions.session_id'))
    document_id = Column(String(255), ForeignKey('documents.document_id'))
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50))  # 'seconds', 'milliseconds', 'count', etc.
    performance_metadata = Column(JSON)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("UserSession", back_populates="performance_metrics")
    document = relationship("Document", back_populates="performance_metrics")
    
    def __repr__(self):
        return f'<PerformanceMetric {self.metric_name}>'

# Error Consolidation Model
class ErrorConsolidation(db.Model):
    """Tracks consolidated error messages to reduce UI clutter."""
    __tablename__ = 'error_consolidation'
    
    id = Column(Integer, primary_key=True)
    document_id = Column(String(255), ForeignKey('documents.document_id'), nullable=False)
    analysis_id = Column(String(255), ForeignKey('analysis_sessions.analysis_id'), nullable=False)
    consolidation_id = Column(String(255), unique=True, nullable=False, index=True)
    related_violation_ids = Column(JSON)  # Array of related violation IDs
    consolidated_message = Column(Text, nullable=False)
    priority_score = Column(Float)
    span_start = Column(Integer)
    span_end = Column(Integer)
    consolidation_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    document = relationship("Document")
    analysis = relationship("AnalysisSession")
    
    def __repr__(self):
        return f'<ErrorConsolidation {self.consolidation_id}>'
