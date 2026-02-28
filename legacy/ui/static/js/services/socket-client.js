/**
 * WebSocket Client — Socket.IO event binding and progress handling.
 * Socket.IO is loaded as a global script (not an ES module).
 */

let socket = null;

/**
 * Initialize Socket.IO connection and bind events.
 */
export function initSocketClient(store) {
    if (typeof io === 'undefined') {
        console.warn('[Socket] Socket.IO not loaded');
        return null;
    }

    socket = io({
        reconnection: true,
        reconnectionAttempts: 10,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        timeout: 300000,
    });

    socket.on('connect', () => {
        console.log('[Socket] Connected:', socket.id);
        const sessionId = store.get('sessionId');
        if (sessionId) {
            socket.emit('join_session', { session_id: sessionId });
        }
    });

    socket.on('disconnect', (reason) => {
        console.log('[Socket] Disconnected:', reason);
    });

    // Analysis progress
    socket.on('progress_update', (data) => {
        const steps = store.get('progressSteps');
        const existing = steps.findIndex((s) => s.step === data.step);
        const newStep = {
            step: data.step,
            status: data.status,
            detail: data.detail,
            percent: parseInt(data.progress, 10) || 0,
        };

        let newSteps;
        if (existing >= 0) {
            newSteps = [...steps];
            newSteps[existing] = newStep;
        } else {
            newSteps = [...steps, newStep];
        }

        store.setState({
            progressSteps: newSteps,
            progressPercent: newStep.percent,
        });
    });

    // Analysis complete via socket (fallback — HTTP response is primary)
    socket.on('process_complete', (data) => {
        if (data.success && store.get('analysisStatus') === 'analyzing') {
            console.log('[Socket] Analysis complete via WebSocket');
        }
    });

    socket.on('analysis_error', (data) => {
        if (store.get('analysisStatus') === 'analyzing') {
            store.setState({
                analysisStatus: 'error',
                errorMessage: data.error || 'Analysis failed',
            });
        }
    });

    // Subscribe to sessionId changes to join rooms
    store.subscribe('sessionId', (sessionId) => {
        if (sessionId && socket.connected) {
            socket.emit('join_session', { session_id: sessionId });
        }
    });

    return socket;
}

/**
 * Get the socket instance.
 */
export function getSocket() {
    return socket;
}
