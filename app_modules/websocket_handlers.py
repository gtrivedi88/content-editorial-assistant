"""
WebSocket Handlers Module
Handles real-time communication for progress updates and notifications.
Provides real-time feedback during analysis and rewriting operations.
"""

import logging
import uuid
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from threading import Lock
import threading

logger = logging.getLogger(__name__)

# Store active sessions
active_sessions = set()

# Store socketio instance for use in emit functions
_socketio = None

# Performance monitoring data structures
_performance_metrics = {
    'block_processing_times': deque(maxlen=1000),  # Last 1000 processing times
    'error_rates': defaultdict(lambda: deque(maxlen=100)),  # Error rates by type
    'websocket_events': defaultdict(int),  # Event counts
    'session_metrics': defaultdict(dict),  # Per-session metrics
    'total_blocks_processed': 0,
    'total_errors': 0,
    'uptime_start': datetime.now()
}

# Thread-safe lock for metrics
_metrics_lock = Lock()

# Error rate tracking
_error_tracking = {
    'recent_errors': deque(maxlen=1000),  # Recent errors with timestamps
    'error_window_minutes': 15,  # Default error rate window
    'error_threshold': 0.05  # 5% error rate threshold
}


def set_socketio(socketio):
    """Set the SocketIO instance for use in emit functions."""
    global _socketio
    _socketio = socketio


# Performance Monitoring Functions

def record_block_processing_time(block_id: str, processing_time: float, success: bool):
    """Record block processing time and outcome for performance metrics."""
    with _metrics_lock:
        _performance_metrics['block_processing_times'].append({
            'block_id': block_id,
            'processing_time': processing_time,
            'success': success,
            'timestamp': datetime.now()
        })
        
        if success:
            _performance_metrics['total_blocks_processed'] += 1
        else:
            _performance_metrics['total_errors'] += 1
            
        logger.debug(f"Recorded block processing: {block_id}, {processing_time:.2f}s, success={success}")


def record_websocket_event(event_type: str, session_id: Optional[str] = None):
    """Record WebSocket event for monitoring."""
    with _metrics_lock:
        _performance_metrics['websocket_events'][event_type] += 1
        
        if session_id:
            if session_id not in _performance_metrics['session_metrics']:
                _performance_metrics['session_metrics'][session_id] = {
                    'events': defaultdict(int),
                    'first_seen': datetime.now(),
                    'last_activity': datetime.now()
                }
            
            _performance_metrics['session_metrics'][session_id]['events'][event_type] += 1
            _performance_metrics['session_metrics'][session_id]['last_activity'] = datetime.now()


def record_error(error_type: str, error_message: str, session_id: Optional[str] = None):
    """Record error for error rate monitoring."""
    with _metrics_lock:
        error_entry = {
            'error_type': error_type,
            'error_message': error_message,
            'session_id': session_id,
            'timestamp': datetime.now()
        }
        
        _error_tracking['recent_errors'].append(error_entry)
        _performance_metrics['error_rates'][error_type].append(datetime.now())
        
        logger.warning(f"Recorded error: {error_type} - {error_message}")


def get_error_rate(error_type: Optional[str] = None, window_minutes: int = None) -> float:
    """Calculate error rate within specified time window."""
    if window_minutes is None:
        window_minutes = _error_tracking['error_window_minutes']
    
    cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
    
    with _metrics_lock:
        if error_type:
            # Get error rate for specific error type
            recent_errors = [
                err for err in _performance_metrics['error_rates'][error_type]
                if err >= cutoff_time
            ]
            total_operations = len([
                pt for pt in _performance_metrics['block_processing_times']
                if pt['timestamp'] >= cutoff_time
            ])
        else:
            # Get overall error rate
            recent_errors = [
                err for err in _error_tracking['recent_errors']
                if err['timestamp'] >= cutoff_time
            ]
            total_operations = len([
                pt for pt in _performance_metrics['block_processing_times']
                if pt['timestamp'] >= cutoff_time
            ])
    
    if total_operations == 0:
        return 0.0
    
    return len(recent_errors) / total_operations


def check_error_rate_threshold() -> Dict[str, Any]:
    """Check if error rate exceeds threshold and return alert data."""
    current_error_rate = get_error_rate()
    threshold = _error_tracking['error_threshold']
    
    alert_data = {
        'error_rate_exceeded': current_error_rate > threshold,
        'current_rate': current_error_rate,
        'threshold': threshold,
        'window_minutes': _error_tracking['error_window_minutes'],
        'timestamp': datetime.now().isoformat()
    }
    
    if alert_data['error_rate_exceeded']:
        logger.warning(f"Error rate threshold exceeded: {current_error_rate:.2%} > {threshold:.2%}")
    
    return alert_data


def get_performance_summary() -> Dict[str, Any]:
    """Get comprehensive performance summary."""
    with _metrics_lock:
        current_time = datetime.now()
        uptime = current_time - _performance_metrics['uptime_start']
        
        # Calculate average processing time
        processing_times = [pt['processing_time'] for pt in _performance_metrics['block_processing_times']]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Calculate success rate
        successful_blocks = sum(1 for pt in _performance_metrics['block_processing_times'] if pt['success'])
        total_attempts = len(_performance_metrics['block_processing_times'])
        success_rate = successful_blocks / total_attempts if total_attempts > 0 else 1.0
        
        # Get active sessions info
        active_session_count = len(active_sessions)
        
        # Calculate error rate within the same lock to avoid deadlock
        cutoff_time = current_time - timedelta(minutes=_error_tracking['error_window_minutes'])
        recent_errors = [
            err for err in _error_tracking['recent_errors']
            if err['timestamp'] >= cutoff_time
        ]
        total_operations = len([
            pt for pt in _performance_metrics['block_processing_times']
            if pt['timestamp'] >= cutoff_time
        ])
        current_error_rate = len(recent_errors) / total_operations if total_operations > 0 else 0.0
        
        # Check error rate threshold within the same lock
        threshold = _error_tracking['error_threshold']
        error_rate_exceeded = current_error_rate > threshold
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime),
            'total_blocks_processed': _performance_metrics['total_blocks_processed'],
            'total_errors': _performance_metrics['total_errors'],
            'average_processing_time': avg_processing_time,
            'success_rate': success_rate,
            'current_error_rate': current_error_rate,
            'active_sessions': active_session_count,
            'websocket_events': dict(_performance_metrics['websocket_events']),
            'error_rate_status': {
                'error_rate_exceeded': error_rate_exceeded,
                'current_rate': current_error_rate,
                'threshold': threshold,
                'window_minutes': _error_tracking['error_window_minutes'],
                'timestamp': current_time.isoformat()
            },
            'timestamp': current_time.isoformat()
        }


def cleanup_old_metrics(retention_hours: int = 24):
    """Clean up old performance metrics to prevent memory issues."""
    cutoff_time = datetime.now() - timedelta(hours=retention_hours)
    
    with _metrics_lock:
        # Clean up block processing times
        _performance_metrics['block_processing_times'] = deque([
            pt for pt in _performance_metrics['block_processing_times']
            if pt['timestamp'] >= cutoff_time
        ], maxlen=1000)
        
        # Clean up error tracking
        _error_tracking['recent_errors'] = deque([
            err for err in _error_tracking['recent_errors']
            if err['timestamp'] >= cutoff_time
        ], maxlen=1000)
        
        # Clean up error rates
        for error_type in _performance_metrics['error_rates']:
            _performance_metrics['error_rates'][error_type] = deque([
                err_time for err_time in _performance_metrics['error_rates'][error_type]
                if err_time >= cutoff_time
            ], maxlen=100)
        
        # Clean up inactive session metrics
        inactive_sessions = []
        for session_id, metrics in _performance_metrics['session_metrics'].items():
            if metrics['last_activity'] < cutoff_time:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            del _performance_metrics['session_metrics'][session_id]
        
        logger.info(f"Cleaned up metrics older than {retention_hours} hours")


# Start background cleanup thread
def start_metrics_cleanup_thread():
    """Start background thread for metrics cleanup."""
    def cleanup_worker():
        while True:
            try:
                time.sleep(3600)  # Run every hour
                cleanup_old_metrics()
            except Exception as e:
                logger.error(f"Error in metrics cleanup thread: {e}")
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("Started metrics cleanup background thread")


def emit_progress(session_id: str, step: str, status: str, detail: str, progress_percent: Optional[int] = None):
    """Emit progress update to specific session."""
    try:
        # Record websocket event
        record_websocket_event('progress_update', session_id)
        
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit progress")
            record_error('websocket_not_initialized', 'SocketIO not initialized for progress update', session_id)
            return
            
        if session_id and session_id.strip():
            # Auto-add session if it doesn't exist (frontend might generate its own IDs)
            if session_id not in active_sessions:
                active_sessions.add(session_id)
                logger.debug(f"Auto-added session to active sessions: {session_id}")
            
            data = {
                'step': step,
                'status': status,
                'detail': detail,
                'session_id': session_id
            }
            
            if progress_percent is not None:
                data['progress'] = str(progress_percent)
            
            _socketio.emit('progress_update', data, to=session_id)
            logger.debug(f"Progress emitted to {session_id}: {step} - {status}")
        else:
            # If no session ID, emit to all connected clients
            data = {
                'step': step,
                'status': status,
                'detail': detail,
                'session_id': 'broadcast'
            }
            
            if progress_percent is not None:
                data['progress'] = str(progress_percent)
            
            _socketio.emit('progress_update', data, broadcast=True)
            logger.debug(f"Progress broadcast to all clients: {step} - {status}")
    except Exception as e:
        logger.error(f"Error emitting progress: {e}")
        record_error('emit_progress_failed', str(e), session_id)


def emit_completion(session_id: str, event_type: str, data: Optional[dict] = None, error: Optional[str] = None):
    """
    Emit completion notification to specific session.
    
    Args:
        session_id: Session identifier
        event_type: Type of completion event (e.g., 'block_processing_complete', 'operation_complete')
        data: Optional completion data
        error: Optional error message
    """
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit completion")
            return
            
        # Determine success based on error presence
        success = error is None
            
        if session_id and session_id.strip():
            # Auto-add session if it doesn't exist (frontend might generate its own IDs)
            if session_id not in active_sessions:
                active_sessions.add(session_id)
                logger.debug(f"Auto-added session to active sessions: {session_id}")
            
            completion_data = {
                'success': success,
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            }
            
            if data:
                completion_data.update(data)
            if error:
                completion_data['error'] = error
            
            _socketio.emit(event_type, completion_data, to=session_id)
            logger.debug(f"Completion emitted to {session_id}: {event_type} success={success}")
        else:
            # If no session ID, emit to all connected clients
            completion_data = {
                'success': success,
                'session_id': 'broadcast',
                'timestamp': datetime.now().isoformat()
            }
            
            if data:
                completion_data.update(data)
            if error:
                completion_data['error'] = error
            
            _socketio.emit(event_type, completion_data, broadcast=True)
            logger.debug(f"Completion broadcast to all clients: {event_type} success={success}")
    except Exception as e:
        logger.error(f"Error emitting completion: {e}")


def emit_confidence_update(session_id: str, confidence_data: Dict[str, Any]):
    """Emit confidence-related update to specific session."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit confidence update")
            return
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
                logger.debug(f"Auto-added session to active sessions: {session_id}")
            
            event_data = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                **confidence_data
            }
            
            _socketio.emit('confidence_update', event_data, to=session_id)
            logger.debug(f"Confidence update emitted to {session_id}: {confidence_data.get('event_type', 'unknown')}")
        else:
            event_data = {
                'session_id': 'broadcast',
                'timestamp': datetime.now().isoformat(),
                **confidence_data
            }
            
            _socketio.emit('confidence_update', event_data, broadcast=True)
            logger.debug(f"Confidence update broadcast: {confidence_data.get('event_type', 'unknown')}")
    except Exception as e:
        logger.error(f"Error emitting confidence update: {e}")


def emit_validation_progress(session_id: str, validation_stage: str, progress_data: Dict[str, Any]):
    """Emit validation progress update to specific session."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit validation progress")
            return
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
                logger.debug(f"Auto-added session to active sessions: {session_id}")
            
            event_data = {
                'session_id': session_id,
                'validation_stage': validation_stage,
                'timestamp': datetime.now().isoformat(),
                **progress_data
            }
            
            _socketio.emit('validation_progress', event_data, to=session_id)
            logger.debug(f"Validation progress emitted to {session_id}: {validation_stage}")
        else:
            event_data = {
                'session_id': 'broadcast',
                'validation_stage': validation_stage,
                'timestamp': datetime.now().isoformat(),
                **progress_data
            }
            
            _socketio.emit('validation_progress', event_data, broadcast=True)
            logger.debug(f"Validation progress broadcast: {validation_stage}")
    except Exception as e:
        logger.error(f"Error emitting validation progress: {e}")


def emit_feedback_notification(session_id: str, feedback_data: Dict[str, Any]):
    """Emit feedback-related notification to specific session."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit feedback notification")
            return
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
                logger.debug(f"Auto-added session to active sessions: {session_id}")
            
            event_data = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                **feedback_data
            }
            
            _socketio.emit('feedback_notification', event_data, to=session_id)
            logger.debug(f"Feedback notification emitted to {session_id}: {feedback_data.get('event_type', 'unknown')}")
        else:
            event_data = {
                'session_id': 'broadcast',
                'timestamp': datetime.now().isoformat(),
                **feedback_data
            }
            
            _socketio.emit('feedback_notification', event_data, broadcast=True)
            logger.debug(f"Feedback notification broadcast: {feedback_data.get('event_type', 'unknown')}")
    except Exception as e:
        logger.error(f"Error emitting feedback notification: {e}")


def emit_confidence_insights(session_id: str, insights_data: Dict[str, Any]):
    """Emit confidence insights and analytics to specific session."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit confidence insights")
            return
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
                logger.debug(f"Auto-added session to active sessions: {session_id}")
            
            event_data = {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'confidence_insights',
                **insights_data
            }
            
            _socketio.emit('confidence_insights', event_data, to=session_id)
            logger.debug(f"Confidence insights emitted to {session_id}")
        else:
            event_data = {
                'session_id': 'broadcast',
                'timestamp': datetime.now().isoformat(),
                'event_type': 'confidence_insights',
                **insights_data
            }
            
            _socketio.emit('confidence_insights', event_data, broadcast=True)
            logger.debug(f"Confidence insights broadcast")
    except Exception as e:
        logger.error(f"Error emitting confidence insights: {e}")


def setup_websocket_handlers(socketio):
    """Setup WebSocket event handlers."""
    
    # Set the socketio instance for use in emit functions
    set_socketio(socketio)
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        try:
            session_id = str(uuid.uuid4())
            active_sessions.add(session_id)
            from flask_socketio import emit
            emit('connected', {'session_id': session_id})
            logger.info(f"Client connected with session ID: {session_id}")
        except Exception as e:
            logger.error(f"Error handling connection: {e}")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection."""
        try:
            # Note: We don't clean up sessions automatically on disconnect
            # because the frontend might reconnect with the same session ID
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error handling disconnection: {e}")
    
    @socketio.on('join_session')
    def handle_join_session(data):
        """Handle client joining a specific session."""
        try:
            session_id = data.get('session_id')
            if session_id:
                from flask_socketio import join_room, emit
                join_room(session_id)
                active_sessions.add(session_id)
                emit('session_joined', {'session_id': session_id})
                logger.info(f"Client joined session: {session_id}")
            else:
                from flask_socketio import emit
                emit('error', {'message': 'No session ID provided'})
        except Exception as e:
            logger.error(f"Error joining session: {e}")
            from flask_socketio import emit
            emit('error', {'message': 'Failed to join session'})
    
    @socketio.on('leave_session')
    def handle_leave_session(data):
        """Handle client leaving a specific session."""
        try:
            session_id = data.get('session_id')
            if session_id:
                from flask_socketio import leave_room, emit
                leave_room(session_id)
                active_sessions.discard(session_id)
                emit('session_left', {'session_id': session_id})
                logger.info(f"Client left session: {session_id}")
        except Exception as e:
            logger.error(f"Error leaving session: {e}")
    
    @socketio.on('ping')
    def handle_ping():
        """Handle ping for connection testing."""
        try:
            from flask_socketio import emit
            emit('pong', {'timestamp': str(uuid.uuid4())})
        except Exception as e:
            logger.error(f"Error handling ping: {e}")
    
    @socketio.on('request_confidence_update')
    def handle_confidence_request(data):
        """Handle request for confidence updates."""
        try:
            session_id = data.get('session_id')
            if not session_id:
                from flask_socketio import emit
                emit('error', {'message': 'No session ID provided for confidence request'})
                return
            
            # Emit acknowledgment
            from flask_socketio import emit
            emit('confidence_request_received', {
                'session_id': session_id,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Confidence update requested for session: {session_id}")
        except Exception as e:
            logger.error(f"Error handling confidence request: {e}")
            from flask_socketio import emit
            emit('error', {'message': 'Failed to process confidence request'})
    
    @socketio.on('submit_feedback_realtime')
    def handle_realtime_feedback(data):
        """Handle real-time feedback submission."""
        try:
            session_id = data.get('session_id')
            feedback_data = data.get('feedback_data', {})
            
            if not session_id:
                from flask_socketio import emit
                emit('error', {'message': 'No session ID provided for feedback'})
                return
            
            if not feedback_data:
                from flask_socketio import emit
                emit('error', {'message': 'No feedback data provided'})
                return
            
            # Process feedback asynchronously
            try:
                from .feedback_storage import feedback_storage
                success, message, feedback_id = feedback_storage.store_feedback(feedback_data)
                
                # Emit feedback processing result
                from flask_socketio import emit
                if success:
                    emit('feedback_processed', {
                        'success': True,
                        'feedback_id': feedback_id,
                        'message': message,
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat()
                    })
                    
                    # Notify about successful feedback
                    emit_feedback_notification(session_id, {
                        'event_type': 'feedback_submitted',
                        'feedback_id': feedback_id,
                        'feedback_type': feedback_data.get('feedback_type'),
                        'error_type': feedback_data.get('error_type')
                    })
                else:
                    emit('feedback_error', {
                        'success': False,
                        'message': message,
                        'session_id': session_id,
                        'timestamp': datetime.now().isoformat()
                    })
                
                logger.info(f"Real-time feedback processed for session {session_id}: {success}")
                
            except Exception as feedback_error:
                logger.error(f"Error processing real-time feedback: {feedback_error}")
                from flask_socketio import emit
                emit('feedback_error', {
                    'success': False,
                    'message': f'Feedback processing failed: {str(feedback_error)}',
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error handling real-time feedback: {e}")
            from flask_socketio import emit
            emit('error', {'message': 'Failed to process feedback'})
    
    @socketio.on('request_validation_status')
    def handle_validation_status_request(data):
        """Handle request for validation status."""
        try:
            session_id = data.get('session_id')
            if not session_id:
                from flask_socketio import emit
                emit('error', {'message': 'No session ID provided for validation status'})
                return
            
            # Emit validation status (this would typically be populated by the validation system)
            from flask_socketio import emit
            emit('validation_status', {
                'session_id': session_id,
                'status': 'active',
                'enhanced_validation_enabled': True,
                'timestamp': datetime.now().isoformat()
            })
            
            logger.info(f"Validation status requested for session: {session_id}")
        except Exception as e:
            logger.error(f"Error handling validation status request: {e}")
            from flask_socketio import emit
            emit('error', {'message': 'Failed to get validation status'})
    
    @socketio.on('subscribe_insights')
    def handle_insights_subscription(data):
        """Handle subscription to confidence insights."""
        try:
            session_id = data.get('session_id')
            insights_type = data.get('insights_type', 'all')
            
            if not session_id:
                from flask_socketio import emit
                emit('error', {'message': 'No session ID provided for insights subscription'})
                return
            
            # Join insights room for this session
            from flask_socketio import join_room, emit
            insights_room = f"insights_{session_id}"
            join_room(insights_room)
            
            emit('insights_subscribed', {
                'session_id': session_id,
                'insights_type': insights_type,
                'subscribed_at': datetime.now().isoformat()
            })
            
            logger.info(f"Session {session_id} subscribed to {insights_type} insights")
        except Exception as e:
            logger.error(f"Error handling insights subscription: {e}")
            from flask_socketio import emit
            emit('error', {'message': 'Failed to subscribe to insights'})


def cleanup_session(session_id: str):
    """Cleanup a specific session."""
    try:
        active_sessions.discard(session_id)
        logger.info(f"Cleaned up session: {session_id}")
    except Exception as e:
        logger.error(f"Error cleaning up session {session_id}: {e}")


def cleanup_all_sessions():
    """Cleanup all active sessions."""
    try:
        session_count = len(active_sessions)
        active_sessions.clear()
        logger.info(f"Cleaned up {session_count} active sessions")
    except Exception as e:
        logger.error(f"Error cleaning up all sessions: {e}")


def get_active_sessions():
    """Get list of active sessions."""
    return list(active_sessions)


def get_session_count():
    """Get the number of active sessions."""
    return len(active_sessions)


def is_session_active(session_id: str) -> bool:
    """Check if a session is active."""
    return session_id in active_sessions


# Enhanced WebSocket helper functions for confidence and feedback features

def broadcast_confidence_threshold_change(new_threshold: float, changed_by_session: Optional[str] = None):
    """Broadcast confidence threshold change to all sessions."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot broadcast threshold change")
            return
        
        threshold_data = {
            'event_type': 'threshold_changed',
            'new_threshold': new_threshold,
            'changed_by_session': changed_by_session,
            'timestamp': datetime.now().isoformat()
        }
        
        _socketio.emit('confidence_update', threshold_data, broadcast=True)
        logger.info(f"Confidence threshold change broadcast: {new_threshold}")
    except Exception as e:
        logger.error(f"Error broadcasting threshold change: {e}")


def emit_validation_stats(session_id: str, validation_stats: Dict[str, Any]):
    """Emit validation statistics to specific session."""
    try:
        stats_data = {
            'event_type': 'validation_statistics',
            'stats': validation_stats,
            'timestamp': datetime.now().isoformat()
        }
        
        emit_confidence_update(session_id, stats_data)
        logger.debug(f"Validation stats emitted to {session_id}")
    except Exception as e:
        logger.error(f"Error emitting validation stats: {e}")


def emit_error_confidence_breakdown(session_id: str, error_breakdown: List[Dict[str, Any]]):
    """Emit error confidence breakdown to specific session."""
    try:
        breakdown_data = {
            'event_type': 'error_confidence_breakdown',
            'breakdown': error_breakdown,
            'timestamp': datetime.now().isoformat()
        }
        
        emit_confidence_update(session_id, breakdown_data)
        logger.debug(f"Error confidence breakdown emitted to {session_id}")
    except Exception as e:
        logger.error(f"Error emitting confidence breakdown: {e}")


def emit_feedback_acknowledgment(session_id: str, feedback_id: str, feedback_type: str):
    """Emit feedback acknowledgment to specific session."""
    try:
        ack_data = {
            'event_type': 'feedback_acknowledged',
            'feedback_id': feedback_id,
            'feedback_type': feedback_type,
            'timestamp': datetime.now().isoformat()
        }
        
        emit_feedback_notification(session_id, ack_data)
        logger.debug(f"Feedback acknowledgment emitted to {session_id}: {feedback_id}")
    except Exception as e:
        logger.error(f"Error emitting feedback acknowledgment: {e}")


def emit_session_feedback_summary(session_id: str, feedback_summary: Dict[str, Any]):
    """Emit session feedback summary to specific session."""
    try:
        summary_data = {
            'event_type': 'session_feedback_summary',
            'summary': feedback_summary,
            'timestamp': datetime.now().isoformat()
        }
        
        emit_feedback_notification(session_id, summary_data)
        logger.debug(f"Session feedback summary emitted to {session_id}")
    except Exception as e:
        logger.error(f"Error emitting session feedback summary: {e}")


# Block-Level Rewriting WebSocket Events

def emit_block_processing_start(session_id: str, block_id: str, block_type: str, applicable_stations: List[str]):
    """Emit block processing start event."""
    try:
        # Record websocket event
        record_websocket_event('block_processing_start', session_id)
        
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit block processing start")
            record_error('websocket_not_initialized', 'SocketIO not initialized for block processing start', session_id)
            return
            
        event_data = {
            'block_id': block_id,
            'block_type': block_type,
            'applicable_stations': applicable_stations,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
            
            _socketio.emit('block_processing_start', event_data, to=session_id)
            logger.debug(f"Block processing start emitted to {session_id}: {block_id}")
        else:
            _socketio.emit('block_processing_start', event_data, broadcast=True)
            logger.debug(f"Block processing start broadcast: {block_id}")
    except Exception as e:
        logger.error(f"Error emitting block processing start: {e}")
        record_error('emit_block_start_failed', str(e), session_id)


def emit_station_progress_update(session_id: str, block_id: str, station: str, status: str, preview_text: Optional[str] = None):
    """Emit assembly line station progress update."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit station progress")
            return
            
        event_data = {
            'block_id': block_id,
            'station': station,
            'status': status,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if preview_text:
            event_data['preview_text'] = preview_text
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
            
            _socketio.emit('station_progress_update', event_data, to=session_id)
            logger.debug(f"Station progress emitted to {session_id}: {block_id} - {station} - {status}")
        else:
            _socketio.emit('station_progress_update', event_data, broadcast=True)
            logger.debug(f"Station progress broadcast: {block_id} - {station} - {status}")
    except Exception as e:
        logger.error(f"Error emitting station progress: {e}")


def emit_block_processing_complete(session_id: str, block_id: str, result: Dict[str, Any], processing_time: Optional[float] = None):
    """Emit block processing completion event."""
    try:
        # Record websocket event
        record_websocket_event('block_processing_complete', session_id)
        
        # Record processing metrics if time provided
        if processing_time is not None:
            success = result.get('success', True) and not result.get('error')
            record_block_processing_time(block_id, processing_time, success)
        
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit block processing complete")
            record_error('websocket_not_initialized', 'SocketIO not initialized for block processing complete', session_id)
            return
            
        event_data = {
            'block_id': block_id,
            'result': result,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if processing_time is not None:
            event_data['processing_time'] = processing_time
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
            
            _socketio.emit('block_processing_complete', event_data, to=session_id)
            logger.debug(f"Block processing complete emitted to {session_id}: {block_id}")
        else:
            _socketio.emit('block_processing_complete', event_data, broadcast=True)
            logger.debug(f"Block processing complete broadcast: {block_id}")
    except Exception as e:
        logger.error(f"Error emitting block processing complete: {e}")
        record_error('emit_block_complete_failed', str(e), session_id)


def emit_block_error(session_id: str, block_id: str, error_message: str):
    """Emit block processing error event."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit block error")
            return
            
        event_data = {
            'block_id': block_id,
            'error': error_message,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }
        
        if session_id and session_id.strip():
            if session_id not in active_sessions:
                active_sessions.add(session_id)
            
            _socketio.emit('block_processing_error', event_data, to=session_id)
            logger.debug(f"Block error emitted to {session_id}: {block_id}")
        else:
            _socketio.emit('block_processing_error', event_data, broadcast=True)
            logger.debug(f"Block error broadcast: {block_id}")
    except Exception as e:
        logger.error(f"Error emitting block error: {e}")


def get_websocket_performance_metrics() -> Dict[str, Any]:
    """Get comprehensive WebSocket performance metrics."""
    try:
        performance_summary = get_performance_summary()
        websocket_health = validate_websocket_health()
        
        return {
            'websocket_health': websocket_health,
            'performance_summary': performance_summary,
            'detailed_metrics': {
                'active_sessions_count': len(active_sessions),
                'active_sessions': list(active_sessions),
                'websocket_initialized': _socketio is not None,
                'recent_error_rate': get_error_rate(),
                'error_rate_status': check_error_rate_threshold()
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting WebSocket performance metrics: {e}")
        return {'error': str(e), 'timestamp': datetime.now().isoformat()}


def validate_websocket_health() -> Dict[str, Any]:
    """Validate WebSocket system health."""
    try:
        health_status = {
            'status': 'healthy',
            'socketio_initialized': _socketio is not None,
            'active_sessions_count': len(active_sessions),
            'can_emit': _socketio is not None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Perform basic health checks
        if not _socketio:
            health_status['status'] = 'unhealthy'
            health_status['issues'] = ['SocketIO not initialized']
        
        return health_status
    except Exception as e:
        logger.error(f"Error validating WebSocket health: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        } 