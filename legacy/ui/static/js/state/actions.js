/**
 * Action Creators — orchestrate state changes and API calls.
 */

import { store } from './store.js';
import { postAnalyze, postUpload, postFeedback } from '../services/api-client.js';
import { getGroup } from '../shared/style-guide-groups.js';
import { generateId } from '../shared/dom-utils.js';

/**
 * Start content analysis.
 */
export async function analyzeContent() {
    const { content, formatHint, contentType, sessionId } = store.getState();
    if (!content.trim()) return;

    const sid = sessionId || generateId();
    store.setState({
        analysisStatus: 'analyzing',
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

        if (!response.success) {
            store.setState({
                analysisStatus: 'error',
                errorMessage: response.error || 'Analysis failed',
            });
            return;
        }

        const flatErrors = flattenErrors(response.structural_blocks || [], response.analysis);
        const score = calculateScore(flatErrors, content);

        store.setState({
            analysisStatus: 'complete',
            analysisResult: response,
            errors: flatErrors,
            filteredErrors: flatErrors,
            structuralBlocks: response.structural_blocks || [],
            codeBlockRanges: response.code_block_ranges || [],
            readability: response.analysis?.readability || null,
            statistics: response.analysis?.statistics || null,
            qualityScore: score,
        });
    } catch (err) {
        console.error('[Actions] Analysis failed:', err);
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
    const { errors, resolvedErrors, filteredErrors } = store.getState();
    const newResolved = new Set(resolvedErrors);
    newResolved.add(errorId);

    const newErrors = errors.filter((e) => e.id !== errorId);
    const newFiltered = filteredErrors.filter((e) => e.id !== errorId);

    store.setState({
        errors: newErrors,
        filteredErrors: newFiltered,
        resolvedErrors: newResolved,
        selectedErrorId: null,
        qualityScore: calculateScore(newErrors, store.get('content')),
    });
}

/**
 * Dismiss an error — remove underline and card.
 */
export function dismissError(errorId) {
    const { dismissedErrors, errors, filteredErrors } = store.getState();
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
 * Submit feedback for an error.
 */
export async function submitFeedback(error, feedbackType, reason) {
    try {
        await postFeedback({
            error_type: error.type,
            error_message: error.message,
            error_text: error.flagged_text,
            feedback_type: feedbackType,
            confidence_score: error.confidence_score,
            user_reason: reason || '',
            session_id: store.get('sessionId'),
        });
    } catch (err) {
        console.error('[Actions] Feedback submission failed:', err);
    }
}

/**
 * Flatten errors from structural blocks into a single array with unique IDs.
 */
function flattenErrors(blocks, analysis) {
    const errors = [];

    if (blocks && blocks.length > 0) {
        for (const block of blocks) {
            const blockErrors = block.errors || [];
            const blockStartPos = block.start_pos || 0;

            for (const error of blockErrors) {
                errors.push(normalizeError(error, blockStartPos, errors.length));
            }

            // Recurse into nested blocks (children)
            if (block.children) {
                for (const child of block.children) {
                    const childErrors = child.errors || [];
                    const childStartPos = child.start_pos || blockStartPos;
                    for (const error of childErrors) {
                        errors.push(normalizeError(error, childStartPos, errors.length));
                    }
                }
            }
        }
    } else if (analysis?.errors) {
        // Flat error list (no structural blocks)
        for (const error of analysis.errors) {
            errors.push(normalizeError(error, 0, errors.length));
        }
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
 * Uses raw_span (source-mapped to raw text) + block.start_pos for precise positioning.
 */
function normalizeError(error, blockStartPos, index) {
    const rawSpan = error.raw_span || error.span || [0, 0];
    return {
        ...error,
        id: `err-${index}-${rawSpan[0]}-${rawSpan[1]}`,
        group: getGroup(error.type),
        globalSpan: [rawSpan[0] + blockStartPos, rawSpan[1] + blockStartPos],
    };
}

/**
 * Calculate a quality score (0-100) from error count and severity.
 */
function calculateScore(errors, content) {
    if (!content || !content.trim()) return 0;

    const wordCount = content.trim().split(/\s+/).length;
    if (wordCount === 0) return 100;

    // Errors per 100 words
    const errorRate = (errors.length / wordCount) * 100;

    // Score decreases with error rate
    // 0 errors = 100, 5 per 100 words = ~50, 10+ per 100 words = ~20
    const score = Math.max(0, Math.min(100, Math.round(100 - errorRate * 10)));
    return score;
}
