/**
 * Issue Card — renders a single issue with accept/dismiss actions,
 * source badge, auto-fetched LLM suggestion, and citation link.
 *
 * LLM suggestions are auto-fetched on card creation, rate-limited
 * to 3 concurrent requests via a module-level queue.
 */

import { acceptSuggestion, dismissError, selectError, submitFeedback, getSuggestion, getCitation } from '../state/actions.js';
import { getGroupMeta, formatRuleType } from '../shared/style-guide-groups.js';
import { createElement, escapeHtml } from '../shared/dom-utils.js';
import { replaceUnderlineText, removeUnderline } from '../editor/underline-renderer.js';

// ---------------------------------------------------------------------------
// Rate-limited LLM suggestion request queue (max 3 concurrent)
// ---------------------------------------------------------------------------
const _MAX_CONCURRENT = 3;
const _pendingRequests = new Set();
const _requestQueue = [];
const _fetchedIssueIds = new Set();

/**
 * Enqueue a request function. Executes immediately if under concurrency
 * limit, otherwise queues for later.
 */
function _enqueueRequest(fn) {
    if (_pendingRequests.size < _MAX_CONCURRENT) {
        _executeRequest(fn);
    } else {
        _requestQueue.push(fn);
    }
}

/**
 * Execute a request function, tracking it in the pending set.
 * On completion, dequeues the next waiting request.
 */
function _executeRequest(fn) {
    const promise = fn();
    _pendingRequests.add(promise);
    promise.finally(() => {
        _pendingRequests.delete(promise);
        if (_requestQueue.length > 0) {
            _executeRequest(_requestQueue.shift());
        }
    });
}

/**
 * Clear the suggestion fetch deduplication cache.
 * Call when starting a new analysis to allow fresh suggestion fetches.
 */
export function clearSuggestionCache() {
    _fetchedIssueIds.clear();
    _requestQueue.length = 0;
}

/**
 * Extract the replacement text from an instruction-style suggestion.
 * Returns the concrete replacement text if one can be extracted, or
 * empty string if the suggestion is a general instruction (e.g.,
 * "Rewrite in active voice") that cannot be applied as a text swap.
 *
 * Examples:
 *   "Change 'functionality' to 'function'"  -> "function"
 *   "Change 'functionality' to 'function'." -> "function"
 *   "Use 'function' instead of 'functionality'" -> "function"
 *   "Replace with 'function'" -> "function"
 *   "do not" (raw replacement, e.g. contractions) -> "do not"
 *   "Rewrite in active voice: ..." -> "" (instruction, not a replacement)
 */
function extractReplacement(suggestion, flaggedText) {
    if (!suggestion) return '';

    // Pattern: "Change 'X' to 'Y'" or "Change 'X' to 'Y'."
    let m = suggestion.match(/[Cc]hange\s+'[^']+'\s+to\s+'([^']+)'/);
    if (m) return m[1];

    // Pattern: "Change to 'Y'" (no source term)
    m = suggestion.match(/[Cc]hange\s+to\s+'([^']+)'/);
    if (m) return m[1];

    // Pattern: "Use 'Y' instead of 'X'"
    m = suggestion.match(/[Uu]se\s+'([^']+)'\s+instead/);
    if (m) return m[1];

    // Pattern: "Replace 'X' with 'Y'" or "Replace with 'Y'"
    m = suggestion.match(/[Rr]eplace(?:\s+'[^']+')?\s+with\s+'([^']+)'/);
    if (m) return m[1];

    // Detect instruction-style suggestions that are NOT direct replacements.
    // These are editorial guidance (e.g., "Rewrite in active voice: make the
    // actor the subject") and should not be used as replacement text.
    // The LLM auto-fetch provides actual rewrite text for these cases.
    if (_isInstruction(suggestion, flaggedText)) {
        return '';
    }

    // Short, non-instruction text is used as-is
    // (handles raw replacements like "do not" from contractions rule)
    return suggestion;
}

/**
 * Detect whether a suggestion is a human-readable instruction rather than
 * a drop-in replacement text. Instructions contain directive verbs and are
 * typically much longer than the flagged text they refer to.
 */
function _isInstruction(suggestion, flaggedText) {
    // Instructions typically start with imperative verbs
    if (/^(Rewrite|Consider|Rephrase|Restructure|Break|Combine|Simplify|Avoid)\b/i.test(suggestion)) {
        return true;
    }

    // Suggestions significantly longer than the flagged text are likely instructions
    const flaggedLen = (flaggedText || '').length;
    if (suggestion.length > 80 && suggestion.length > flaggedLen * 3) {
        return true;
    }

    return false;
}

/**
 * Create a DOM element for an issue card.
 */
export function createIssueCard(error, editorEl) {
    const suggestion = error.suggestions?.[0] || '';
    const replacementText = extractReplacement(suggestion, error.flagged_text);

    const card = createElement('div', {
        className: 'cea-issue-card',
        dataset: { errorId: error.id },
        onClick: () => selectError(error.id),
    });

    // Header: source badge + rule type badge
    const header = createElement('div', { className: 'cea-issue-card__header' });

    // Source badge: "AI" for LLM-sourced, "Rule" for deterministic
    const isLlmSource = error.source && error.source.startsWith('llm');
    const sourceBadge = createElement('span', {
        className: `cea-issue-source-badge cea-issue-source-badge--${isLlmSource ? 'ai' : 'rule'}`,
        textContent: isLlmSource ? 'AI' : 'Rule',
        title: isLlmSource ? 'Detected by AI analysis' : 'Detected by deterministic rule',
    });
    header.appendChild(sourceBadge);

    header.appendChild(createElement('span', {
        className: 'cea-issue-type-badge',
        textContent: formatRuleType(error.type),
    }));
    card.appendChild(header);

    // Flagged text
    if (error.flagged_text) {
        const flagged = createElement('div', { className: 'cea-issue-card__flagged' });
        flagged.appendChild(createElement('span', {
            className: 'cea-issue-card__flagged-text',
            textContent: error.flagged_text,
        }));
        card.appendChild(flagged);
    }

    // Message
    card.appendChild(createElement('div', {
        className: 'cea-issue-card__message',
        textContent: error.message,
    }));

    // Deterministic suggestion (if available)
    if (replacementText) {
        const suggBox = createElement('div', { className: 'cea-issue-card__suggestion' });
        suggBox.appendChild(createElement('span', {
            className: 'cea-issue-card__suggestion-icon',
            innerHTML: '<i class="fas fa-arrow-right"></i>',
        }));
        suggBox.appendChild(createElement('span', {
            className: 'cea-issue-card__suggestion-text',
            textContent: replacementText,
        }));
        card.appendChild(suggBox);
    }

    // LLM suggestion container (populated async)
    const llmContainer = createElement('div', {
        className: 'cea-issue-card__llm-suggestion',
    });
    card.appendChild(llmContainer);

    // Actions
    const actions = createElement('div', { className: 'cea-issue-card__actions' });

    // Accept button — hoisted so _autoFetchSuggestion can update its handler
    let acceptBtn = null;
    if (replacementText) {
        acceptBtn = createElement('button', {
            className: 'cea-issue-btn cea-issue-btn--accept',
            textContent: 'Accept',
            'aria-label': `Accept suggestion for: ${escapeHtml(error.flagged_text || '')}`,
            onClick: (e) => {
                e.stopPropagation();
                replaceUnderlineText(editorEl, error.id, replacementText);
                acceptSuggestion(error.id);
            },
        });
        actions.appendChild(acceptBtn);
    }

    const dismissBtn = createElement('button', {
        className: 'cea-issue-btn cea-issue-btn--dismiss',
        textContent: 'Dismiss',
        'aria-label': `Dismiss issue: ${escapeHtml(error.message || '')}`,
        onClick: (e) => {
            e.stopPropagation();
            removeUnderline(editorEl, error.id);
            dismissError(error.id);
        },
    });
    actions.appendChild(dismissBtn);

    // Feedback buttons
    const thumbsUp = createElement('button', {
        className: 'cea-issue-btn cea-issue-btn--feedback',
        innerHTML: '<i class="fas fa-thumbs-up"></i>',
        title: 'Helpful',
        'aria-label': 'Mark this issue as helpful',
        onClick: (e) => {
            e.stopPropagation();
            submitFeedback(error, 'correct');
            thumbsUp.disabled = true;
            thumbsDown.disabled = true;
            thumbsUp.style.color = '#388400';
        },
    });

    const thumbsDown = createElement('button', {
        className: 'cea-issue-btn cea-issue-btn--feedback',
        innerHTML: '<i class="fas fa-thumbs-down"></i>',
        title: 'Not helpful',
        'aria-label': 'Mark this issue as not helpful',
        onClick: (e) => {
            e.stopPropagation();
            submitFeedback(error, 'incorrect');
            thumbsUp.disabled = true;
            thumbsDown.disabled = true;
            thumbsDown.style.color = '#c9190b';
        },
    });

    actions.appendChild(thumbsUp);
    actions.appendChild(thumbsDown);
    card.appendChild(actions);

    // Citation link — only show when a real citation string exists.
    // LLM issues have empty style_guide_citation; showing the raw rule_name
    // (e.g., "llm_style") leads to a 404 "Citation not available" popup.
    if (error.style_guide_citation) {
        const citationLink = createElement('button', {
            className: 'cea-issue-card__citation cea-citation-link',
            'aria-label': `View citation: ${escapeHtml(error.style_guide_citation)}`,
            onClick: (e) => {
                e.stopPropagation();
                _handleCitationClick(error.rule_name || error.type, e.currentTarget);
            },
        });
        citationLink.innerHTML = `<i class="fas fa-book"></i> ${escapeHtml(error.style_guide_citation)}`;
        card.appendChild(citationLink);
    }

    // Auto-fetch LLM suggestion (rate-limited, deduplicated)
    if (!_fetchedIssueIds.has(error.id)) {
        _fetchedIssueIds.add(error.id);
        _enqueueRequest(() => _autoFetchSuggestion(error, editorEl, card, llmContainer, acceptBtn, actions));
    }

    return card;
}

/**
 * Auto-fetch an LLM suggestion for the given issue.
 * Shows a spinner while loading, then renders the rewrite or fails silently.
 * Updates the Accept button to use the LLM rewrite text.
 */
async function _autoFetchSuggestion(error, editorEl, card, container, existingAcceptBtn, actionsEl) {
    // Show spinner
    container.innerHTML = '';
    const loadingEl = createElement('span', {
        className: 'cea-issue-card__llm-loading',
        role: 'status',
        'aria-live': 'polite',
    });
    loadingEl.innerHTML = '<span class="cea-suggestion-spinner"></span> Getting suggestion\u2026';
    container.appendChild(loadingEl);

    const result = await getSuggestion(error.id);

    // Card may have been removed while loading
    if (!card.isConnected) return;

    if (!result || result.error) {
        // Silently remove spinner, keep deterministic suggestion
        container.innerHTML = '';
        return;
    }

    const rewriteText = result.rewritten_text || result.suggestion || result.rewrite || '';
    if (!rewriteText) {
        container.innerHTML = '';
        return;
    }

    // Render LLM suggestion
    container.innerHTML = '';
    container.appendChild(createElement('span', {
        className: 'cea-issue-card__suggestion-icon',
        innerHTML: '<i class="fas fa-wand-magic-sparkles"></i>',
    }));
    container.appendChild(createElement('span', {
        className: 'cea-issue-card__suggestion-text',
        textContent: rewriteText,
    }));

    // Update or create Accept button to use LLM rewrite text
    if (existingAcceptBtn) {
        existingAcceptBtn.onclick = (e) => {
            e.stopPropagation();
            replaceUnderlineText(editorEl, error.id, rewriteText);
            acceptSuggestion(error.id);
        };
    } else if (actionsEl) {
        const newAcceptBtn = createElement('button', {
            className: 'cea-issue-btn cea-issue-btn--accept',
            textContent: 'Accept',
            'aria-label': `Accept suggestion for: ${escapeHtml(error.flagged_text || '')}`,
            onClick: (e) => {
                e.stopPropagation();
                replaceUnderlineText(editorEl, error.id, rewriteText);
                acceptSuggestion(error.id);
            },
        });
        actionsEl.insertBefore(newAcceptBtn, actionsEl.firstChild);
    }
}

/**
 * Handle citation link click.
 * Dispatches a custom event that the citation popover listens for.
 */
function _handleCitationClick(ruleType, anchorEl) {
    globalThis.dispatchEvent(new CustomEvent('cea:show-citation', {
        detail: {
            ruleType,
            anchorEl,
        },
    }));
}
