"""
Data Access Objects (DAO) for Style Guide AI
Provides high-level database operations with proper error handling.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, or_, func

from database import db
from database.models import (
    UserSession, Document, DocumentBlock, AnalysisSession,
    StyleRule, RuleViolation, ValidationResult, RewriteSession,
    RewriteResult, UserFeedback, PerformanceMetric, ModelConfiguration,
    ModelUsageLog, AmbiguityDetection, ErrorConsolidation,
    ProcessingStatus, SessionStatus, FeedbackType, DocumentStatus,
    AnalysisMode, RewriteType, RewriteMode, OperationType, SeverityLevel
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
    
    @staticmethod
    @BaseDAO.handle_db_error("get_active_sessions")
    def get_active_sessions(limit: int = 100) -> List[UserSession]:
        """Get active sessions with optional limit."""
        return UserSession.query.filter_by(status=SessionStatus.ACTIVE).limit(limit).all()
    
    @staticmethod
    @BaseDAO.handle_db_error("cleanup_expired_sessions")
    def cleanup_expired_sessions(hours_old: int = 24) -> int:
        """Clean up expired sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
        expired_sessions = UserSession.query.filter(
            UserSession.updated_at < cutoff_time,
            UserSession.status == SessionStatus.ACTIVE
        ).all()
        
        count = 0
        for session in expired_sessions:
            session.status = SessionStatus.EXPIRED
            count += 1
        
        if count > 0:
            db.session.commit()
            logger.info(f"Expired {count} old sessions")
        
        return count

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
            processing_status=DocumentStatus.PROCESSED
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
        return Document.query.filter_by(session_id=session_id).order_by(Document.created_at.desc()).all()
    
    @staticmethod
    @BaseDAO.handle_db_error("update_document_status")
    def update_document_status(document_id: str, status: DocumentStatus) -> bool:
        """Update document processing status."""
        document = Document.query.filter_by(document_id=document_id).first()
        if document:
            document.processing_status = status
            if status == DocumentStatus.PROCESSED:
                document.processed_at = datetime.utcnow()
            db.session.commit()
            return True
        return False

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
    
    @staticmethod
    @BaseDAO.handle_db_error("get_block")
    def get_block(block_id: str) -> Optional[DocumentBlock]:
        """Get a specific block by ID."""
        return DocumentBlock.query.filter_by(block_id=block_id).first()

class AnalysisDAO(BaseDAO):
    """DAO for analysis operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("create_analysis_session")
    def create_analysis_session(
        session_id: str,
        document_id: str,
        analysis_mode: str = "comprehensive",
        format_hint: str = None,
        content_type: str = None,
        configuration: Dict[str, Any] = None
    ) -> AnalysisSession:
        """Create a new analysis session."""
        analysis = AnalysisSession(
            session_id=session_id,
            document_id=document_id,
            analysis_id=BaseDAO.generate_id(),
            analysis_mode=AnalysisMode(analysis_mode),
            format_hint=format_hint,
            content_type=content_type,
            status=ProcessingStatus.PENDING,
            configuration=configuration or {}
        )
        db.session.add(analysis)
        db.session.commit()
        logger.info(f"Created analysis session: {analysis.analysis_id}")
        return analysis
    
    @staticmethod
    @BaseDAO.handle_db_error("get_analysis_session")
    def get_analysis_session(analysis_id: str) -> Optional[AnalysisSession]:
        """Get analysis session by ID."""
        return AnalysisSession.query.filter_by(analysis_id=analysis_id).first()
    
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
    
    @staticmethod
    @BaseDAO.handle_db_error("get_session_analyses")
    def get_session_analyses(session_id: str) -> List[AnalysisSession]:
        """Get all analysis sessions for a user session."""
        return AnalysisSession.query.filter_by(session_id=session_id).order_by(AnalysisSession.started_at.desc()).all()

class StyleRuleDAO(BaseDAO):
    """DAO for style rule operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("create_rule")
    def create_rule(
        rule_id: str,
        rule_name: str,
        rule_category: str,
        description: str = None,
        severity = SeverityLevel.MEDIUM,
        configuration: Dict[str, Any] = None
    ) -> StyleRule:
        """Create a new style rule."""
        rule = StyleRule(
            rule_id=rule_id,
            rule_name=rule_name,
            rule_category=rule_category,
            description=description,
            severity=severity,
            configuration=configuration or {}
        )
        db.session.add(rule)
        db.session.commit()
        logger.info(f"Created style rule: {rule_id}")
        return rule
    
    @staticmethod
    @BaseDAO.handle_db_error("get_rule")
    def get_rule(rule_id: str) -> Optional[StyleRule]:
        """Get rule by ID."""
        return StyleRule.query.filter_by(rule_id=rule_id).first()
    
    @staticmethod
    @BaseDAO.handle_db_error("get_enabled_rules")
    def get_enabled_rules() -> List[StyleRule]:
        """Get all enabled rules."""
        return StyleRule.query.filter_by(is_enabled=True).all()
    
    @staticmethod
    @BaseDAO.handle_db_error("get_rules_by_category")
    def get_rules_by_category(category: str) -> List[StyleRule]:
        """Get rules by category."""
        return StyleRule.query.filter_by(rule_category=category, is_enabled=True).all()

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
                severity=SeverityLevel(violation_data.get('severity')) if violation_data.get('severity') else None,
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
    
    @staticmethod
    @BaseDAO.handle_db_error("get_violation")
    def get_violation(violation_id: str) -> Optional[RuleViolation]:
        """Get violation by ID."""
        return RuleViolation.query.filter_by(violation_id=violation_id).first()
    
    @staticmethod
    @BaseDAO.handle_db_error("get_rule_violations")
    def get_rule_violations(rule_id: str, limit: int = 100) -> List[RuleViolation]:
        """Get violations for a specific rule."""
        return RuleViolation.query.filter_by(rule_id=rule_id).limit(limit).all()

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
        return UserFeedback.query.filter_by(session_id=session_id).order_by(UserFeedback.timestamp.desc()).all()
    
    @staticmethod
    @BaseDAO.handle_db_error("get_violation_feedback")
    def get_violation_feedback(violation_id: str) -> List[UserFeedback]:
        """Get all feedback for a specific violation."""
        return UserFeedback.query.filter_by(violation_id=violation_id).all()
    
    @staticmethod
    @BaseDAO.handle_db_error("get_rule_feedback_stats")
    def get_rule_feedback_stats(rule_id: str) -> Dict[str, Any]:
        """Get feedback statistics for a rule."""
        # Join violations and feedback to get rule-specific feedback
        feedback_query = db.session.query(UserFeedback).join(
            RuleViolation, UserFeedback.violation_id == RuleViolation.violation_id
        ).filter(RuleViolation.rule_id == rule_id)
        
        feedback_list = feedback_query.all()
        
        if not feedback_list:
            return {'total': 0, 'correct': 0, 'incorrect': 0, 'partially_correct': 0, 'accuracy_rate': 0.0}
        
        total = len(feedback_list)
        correct = len([f for f in feedback_list if f.feedback_type == FeedbackType.CORRECT])
        incorrect = len([f for f in feedback_list if f.feedback_type == FeedbackType.INCORRECT])
        partially_correct = len([f for f in feedback_list if f.feedback_type == FeedbackType.PARTIALLY_CORRECT])
        
        return {
            'total': total,
            'correct': correct,
            'incorrect': incorrect,
            'partially_correct': partially_correct,
            'accuracy_rate': correct / total if total > 0 else 0.0
        }

class RewriteDAO(BaseDAO):
    """DAO for rewrite operations."""
    
    @staticmethod
    @BaseDAO.handle_db_error("create_rewrite_session")
    def create_rewrite_session(
        session_id: str,
        document_id: str,
        rewrite_type: str = "full_document",
        rewrite_mode: str = "comprehensive",
        model_provider: str = None,
        model_name: str = None,
        pass_number: int = 1,
        configuration: Dict[str, Any] = None
    ) -> RewriteSession:
        """Create a new rewrite session."""
        rewrite_session = RewriteSession(
            session_id=session_id,
            document_id=document_id,
            rewrite_id=BaseDAO.generate_id(),
            rewrite_type=RewriteType(rewrite_type),
            rewrite_mode=RewriteMode(rewrite_mode),
            model_provider=model_provider,
            model_name=model_name,
            pass_number=pass_number,
            status=ProcessingStatus.PENDING,
            configuration=configuration or {}
        )
        db.session.add(rewrite_session)
        db.session.commit()
        logger.info(f"Created rewrite session: {rewrite_session.rewrite_id}")
        return rewrite_session
    
    @staticmethod
    @BaseDAO.handle_db_error("store_rewrite_result")
    def store_rewrite_result(
        rewrite_id: str,
        original_text: str,
        rewritten_text: str,
        block_id: str = None,
        improvements_made: List[str] = None,
        quality_score: float = None,
        processing_time: float = None,
        tokens_used: int = None,
        readability_before: float = None,
        readability_after: float = None
    ) -> RewriteResult:
        """Store rewrite result."""
        result = RewriteResult(
            rewrite_id=rewrite_id,
            block_id=block_id,
            result_id=BaseDAO.generate_id(),
            original_text=original_text,
            rewritten_text=rewritten_text,
            improvements_made=improvements_made or [],
            quality_score=quality_score,
            processing_time=processing_time,
            tokens_used=tokens_used,
            readability_before=readability_before,
            readability_after=readability_after
        )
        db.session.add(result)
        db.session.commit()
        logger.info(f"Stored rewrite result: {result.result_id}")
        return result
    
    @staticmethod
    @BaseDAO.handle_db_error("update_rewrite_session")
    def update_rewrite_session(
        rewrite_id: str,
        status: ProcessingStatus,
        processing_time: float = None,
        tokens_used: int = None
    ) -> bool:
        """Update rewrite session status."""
        rewrite_session = RewriteSession.query.filter_by(rewrite_id=rewrite_id).first()
        if rewrite_session:
            rewrite_session.status = status
            if status == ProcessingStatus.COMPLETED:
                rewrite_session.completed_at = datetime.utcnow()
            if processing_time is not None:
                rewrite_session.total_processing_time = processing_time
            if tokens_used is not None:
                rewrite_session.tokens_used = tokens_used
            
            db.session.commit()
            return True
        return False
    
    @staticmethod
    @BaseDAO.handle_db_error("get_rewrite_results")
    def get_rewrite_results(rewrite_id: str) -> List[RewriteResult]:
        """Get all results for a rewrite session."""
        return RewriteResult.query.filter_by(rewrite_id=rewrite_id).all()

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
    
    @staticmethod
    @BaseDAO.handle_db_error("get_metrics")
    def get_metrics(
        metric_type: str = None,
        session_id: str = None,
        hours_back: int = 24,
        limit: int = 1000
    ) -> List[PerformanceMetric]:
        """Get performance metrics with filters."""
        query = PerformanceMetric.query
        
        if metric_type:
            query = query.filter_by(metric_type=metric_type)
        if session_id:
            query = query.filter_by(session_id=session_id)
        
        # Filter by time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
        query = query.filter(PerformanceMetric.recorded_at >= cutoff_time)
        
        return query.order_by(PerformanceMetric.recorded_at.desc()).limit(limit).all()

class ModelUsageDAO(BaseDAO):
    """DAO for model usage tracking."""
    
    @staticmethod
    @BaseDAO.handle_db_error("log_model_usage")
    def log_model_usage(
        session_id: str,
        operation_type: str,
        model_provider: str = None,
        model_name: str = None,
        tokens_used: int = None,
        processing_time_ms: int = None,
        cost_estimate: float = None,
        success: bool = True,
        error_message: str = None
    ) -> ModelUsageLog:
        """Log model usage."""
        log_entry = ModelUsageLog(
            log_id=BaseDAO.generate_id(),
            session_id=session_id,
            operation_type=OperationType(operation_type),
            model_provider=model_provider,
            model_name=model_name,
            tokens_used=tokens_used,
            processing_time_ms=processing_time_ms,
            cost_estimate=cost_estimate,
            success=success,
            error_message=error_message
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    @staticmethod
    @BaseDAO.handle_db_error("get_usage_stats")
    def get_usage_stats(
        session_id: str = None,
        operation_type: str = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get model usage statistics."""
        query = ModelUsageLog.query
        
        if session_id:
            query = query.filter_by(session_id=session_id)
        if operation_type:
            query = query.filter_by(operation_type=OperationType(operation_type))
        
        # Filter by time
        cutoff_time = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(ModelUsageLog.timestamp >= cutoff_time)
        
        logs = query.all()
        
        if not logs:
            return {'total_operations': 0, 'total_tokens': 0, 'total_cost': 0.0, 'success_rate': 0.0}
        
        total_operations = len(logs)
        total_tokens = sum(log.tokens_used or 0 for log in logs)
        total_cost = sum(log.cost_estimate or 0.0 for log in logs)
        successful_operations = len([log for log in logs if log.success])
        success_rate = successful_operations / total_operations if total_operations > 0 else 0.0
        
        return {
            'total_operations': total_operations,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'success_rate': success_rate,
            'successful_operations': successful_operations,
            'failed_operations': total_operations - successful_operations
        }
