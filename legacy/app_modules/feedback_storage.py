"""
Feedback Storage Module
Handles storage, validation, and aggregation of user feedback on error accuracy
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class FeedbackEntry:
    """Represents a single feedback entry"""
    feedback_id: str
    session_id: str
    error_id: str
    error_type: str
    error_message: str
    error_text: str 
    context_before: Optional[str]
    context_after: Optional[str]
    feedback_type: str
    confidence_score: float
    user_reason: Optional[str]
    timestamp: str
    user_agent: Optional[str]
    ip_hash: Optional[str]  # Hashed for privacy
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeedbackEntry':
        """Create from dictionary"""
        return cls(**data)


class FeedbackStorage:
    """Manages feedback storage and aggregation"""
    
    def __init__(self, storage_dir: str = "feedback_data"):
        """Initialize feedback storage"""
        self.storage_dir = storage_dir
        self.session_storage = {}  # In-memory session storage
        self.ensure_storage_directory()
    
    def ensure_storage_directory(self):
        """Ensure storage directory exists"""
        try:
            os.makedirs(self.storage_dir, exist_ok=True)
            # Create subdirectories for organization
            os.makedirs(os.path.join(self.storage_dir, "sessions"), exist_ok=True)
            os.makedirs(os.path.join(self.storage_dir, "daily"), exist_ok=True)
            os.makedirs(os.path.join(self.storage_dir, "aggregated"), exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create feedback storage directory: {e}")
    
    def generate_feedback_id(self, session_id: str, error_id: str) -> str:
        """Generate unique feedback ID"""
        timestamp = str(int(time.time() * 1000))  # Milliseconds
        data = f"{session_id}:{error_id}:{timestamp}"
        return hashlib.md5(data.encode()).hexdigest()[:12]
    
    def hash_ip(self, ip_address: str) -> str:
        """Hash IP address for privacy"""
        if not ip_address:
            return None
        salt = "feedback_privacy_salt_2024"
        return hashlib.sha256(f"{salt}:{ip_address}".encode()).hexdigest()[:16]
    
    def validate_feedback_data(self, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate feedback submission data"""
        required_fields = ['session_id', 'error_id', 'error_type', 'error_message', 'error_text', 'feedback_type']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                return False, f"Missing required field: {field}"
        
        # Validate feedback type
        valid_feedback_types = ['correct', 'incorrect', 'partially_correct']
        if data['feedback_type'] not in valid_feedback_types:
            return False, f"Invalid feedback_type. Must be one of: {', '.join(valid_feedback_types)}"
        
        # Validate confidence score
        confidence_score = data.get('confidence_score')
        if confidence_score is not None:
            try:
                confidence_score = float(confidence_score)
                if not 0.0 <= confidence_score <= 1.0:
                    return False, "confidence_score must be between 0.0 and 1.0"
            except (ValueError, TypeError):
                return False, "confidence_score must be a valid number"
        
        # Validate session_id format
        session_id = data['session_id']
        if not isinstance(session_id, str) or len(session_id) < 1:
            return False, "session_id must be a non-empty string"
        
        # Validate error_id format  
        error_id = data['error_id']
        if not isinstance(error_id, str) or len(error_id) < 1:
            return False, "error_id must be a non-empty string"
        
        # Validate user_reason length if provided
        user_reason = data.get('user_reason', '')
        if user_reason and len(user_reason) > 1000:
            return False, "user_reason must be 1000 characters or less"
        
        return True, "Valid"
    
    def store_feedback(self, feedback_data: Dict[str, Any], 
                      user_agent: Optional[str] = None,
                      ip_address: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Store feedback entry"""
        try:
            # Validate input data
            is_valid, validation_message = self.validate_feedback_data(feedback_data)
            if not is_valid:
                return False, validation_message, None
            
            # Generate feedback ID
            feedback_id = self.generate_feedback_id(
                feedback_data['session_id'], 
                feedback_data['error_id']
            )
            
            # Create feedback entry
            feedback_entry = FeedbackEntry(
                feedback_id=feedback_id,
                session_id=feedback_data['session_id'],
                error_id=feedback_data['error_id'],
                error_type=feedback_data['error_type'],
                error_message=feedback_data['error_message'],
                error_text=feedback_data['error_text'],
                context_before=feedback_data.get('context_before'),
                context_after=feedback_data.get('context_after'),
                feedback_type=feedback_data['feedback_type'],
                confidence_score=feedback_data.get('confidence_score', 0.5),
                user_reason=feedback_data.get('user_reason'),
                timestamp=datetime.now().isoformat(),
                user_agent=user_agent,
                ip_hash=self.hash_ip(ip_address)
            )
            
            # Store in session storage
            session_id = feedback_data['session_id']
            if session_id not in self.session_storage:
                self.session_storage[session_id] = []
            self.session_storage[session_id].append(feedback_entry)
            
            # Store to disk (daily file)
            self._store_to_daily_file(feedback_entry)
            
            logger.info(f"Feedback stored successfully: {feedback_id}")
            return True, "Feedback stored successfully", feedback_id
            
        except Exception as e:
            logger.error(f"Failed to store feedback: {e}")
            return False, f"Storage error: {str(e)}", None
    
    def _store_to_daily_file(self, feedback_entry: FeedbackEntry):
        """Store feedback to daily file for persistence"""
        try:
            date_str = datetime.now().strftime('%Y-%m-%d')
            daily_file = os.path.join(self.storage_dir, "daily", f"feedback_{date_str}.jsonl")
            
            with open(daily_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(feedback_entry.to_dict()) + '\n')
                
        except Exception as e:
            logger.error(f"Failed to store feedback to daily file: {e}")
    
    def get_session_feedback(self, session_id: str) -> List[FeedbackEntry]:
        """Get all feedback for a session"""
        return self.session_storage.get(session_id, [])
    
    def get_feedback_stats(self, session_id: Optional[str] = None, 
                          days_back: int = 7) -> Dict[str, Any]:
        """Get feedback statistics"""
        try:
            if session_id:
                # Session-specific stats
                feedback_entries = self.get_session_feedback(session_id)
            else:
                # Overall stats from recent days
                feedback_entries = self._load_recent_feedback(days_back)
            
            if not feedback_entries:
                return {
                    'total_feedback': 0,
                    'feedback_distribution': {},
                    'confidence_analysis': {},
                    'error_type_analysis': {},
                    'session_id': session_id
                }
            
            # Calculate statistics
            total_feedback = len(feedback_entries)
            feedback_distribution = Counter(entry.feedback_type for entry in feedback_entries)
            
            # Confidence analysis
            confidence_scores = [entry.confidence_score for entry in feedback_entries if entry.confidence_score is not None]
            confidence_analysis = {}
            if confidence_scores:
                confidence_analysis = {
                    'average_confidence': sum(confidence_scores) / len(confidence_scores),
                    'min_confidence': min(confidence_scores),
                    'max_confidence': max(confidence_scores),
                    'confidence_distribution': {
                        'high_confidence': len([c for c in confidence_scores if c >= 0.7]),
                        'medium_confidence': len([c for c in confidence_scores if 0.5 <= c < 0.7]),
                        'low_confidence': len([c for c in confidence_scores if c < 0.5])
                    }
                }
            
            # Error type analysis
            error_type_feedback = defaultdict(lambda: defaultdict(int))
            for entry in feedback_entries:
                error_type_feedback[entry.error_type][entry.feedback_type] += 1
            
            return {
                'total_feedback': total_feedback,
                'feedback_distribution': dict(feedback_distribution),
                'confidence_analysis': confidence_analysis,
                'error_type_analysis': dict(error_type_feedback),
                'session_id': session_id,
                'data_period_days': days_back if not session_id else None
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate feedback stats: {e}")
            return {'error': str(e)}
    
    def _load_recent_feedback(self, days_back: int) -> List[FeedbackEntry]:
        """Load feedback from recent days"""
        feedback_entries = []
        
        try:
            # Load from session storage (current session)
            for session_feedback in self.session_storage.values():
                feedback_entries.extend(session_feedback)
            
            # Load from daily files
            for days_ago in range(days_back):
                date = datetime.now() - timedelta(days=days_ago)
                date_str = date.strftime('%Y-%m-%d')
                daily_file = os.path.join(self.storage_dir, "daily", f"feedback_{date_str}.jsonl")
                
                if os.path.exists(daily_file):
                    with open(daily_file, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    data = json.loads(line)
                                    feedback_entries.append(FeedbackEntry.from_dict(data))
                                except json.JSONDecodeError:
                                    continue
                                    
        except Exception as e:
            logger.error(f"Failed to load recent feedback: {e}")
        
        return feedback_entries
    
    def aggregate_feedback_insights(self, days_back: int = 30) -> Dict[str, Any]:
        """Generate aggregated insights from feedback data"""
        try:
            feedback_entries = self._load_recent_feedback(days_back)
            
            if not feedback_entries:
                return {'message': 'No feedback data available for analysis'}
            
            insights = {
                'summary': {
                    'total_feedback_entries': len(feedback_entries),
                    'unique_sessions': len(set(entry.session_id for entry in feedback_entries)),
                    'analysis_period_days': days_back
                },
                'accuracy_insights': self._calculate_accuracy_insights(feedback_entries),
                'confidence_insights': self._calculate_confidence_insights(feedback_entries),
                'error_type_insights': self._calculate_error_type_insights(feedback_entries),
                'temporal_patterns': self._calculate_temporal_patterns(feedback_entries)
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Failed to generate feedback insights: {e}")
            return {'error': str(e)}
    
    def _calculate_accuracy_insights(self, feedback_entries: List[FeedbackEntry]) -> Dict[str, Any]:
        """Calculate accuracy-related insights"""
        total = len(feedback_entries)
        correct = len([e for e in feedback_entries if e.feedback_type == 'correct'])
        incorrect = len([e for e in feedback_entries if e.feedback_type == 'incorrect'])
        partially_correct = len([e for e in feedback_entries if e.feedback_type == 'partially_correct'])
        
        return {
            'overall_accuracy_rate': correct / total if total > 0 else 0,
            'false_positive_rate': incorrect / total if total > 0 else 0,
            'partial_accuracy_rate': partially_correct / total if total > 0 else 0,
            'feedback_distribution': {
                'correct': correct,
                'incorrect': incorrect,
                'partially_correct': partially_correct
            }
        }
    
    def _calculate_confidence_insights(self, feedback_entries: List[FeedbackEntry]) -> Dict[str, Any]:
        """Calculate confidence-related insights"""
        confidence_scores = [e.confidence_score for e in feedback_entries if e.confidence_score is not None]
        
        if not confidence_scores:
            return {'message': 'No confidence data available'}
        
        # Analyze accuracy by confidence level
        high_conf_entries = [e for e in feedback_entries if e.confidence_score >= 0.7]
        medium_conf_entries = [e for e in feedback_entries if 0.5 <= e.confidence_score < 0.7]
        low_conf_entries = [e for e in feedback_entries if e.confidence_score < 0.5]
        
        def accuracy_for_entries(entries):
            if not entries:
                return 0
            correct = len([e for e in entries if e.feedback_type == 'correct'])
            return correct / len(entries)
        
        return {
            'average_confidence': sum(confidence_scores) / len(confidence_scores),
            'confidence_accuracy_correlation': {
                'high_confidence_accuracy': accuracy_for_entries(high_conf_entries),
                'medium_confidence_accuracy': accuracy_for_entries(medium_conf_entries),
                'low_confidence_accuracy': accuracy_for_entries(low_conf_entries)
            },
            'confidence_distribution': {
                'high_confidence_count': len(high_conf_entries),
                'medium_confidence_count': len(medium_conf_entries),
                'low_confidence_count': len(low_conf_entries)
            }
        }
    
    def _calculate_error_type_insights(self, feedback_entries: List[FeedbackEntry]) -> Dict[str, Any]:
        """Calculate error type insights"""
        error_type_stats = defaultdict(lambda: {'total': 0, 'correct': 0, 'incorrect': 0, 'partially_correct': 0})
        
        for entry in feedback_entries:
            error_type_stats[entry.error_type]['total'] += 1
            error_type_stats[entry.error_type][entry.feedback_type] += 1
        
        # Calculate accuracy rates by error type
        accuracy_by_type = {}
        for error_type, stats in error_type_stats.items():
            total = stats['total']
            accuracy_rate = stats['correct'] / total if total > 0 else 0
            accuracy_by_type[error_type] = {
                'accuracy_rate': accuracy_rate,
                'total_feedback': total,
                'distribution': {
                    'correct': stats['correct'],
                    'incorrect': stats['incorrect'],
                    'partially_correct': stats['partially_correct']
                }
            }
        
        return accuracy_by_type
    
    def _calculate_temporal_patterns(self, feedback_entries: List[FeedbackEntry]) -> Dict[str, Any]:
        """Calculate temporal patterns in feedback"""
        try:
            # Group by date
            date_groups = defaultdict(list)
            for entry in feedback_entries:
                entry_date = entry.timestamp[:10]  # Extract YYYY-MM-DD
                date_groups[entry_date].append(entry)
            
            daily_stats = {}
            for date, entries in date_groups.items():
                total = len(entries)
                correct = len([e for e in entries if e.feedback_type == 'correct'])
                daily_stats[date] = {
                    'total_feedback': total,
                    'accuracy_rate': correct / total if total > 0 else 0
                }
            
            return {
                'daily_statistics': daily_stats,
                'total_days_with_feedback': len(daily_stats)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate temporal patterns: {e}")
            return {'error': str(e)}


# Global feedback storage instance
feedback_storage = FeedbackStorage()