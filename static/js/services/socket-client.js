/**
 * WebSocket Client — Socket.IO event binding and streaming analysis handlers.
 * Socket.IO is loaded as a global script (not an ES module).
 *
 * All intermediate phase events (deterministic_complete, llm_granular_complete,
 * llm_global_complete) are logged but do NOT update the UI. The checking
 * indicator stays visible throughout the entire pipeline. Only the
 * analysis_complete event reveals the final merged results.
 */

import { getGroup } from '../shared/style-guide-groups.js';

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

    // Analysis progress — updates the checking indicator sweep
    socket.on('progress_update', (data) => {
        if (data.session_id && data.session_id !== store.get('sessionId')) return;

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

    // Stage progress — drives the checking indicator phases
    socket.on('stage_progress', (data) => {
        if (data.session_id && data.session_id !== store.get('sessionId')) return;
        store.setState({ stageProgress: data });
    });

    // Phase 1: Deterministic rules complete — logged only, no UI update
    socket.on('deterministic_complete', (data) => {
        if (data.session_id !== store.get('sessionId')) return;
        console.log('[Socket] Deterministic phase complete (%d issues)', (data.issues || []).length);
    });

    // Phase 2: LLM granular (per-block) complete — logged only, no UI update
    socket.on('llm_granular_complete', (data) => {
        if (data.session_id !== store.get('sessionId')) return;
        console.log('[Socket] LLM granular phase complete (%d issues)', (data.issues || []).length);
    });

    // Phase 3: LLM global (tone/flow) complete — logged only, no UI update
    socket.on('llm_global_complete', (data) => {
        if (data.session_id !== store.get('sessionId')) return;
        console.log('[Socket] LLM global phase complete (%d issues)', (data.issues || []).length);
    });

    // Final: Analysis fully complete — the single source of truth for UI results
    socket.on('analysis_complete', (data) => {
        if (data.session_id !== store.get('sessionId')) return;
        const stateUpdate = {
            analysisStatus: 'complete',
            qualityScore: (typeof data.score === 'object' ? data.score?.score : data.score) ?? store.get('qualityScore'),
            detectedContentType: data.detected_content_type || store.get('detectedContentType'),
        };

        if (data.issues && data.issues.length > 0) {
            const normalized = data.issues.map((issue, idx) => normalizeSocketIssue(issue, idx));

            const seen = new Set();
            const finalIssues = normalized.filter((e) => {
                const key = `${e.globalSpan[0]}-${e.globalSpan[1]}-${e.type}`;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            });

            const activeGroup = store.get('activeGroup');
            stateUpdate.errors = finalIssues;
            stateUpdate.filteredErrors = activeGroup === 'all'
                ? finalIssues
                : finalIssues.filter((e) => e.group === activeGroup);
        }

        // Merge report data into the same setState to avoid double subscriber notification
        if (data.report) {
            stateUpdate.readability = data.report.readability || store.get('readability');
            stateUpdate.statistics = data.report.statistics || store.get('statistics');
            stateUpdate.reportData = data.report || store.get('reportData');
        }

        store.setState(stateUpdate);

        // Guard: if user resolved issues during LLM phase, the score from
        // analysis_complete may be stale.  Backend preserves statuses, but
        // the emitted score was computed before the session update.
        const { resolvedErrors, dismissedErrors, manuallyFixedErrors } = store.getState();
        const hasResolved = (resolvedErrors?.size > 0)
            || (dismissedErrors?.size > 0)
            || (manuallyFixedErrors?.size > 0);
        const currentErrors = store.get('errors') || [];
        if (hasResolved && currentErrors.length === 0) {
            store.setState({ qualityScore: 100 });
        }
    });

    // LLM skipped — background task failed to start, use HTTP response data
    socket.on('llm_skipped', (data) => {
        if (data.session_id !== store.get('sessionId')) return;

        console.log('[Socket] LLM phase skipped');
        const analysisResult = store.get('analysisResult');
        const stateUpdate = { analysisStatus: 'complete' };

        // Fall back to the HTTP response data stored during analyzeContent()
        if (analysisResult && analysisResult.issues) {
            const flatErrors = analysisResult.issues.map((issue, idx) => normalizeSocketIssue(issue, idx));
            const score = typeof analysisResult.score === 'object'
                ? analysisResult.score.score
                : (analysisResult.score ?? 0);
            stateUpdate.errors = flatErrors;
            stateUpdate.filteredErrors = flatErrors;
            stateUpdate.qualityScore = score;
        }

        store.setState(stateUpdate);
    });

    // Analysis error via socket
    socket.on('analysis_error', (data) => {
        if (data.session_id && data.session_id !== store.get('sessionId')) return;

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
 * Normalize an issue from a socket event for the UI.
 */
function normalizeSocketIssue(issue, index) {
    const span = issue.span || [0, 0];
    const backendId = issue.id || `err-${index}-${span[0]}-${span[1]}`;

    return {
        ...issue,
        id: backendId,
        type: issue.rule_name || issue.type || 'general',
        group: getGroup(issue.rule_name || issue.type),
        globalSpan: [span[0], span[1]],
        source: issue.source || 'deterministic',
        category: issue.category || '',
        rule_name: issue.rule_name || issue.type || '',
        confidence: issue.confidence ?? 1.0,
        style_guide_citation: issue.style_guide_citation || '',
    };
}

/**
 * Get the socket instance.
 */
export function getSocket() {
    return socket;
}
