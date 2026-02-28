"""
Service layer for database operations
Provides business logic and integrates with existing services.
"""

import logging
import time
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone

from database import db
from database.dao import (
    SessionDAO, DocumentDAO, BlockDAO, AnalysisDAO, StyleRuleDAO,
    ViolationDAO, FeedbackDAO, PerformanceDAO
)
from database.models import ProcessingStatus

logger = logging.getLogger(__name__)

class DatabaseService:
    """Main service for database operations."""
    
    def __init__(self):
        self.session_dao = SessionDAO()
        self.document_dao = DocumentDAO()
        self.block_dao = BlockDAO()
        self.analysis_dao = AnalysisDAO()
        self.style_rule_dao = StyleRuleDAO()
        self.violation_dao = ViolationDAO()
        self.feedback_dao = FeedbackDAO()
        self.performance_dao = PerformanceDAO()
    
    def create_user_session(self, user_agent: str = None, ip_address: str = None) -> str:
        """Create a new user session and return session ID."""
        # Hash IP for privacy
        ip_hash = self._hash_ip(ip_address) if ip_address else None
        
        session = self.session_dao.create_session(user_agent=user_agent, ip_hash=ip_hash)
        return session.session_id
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        session = self.session_dao.get_session(session_id)
        if not session:
            return None
        
        return {
            'session_id': session.session_id,
            'status': session.status.value,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'user_agent': session.user_agent
        }
    
    def process_document_upload(
        self, 
        session_id: str, 
        content: str, 
        filename: str = None,
        content_type: str = None,
        document_format: str = None,
        blocks: List[Dict[str, Any]] = None
    ) -> Tuple[str, str]:  # Returns (document_id, analysis_id)
        """Process document upload and create initial analysis session."""
        
        # Store document
        document = self.document_dao.store_document(
            session_id=session_id,
            filename=filename,
            content=content,
            content_type=content_type,
            document_format=document_format,
            file_size=len(content.encode('utf-8'))
        )
        
        # Store blocks if provided
        if blocks:
            self.block_dao.store_blocks(document.document_id, blocks)
        
        # Create initial analysis session
        analysis = self.analysis_dao.create_analysis_session(
            session_id=session_id,
            document_id=document.document_id,
            content_type=content_type
        )
        
        logger.info(f"Processed document upload: doc={document.document_id}, analysis={analysis.analysis_id}")
        return document.document_id, analysis.analysis_id
    
    def start_analysis(self, analysis_id: str) -> bool:
        """Mark analysis as started."""
        return self.analysis_dao.update_analysis_status(
            analysis_id=analysis_id,
            status=ProcessingStatus.PROCESSING
        )
    
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
        
        logger.info(f"Stored {len(stored_violations)} violations for analysis {analysis_id}")
        return success
    
    def get_analysis_results(self, analysis_id: str) -> Dict[str, Any]:
        """Get complete analysis results."""
        analysis = self.analysis_dao.get_analysis_session(analysis_id)
        if not analysis:
            return {'error': 'Analysis not found'}
        
        violations = self.violation_dao.get_analysis_violations(analysis_id)
        
        # Convert to format expected by frontend
        results = {
            'analysis_id': analysis_id,
            'status': analysis.status.value,
            'started_at': analysis.started_at.isoformat(),
            'completed_at': analysis.completed_at.isoformat() if analysis.completed_at else None,
            'total_processing_time': analysis.total_processing_time,
            'total_errors_found': analysis.total_errors_found,
            'total_blocks_analyzed': analysis.total_blocks_analyzed,
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
                    'context_after': v.context_after,
                    'block_id': v.block_id
                }
                for v in violations
            ]
        }
        
        return results
    
    def store_user_feedback(
        self,
        session_id: str,
        violation_id: str,
        feedback_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Store or update user feedback."""
        try:
            # Use update_feedback which handles both update and create cases
            feedback = self.feedback_dao.update_feedback(
                session_id=session_id,
                violation_id=violation_id,
                feedback_data=feedback_data
            )
            
            logger.info(f"Stored/updated feedback: {feedback.feedback_id} for violation: {violation_id}")
            return True, feedback.feedback_id
        except Exception as e:
            logger.error(f"Failed to store/update feedback: {e}")
            return False, str(e)
    
    def get_existing_feedback(
        self,
        session_id: str,
        violation_id: str
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Get existing feedback for a session and violation."""
        try:
            feedback = self.feedback_dao.get_existing_feedback(session_id, violation_id)
            if feedback:
                violation = feedback.violation if hasattr(feedback, 'violation') else None
                
                feedback_data = {
                    'feedback_id': feedback.feedback_id,
                    'session_id': feedback.session_id,
                    'violation_id': feedback.violation_id,
                    'error_type': feedback.error_type,
                    'error_message': feedback.error_message,
                    'error_text': violation.error_text if violation else '',
                    'context_before': violation.context_before if violation else None,
                    'context_after': violation.context_after if violation else None,
                    'feedback_type': feedback.feedback_type.value,
                    'confidence_score': feedback.confidence_score,
                    'user_reason': feedback.user_reason,
                    'timestamp': feedback.timestamp.isoformat()
                }
                return True, feedback_data
            else:
                return True, None
                
        except Exception as e:
            logger.error(f"Failed to get existing feedback: {e}")
            return False, None
            
    def delete_user_feedback(
        self,
        session_id: str,
        violation_id: str
    ) -> Tuple[bool, str]:
        """Delete user feedback."""
        try:
            success = self.feedback_dao.delete_feedback(session_id, violation_id)
            
            if success:
                logger.info(f"Deleted feedback for session: {session_id}, violation: {violation_id}")
                return True, "Feedback deleted successfully"
            else:
                return False, "No feedback found to delete"
                
        except Exception as e:
            logger.error(f"Failed to delete feedback: {e}")
            return False, str(e)
    
    def get_session_analytics(self, session_id: str) -> Dict[str, Any]:
        """Get analytics for a session."""
        session = self.session_dao.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        documents = self.document_dao.get_session_documents(session_id)
        analyses = self.analysis_dao.get_session_analyses(session_id)
        feedback_entries = self.feedback_dao.get_session_feedback(session_id)
        
        # Calculate total violations
        total_violations = 0
        for analysis in analyses:
            total_violations += analysis.total_errors_found or 0
        
        return {
            'session_id': session_id,
            'session_status': session.status.value,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'total_documents': len(documents),
            'total_analyses': len(analyses),
            'total_violations': total_violations,
            'total_feedback': len(feedback_entries),
            'feedback_breakdown': self._analyze_feedback(feedback_entries),
            'document_summary': [
                {
                    'document_id': doc.document_id,
                    'filename': doc.filename,
                    'format': doc.document_format,
                    'created_at': doc.created_at.isoformat(),
                    'status': doc.processing_status.value
                }
                for doc in documents
            ]
        }
    
    def get_rule_performance(self, rule_id: str = None, days_back: int = 30) -> Dict[str, Any]:
        """Get rule performance analytics."""
        if rule_id:
            rule = self.style_rule_dao.get_rule(rule_id)
            if not rule:
                return {'error': f'Rule {rule_id} not found'}
            
            feedback_stats = self.feedback_dao.get_rule_feedback_stats(rule_id)
            violations = self.violation_dao.get_rule_violations(rule_id, limit=1000)
            
            # Calculate confidence distribution
            confidence_scores = [v.confidence_score for v in violations if v.confidence_score is not None]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
            
            return {
                'rule_id': rule_id,
                'rule_name': rule.rule_name,
                'rule_category': rule.rule_category,
                'total_violations': len(violations),
                'average_confidence': avg_confidence,
                'feedback_stats': feedback_stats,
                'is_enabled': rule.is_enabled
            }
        else:
            # Return performance for all rules
            rules = self.style_rule_dao.get_enabled_rules()
            rule_performances = []
            
            for rule in rules:
                feedback_stats = self.feedback_dao.get_rule_feedback_stats(rule.rule_id)
                violations = self.violation_dao.get_rule_violations(rule.rule_id, limit=100)
                
                rule_performances.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'rule_category': rule.rule_category,
                    'total_violations': len(violations),
                    'feedback_stats': feedback_stats
                })
            
            return {'rules': rule_performances}

    def get_rule_accuracy_report(self) -> Dict[str, Any]:
        """Get per-rule accuracy report with false positive rates and actionable flags.

        Returns a report identifying rules that need attention based on user feedback,
        sorted by false positive rate (worst offenders first).
        """
        summary = self.feedback_dao.get_rule_feedback_summary()

        # Aggregate feedback counts per rule
        rule_stats = {}
        for entry in summary:
            rule_id = entry['rule_id']
            if rule_id not in rule_stats:
                rule_stats[rule_id] = {'correct': 0, 'incorrect': 0, 'partially_correct': 0}

            feedback_type = entry.get('feedback_type')
            count = entry.get('count', 0)
            if feedback_type == 'correct':
                rule_stats[rule_id]['correct'] += count
            elif feedback_type == 'incorrect':
                rule_stats[rule_id]['incorrect'] += count
            elif feedback_type == 'partially_correct':
                rule_stats[rule_id]['partially_correct'] += count

        # Build per-rule accuracy entries
        rules_accuracy = []
        for rule_id, stats in rule_stats.items():
            total = stats['correct'] + stats['incorrect'] + stats['partially_correct']
            false_positive_rate = stats['incorrect'] / total if total > 0 else 0.0
            accuracy_rate = stats['correct'] / total if total > 0 else 0.0

            # Flag rules that exceed 5% false positive threshold
            needs_attention = false_positive_rate > 0.05 and total >= 3

            rules_accuracy.append({
                'rule_id': rule_id,
                'total_feedback': total,
                'correct': stats['correct'],
                'incorrect': stats['incorrect'],
                'partially_correct': stats['partially_correct'],
                'accuracy_rate': round(accuracy_rate, 4),
                'false_positive_rate': round(false_positive_rate, 4),
                'needs_attention': needs_attention
            })

        # Sort by false positive rate descending (worst offenders first)
        rules_accuracy.sort(key=lambda x: x['false_positive_rate'], reverse=True)

        # Calculate overall stats
        total_feedback = sum(r['total_feedback'] for r in rules_accuracy)
        total_incorrect = sum(r['incorrect'] for r in rules_accuracy)
        overall_false_positive_rate = total_incorrect / total_feedback if total_feedback > 0 else 0.0

        return {
            'overall': {
                'total_feedback': total_feedback,
                'total_incorrect': total_incorrect,
                'false_positive_rate': round(overall_false_positive_rate, 4),
                'rules_needing_attention': sum(1 for r in rules_accuracy if r['needs_attention'])
            },
            'rules': rules_accuracy
        }

    def get_model_usage_stats(
        self,
        session_id: str = None,
        operation_type: str = None,
        days_back: int = 30
    ) -> Dict[str, Any]:
        """Get model usage statistics."""
        return {'total_operations': 0, 'total_tokens': 0, 'avg_processing_time_ms': 0.0, 'success_rate': 1.0}

    def cleanup_expired_sessions(self, hours_old: int = 24) -> Dict[str, int]:
        """Clean up old sessions and related data."""
        expired_count = self.session_dao.cleanup_expired_sessions(hours_old)
        
        # Could add cleanup of related data here in the future
        # For now, we rely on cascade deletes
        
        return {
            'expired_sessions': expired_count,
            'hours_threshold': hours_old
        }
    
    def initialize_default_rules(self) -> int:
        """Initialize all 98 style rules from the rules registry in the database."""
        from database.models import SeverityLevel
        
        # Dynamically load all rules from the rules registry
        try:
            from rules import get_registry
            registry = get_registry()  # Uses shared singleton — must keep consolidation enabled
            
            default_rules = []
            for rule_type, rule_instance in registry.rules.items():
                # Get category from rule location
                location = registry.rule_locations.get(rule_type, 'general')
                category = 'general'
                if '(' in location and ')' in location:
                    category = location.split('(')[1].split(')')[0]
                
                # Create human-readable name
                rule_name = rule_type.replace('_', ' ').title()
                
                # Determine severity based on rule type and category
                severity = SeverityLevel.MEDIUM  # Default
                
                # High severity rules
                if any(keyword in rule_type.lower() for keyword in ['spelling', 'anthropomorphism', 'legal', 'compliance']):
                    severity = SeverityLevel.HIGH
                # Low severity rules
                elif any(keyword in rule_type.lower() for keyword in ['sentence_length', 'oxford_comma', 'word_usage', 'conversational']):
                    severity = SeverityLevel.LOW
                # Everything else stays MEDIUM
                
                default_rules.append({
                    'rule_id': rule_type,
                    'rule_name': rule_name,
                    'rule_category': category,
                    'description': f'Analyzes {rule_name.lower()} compliance and style',
                    'severity': severity
                })
            
            print(f"🔧 Preparing to create {len(default_rules)} rule records from rules registry")
            
        except Exception as e:
            print(f"⚠️ Could not load rules registry: {e}")
            print("🔧 Falling back to basic rule set...")
            # Fallback to the original 5 rules if registry fails
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
                {
                    'rule_id': 'second_person',
                    'rule_name': 'Second Person Usage',
                    'rule_category': 'language',
                    'description': 'Detects inappropriate second person usage',
                    'severity': SeverityLevel.MEDIUM
                },
                {
                    'rule_id': 'oxford_comma',
                    'rule_name': 'Oxford Comma',
                    'rule_category': 'punctuation',
                    'description': 'Checks for missing Oxford commas',
                    'severity': SeverityLevel.LOW
                }
            ]
        
        created_count = 0
        for rule_data in default_rules:
            existing_rule = self.style_rule_dao.get_rule(rule_data['rule_id'])
            if not existing_rule:
                self.style_rule_dao.create_rule(**rule_data)
                created_count += 1
        
        logger.info(f"Initialized {created_count} default rules")
        return created_count
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics."""
        try:
            recent_metrics = self.performance_dao.get_metrics(hours_back=1, limit=100)
            active_sessions = self.session_dao.get_active_sessions(limit=10)

            analysis_times = [m.metric_value for m in recent_metrics if m.metric_name == 'total_analysis_time']
            avg_analysis_time = sum(analysis_times) / len(analysis_times) if analysis_times else 0.0

            return {
                'status': 'healthy',
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'active_sessions': len(active_sessions),
                'recent_metrics_count': len(recent_metrics),
                'average_analysis_time': avg_analysis_time,
                'database_connection': True
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
    
    def _hash_ip(self, ip_address: str) -> str:
        """Hash IP address for privacy."""
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
