"""
WebSocket Handlers Module
Handles real-time communication for progress updates and notifications.
Provides real-time feedback during analysis and rewriting operations.
"""

import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Store active sessions
active_sessions = set()

# Store socketio instance for use in emit functions
_socketio = None


def set_socketio(socketio):
    """Set the SocketIO instance for use in emit functions."""
    global _socketio
    _socketio = socketio


def emit_progress(session_id: str, step: str, status: str, detail: str, progress_percent: Optional[int] = None):
    """Emit progress update to specific session."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit progress")
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


def emit_completion(session_id: str, success: bool, data: Optional[dict] = None, error: Optional[str] = None):
    """Emit completion notification to specific session."""
    try:
        if not _socketio:
            logger.warning("SocketIO not initialized, cannot emit completion")
            return
            
        if session_id and session_id.strip():
            # Auto-add session if it doesn't exist (frontend might generate its own IDs)
            if session_id not in active_sessions:
                active_sessions.add(session_id)
                logger.debug(f"Auto-added session to active sessions: {session_id}")
            
            completion_data = {
                'success': success,
                'session_id': session_id
            }
            
            if data:
                completion_data['data'] = data
            if error:
                completion_data['error'] = error
            
            _socketio.emit('operation_complete', completion_data, to=session_id)
            logger.debug(f"Completion emitted to {session_id}: success={success}")
        else:
            # If no session ID, emit to all connected clients
            completion_data = {
                'success': success,
                'session_id': 'broadcast'
            }
            
            if data:
                completion_data['data'] = data
            if error:
                completion_data['error'] = error
            
            _socketio.emit('operation_complete', completion_data, broadcast=True)
            logger.debug(f"Completion broadcast to all clients: success={success}")
    except Exception as e:
        logger.error(f"Error emitting completion: {e}")


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