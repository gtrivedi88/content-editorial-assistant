/**
 * Action Creators — orchestrate state changes and API calls.
 * Adapted for the new /api/v1/ backend contract with three-phase analysis.
 */

import { store } from './store.js';
import {
    postAnalyze, postUpload, submitFeedback as apiSubmitFeedback,
    fetchSuggestion, fetchCitation, acceptIssue, dismissIssue,
} from '../services/api-client.js';
import { getGroup } from '../shared/style-guide-groups.js';
import { generateId } from '../shared/dom-utils.js';
import { clearSuggestionCache } from '../issues/issue-card.js';

/**
 * Start content analysis.
 * Generates a new analysisId for cancellation tracking.
 * When LLM is enabled (partial=true), the checking indicator stays
 * visible until the analysis_complete WebSocket event delivers
 * the final merged results. No intermediate results are shown.
 */
export async function analyzeContent() {
    const { content, formatHint, contentType, sessionId } = store.getState();
    if (!content.trim()) return;

    const sid = sessionId || generateId();
    const analysisId = generateId();

    clearSuggestionCache();

    store.setState({
        analysisStatus: 'analyzing',
        currentAnalysisId: analysisId,
        sessionId: sid,
        errors: [],
        filteredErrors: [],
        selectedErrorId: null,
        dismissedErrors: new Set(),
        resolvedErrors: new Set(),
        progressSteps: [],
        progressPercent: 0,
        qualityScore: 0,
        errorMessage: null,
    });

    try {
        const response = await postAnalyze(content, formatHint, contentType, sid);

        // Guard against stale responses after cancellation
        if (store.get('currentAnalysisId') !== analysisId) return;

        if (!response.success) {
            store.setState({
                analysisStatus: 'error',
                errorMessage: response.error || 'Analysis failed',
            });
            return;
        }

        // When LLM is pending (partial=true), keep the checking indicator
        // visible. Only store the session_id so WebSocket events match.
        // Final results arrive via the analysis_complete WebSocket event.
        if (response.partial) {
            store.setState({
                analysisResult: response,
                sessionId: response.session_id || sid,
            });
            return;
        }

        // LLM disabled (partial=false): show results immediately
        console.log('[Actions] HTTP response: partial=false, %d issues', (response.issues || []).length);
        if (response.issues) {
            response.issues.forEach((iss, i) => {
                console.log('[Actions] DEBUG HTTP issue[%d]: id=%s rule=%s span=%s flagged_text=%s',
                    i, iss.id, iss.rule_name, JSON.stringify(iss.span),
                    JSON.stringify((iss.flagged_text || '').substring(0, 60)));
            });
        }
        const flatErrors = flattenErrors(response.issues || []);
        console.log('[Actions] flattenErrors produced %d errors', flatErrors.length);
        const score = typeof response.score === 'object' ? response.score.score : (response.score ?? 0);

        store.setState({
            analysisStatus: 'complete',
            analysisResult: response,
            sessionId: response.session_id || sid,
            errors: flatErrors,
            filteredErrors: flatErrors,
            structuralBlocks: response.structural_blocks || [],
            codeBlockRanges: response.code_block_ranges || [],
            readability: response.report?.readability || null,
            statistics: response.report?.statistics || null,
            qualityScore: score,
        });
    } catch (err) {
        // Ignore abort errors from cancelled requests
        if (err.name === 'AbortError') return;

        console.error('[Actions] Analysis failed:', err);
        if (store.get('currentAnalysisId') !== analysisId) return;

        store.setState({
            analysisStatus: 'error',
            errorMessage: err.message || 'Network error',
        });
    }
}

/**
 * Upload a file and populate the editor.
 */
export async function uploadFile(file) {
    store.setState({ analysisStatus: 'uploading', errorMessage: null });

    try {
        const response = await postUpload(file);

        if (!response.success) {
            store.setState({
                analysisStatus: 'idle',
                errorMessage: response.error || 'Upload failed',
            });
            return null;
        }

        store.setState({
            analysisStatus: 'idle',
            content: response.content,
            formatHint: response.detected_format || 'auto',
        });

        return response;
    } catch (err) {
        console.error('[Actions] Upload failed:', err);
        store.setState({
            analysisStatus: 'idle',
            errorMessage: err.message || 'Upload failed',
        });
        return null;
    }
}

/**
 * Select an error (click underline or card).
 */
export function selectError(errorId) {
    store.setState({ selectedErrorId: errorId });
}

/**
 * Accept a suggestion — replace text inline.
 */
export function acceptSuggestion(errorId) {
    const { errors, resolvedErrors, filteredErrors, sessionId } = store.getState();
    const newResolved = new Set(resolvedErrors);
    newResolved.add(errorId);

    const newErrors = errors.filter((e) => e.id !== errorId);
    const newFiltered = filteredErrors.filter((e) => e.id !== errorId);

    store.setState({
        errors: newErrors,
        filteredErrors: newFiltered,
        resolvedErrors: newResolved,
        selectedErrorId: null,
    });

    // Notify backend
    if (sessionId) {
        acceptIssue(sessionId, errorId).catch((err) => {
            console.error('[Actions] Accept issue notification failed:', err);
        });
    }
}

/**
 * Dismiss an error — remove underline and card.
 */
export function dismissError(errorId) {
    const { dismissedErrors, errors, filteredErrors, sessionId } = store.getState();
    const newDismissed = new Set(dismissedErrors);
    newDismissed.add(errorId);

    const newErrors = errors.filter((e) => e.id !== errorId);
    const newFiltered = filteredErrors.filter((e) => e.id !== errorId);

    store.setState({
        errors: newErrors,
        filteredErrors: newFiltered,
        dismissedErrors: newDismissed,
        selectedErrorId: null,
    });

    // Notify backend
    if (sessionId) {
        dismissIssue(sessionId, errorId).catch((err) => {
            console.error('[Actions] Dismiss issue notification failed:', err);
        });
    }
}

/**
 * Filter errors by IBM Style Guide group.
 */
export function filterByGroup(group) {
    const { errors } = store.getState();
    const filtered = group === 'all'
        ? errors
        : errors.filter((e) => e.group === group);

    store.setState({
        activeGroup: group,
        filteredErrors: filtered,
        selectedErrorId: null,
    });
}

/**
 * Submit feedback for an error (thumbs up/down).
 */
export async function submitFeedback(error, feedbackType) {
    const sessionId = store.get('sessionId');
    try {
        await apiSubmitFeedback(
            sessionId || '',
            error.id,
            error.rule_name || error.type,
            feedbackType === 'correct',
            ''
        );
    } catch (err) {
        console.error('[Actions] Feedback submission failed:', err);
    }
}

/**
 * Get an LLM suggestion for a specific issue.
 */
export async function getSuggestion(issueId) {
    const sessionId = store.get('sessionId');
    if (!sessionId) return null;

    try {
        const response = await fetchSuggestion(sessionId, issueId);
        return response;
    } catch (err) {
        console.error('[Actions] Suggestion fetch failed:', err);
        return null;
    }
}

/**
 * Get a citation excerpt for a rule type.
 */
export async function getCitation(ruleType) {
    if (!ruleType) return null;

    try {
        const response = await fetchCitation(ruleType);
        return response;
    } catch (err) {
        console.error('[Actions] Citation fetch failed:', err);
        return null;
    }
}

/**
 * Merge new LLM-sourced errors into the existing error list.
 * Deduplicates by span overlap, preserves user actions on existing issues.
 *
 * @param {Array} existingErrors - Current errors in state
 * @param {Array} newLlmErrors - New errors from LLM phase
 * @returns {Array} Merged and deduplicated errors
 */
export function mergeErrors(existingErrors, newLlmErrors) {
    if (!newLlmErrors || newLlmErrors.length === 0) return existingErrors;

    const { dismissedErrors, resolvedErrors } = store.getState();
    const merged = [...existingErrors];

    for (const llmError of newLlmErrors) {
        const normalized = normalizeError(llmError, merged.length);

        // Skip if user already dismissed or resolved this issue
        if (dismissedErrors.has(normalized.id) || resolvedErrors.has(normalized.id)) {
            continue;
        }

        // Check for span overlap with existing errors
        const hasOverlap = merged.some((existing) => {
            const [eStart, eEnd] = existing.globalSpan;
            const [nStart, nEnd] = normalized.globalSpan;
            return eStart < nEnd && nStart < eEnd && existing.type === normalized.type;
        });

        if (!hasOverlap) {
            merged.push(normalized);
        }
    }

    return merged;
}

/**
 * Flatten errors from the new API format (flat issues array) into UI format.
 * The new API returns issues directly as a list, not nested in structural_blocks.
 *
 * @param {Array} issues - Flat list of issue objects from the API
 * @returns {Array} Normalized and deduplicated errors
 */
function flattenErrors(issues) {
    if (!issues || issues.length === 0) return [];

    const errors = [];
    for (const issue of issues) {
        errors.push(normalizeError(issue, errors.length));
    }

    // Deduplicate by span
    const seen = new Set();
    return errors.filter((e) => {
        const key = `${e.globalSpan[0]}-${e.globalSpan[1]}-${e.type}`;
        if (seen.has(key)) return false;
        seen.add(key);
        return true;
    });
}

/**
 * Normalize a backend error object for the UI.
 * The new API returns `span` directly (not `raw_span`), and includes
 * `id`, `source`, `category`, `rule_name`, `confidence`, `style_guide_citation`.
 */
function normalizeError(error, index) {
    const span = error.span || [0, 0];
    const backendId = error.id || `err-${index}-${span[0]}-${span[1]}`;

    return {
        ...error,
        id: backendId,
        type: error.rule_name || error.type || 'general',
        group: getGroup(error.rule_name || error.type),
        globalSpan: [span[0], span[1]],
        source: error.source || 'deterministic',
        category: error.category || '',
        rule_name: error.rule_name || error.type || '',
        confidence: error.confidence ?? 1.0,
        style_guide_citation: error.style_guide_citation || '',
    };
}
