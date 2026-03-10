/**
 * Issue Card — renders a single issue with accept/dismiss actions,
 * source badge, auto-fetched LLM suggestion, and citation link.
 *
 * LLM suggestions are auto-fetched on card creation, rate-limited
 * to 3 concurrent requests via a module-level queue.
 */

import { acceptSuggestion, dismissError, manuallyFixError, selectError, submitFeedback, getSuggestion, getCitation } from '../state/actions.js';
import { getGroupMeta, formatRuleType, getCategory, getCategoryLabel } from '../shared/style-guide-groups.js';
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
export function extractReplacement(suggestion, flaggedText) {
    if (!suggestion) return '';

    // Pattern: "Change 'X' to 'Y'" or "Change 'X' to 'Y'."
    let m = suggestion.match(/[Cc]hange\s+['"`][^'"`]+['"`]\s+to\s+['"`]([^'"`]+)['"`]/);
    if (m) return m[1];

    // Pattern: "Change to 'Y'" (no source term)
    m = suggestion.match(/[Cc]hange\s+to\s+['"`]([^'"`]+)['"`]/);
    if (m) return m[1];

    // Pattern: "Use 'Y' instead of 'X'"
    m = suggestion.match(/[Uu]se\s+['"`]([^'"`]+)['"`]\s+instead/);
    if (m) return m[1];

    // Pattern: "Replace 'X' with 'Y'" or "Replace with 'Y'"
    m = suggestion.match(/[Rr]eplace(?:\s+['"`][^'"`]+['"`])?\s+with\s+['"`]([^'"`]+)['"`]/);
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
    if (/^(Rewrite|Consider|Rephrase|Restructure|Replace|Remove|Break|Combine|Simplify|Avoid|Insert|Add|Move|Split|Write|Do not|Ensure|Verify|Check)\b/i.test(suggestion)) {
        return true;
    }

    // Suggestions significantly longer than the flagged text are likely instructions
    const flaggedLen = (flaggedText || '').length;
    if (suggestion.length > 50 && suggestion.length > flaggedLen * 3) {
        return true;
    }

    return false;
}

/**
 * Extract a concrete replacement from an issue message string.
 * Many rule messages embed the alternative as a quoted term
 * (e.g., "Use 'inactive' instead of 'disabled'").
 * Returns the extracted text with case matching, or empty string.
 */
export function extractFromMessage(message, flaggedText) {
    if (!message) return '';

    // "Use 'Y' instead"
    let m = message.match(/(?<!\bnot )(?<!\bnot\s)[Uu]se\s+['"`]([^'"`]+)['"`]/);
    if (m) return _matchCase(m[1], flaggedText);

    // "Change to 'Y'" or "Change 'X' to 'Y'"
    m = message.match(/[Cc]hange\s+(?:['"`][^'"`]+['"`]\s+)?to\s+['"`]([^'"`]+)['"`]/);
    if (m) return _matchCase(m[1], flaggedText);

    // "Replace with 'Y'" or "Replace 'X' with 'Y'"
    m = message.match(/[Rr]eplace\s+(?:['"`][^'"`]+['"`]\s+)?with\s+['"`]([^'"`]+)['"`]/);
    if (m) return _matchCase(m[1], flaggedText);

    // "Write 'Y'"
    m = message.match(/[Ww]rite\s+['"`]([^'"`]+)['"`]/);
    if (m) return _matchCase(m[1], flaggedText);

    // "Refer to ... as 'Y'"
    m = message.match(/[Rr]efer\s+to\s+\S+\s+\S+\s+as\s+['"`]([^'"`]+)['"`]/);
    if (m) return _matchCase(m[1], flaggedText);

    return '';
}

/**
 * Capitalize replacement if flagged text starts uppercase.
 */
function _matchCase(replacement, flaggedText) {
    if (flaggedText && flaggedText[0] === flaggedText[0].toUpperCase()
        && flaggedText[0] !== flaggedText[0].toLowerCase() && replacement) {
        return replacement[0].toUpperCase() + replacement.slice(1);
    }
    return replacement;
}

/**
 * Create a DOM element for an issue card.
 * Two-tier structure: summary row (always visible) + expandable detail.
 */
export function createIssueCard(error, editorEl) {
    const cat = getCategory(error);

    const card = createElement('div', {
        className: 'cea-issue-card',
        dataset: { errorId: error.id, cat },
        onClick: () => selectError(error.id),
    });

    // ── Summary row (always visible) ──
    const summary = createElement('div', { className: 'cea-card-summary' });

    summary.appendChild(createElement('span', {
        className: `cea-card-dot cea-card-dot--${cat}`,
    }));

    const textEl = createElement('div', { className: 'cea-card-text' });
    const flagged = error.flagged_text || '';
    const truncated = flagged.length > 30 ? flagged.slice(0, 30) + '\u2026' : flagged;

    textEl.appendChild(createElement('span', {
        className: 'cea-card-word',
        textContent: truncated,
    }));
    textEl.appendChild(createElement('span', {
        className: 'cea-card-sep',
        textContent: ' \u2013 ',
    }));
    textEl.appendChild(createElement('span', {
        className: 'cea-card-desc',
        textContent: formatRuleType(error.type),
    }));

    summary.appendChild(textEl);
    card.appendChild(summary);

    // ── Expandable detail ──
    const detail = createElement('div', { className: 'cea-card-detail' });
    const detailWrap = createElement('div', { className: 'cea-card-detail-wrap' });
    const detailInner = createElement('div', { className: 'cea-card-detail-inner' });

    // Category label
    const catLabel = createElement('div', {
        className: 'cea-detail-cat',
        dataset: { cat },
    });
    catLabel.appendChild(document.createTextNode(getCategoryLabel(cat)));
    if (error.style_guide_citation) {
        catLabel.appendChild(createElement('i', {
            className: 'fas fa-circle-info',
            title: error.style_guide_citation,
        }));
    }
    detailInner.appendChild(catLabel);

    // Message
    detailInner.appendChild(createElement('div', {
        className: 'cea-detail-msg',
        textContent: error.message,
    }));

    // Suggestion chips — extract all deterministic alternatives
    const allSuggestions = (error.suggestions || [])
        .map(s => extractReplacement(s, error.flagged_text))
        .filter(Boolean);

    let firstChip = null;

    if (allSuggestions.length === 1) {
        firstChip = _createSuggestionChip(allSuggestions[0], error, editorEl);
        detailInner.appendChild(firstChip);
    } else if (allSuggestions.length > 1) {
        const chipsWrapper = createElement('div', { className: 'cea-suggestion-chips' });
        for (const text of allSuggestions) {
            const chip = _createSuggestionChip(text, error, editorEl);
            if (!firstChip) firstChip = chip;
            chipsWrapper.appendChild(chip);
        }
        detailInner.appendChild(chipsWrapper);
    }

    // LLM suggestion container (populated async)
    const llmContainer = createElement('div', {
        className: 'cea-issue-card__llm-suggestion',
    });
    detailInner.appendChild(llmContainer);

    // Action links
    const actions = createElement('div', { className: 'cea-detail-actions' });

    actions.appendChild(createElement('button', {
        className: 'cea-action-link',
        innerHTML: '<i class="fas fa-times"></i> Dismiss',
        'aria-label': `Dismiss issue: ${escapeHtml(error.message || '')}`,
        onClick: (e) => {
            e.stopPropagation();
            removeUnderline(editorEl, error.id);
            dismissError(error.id);
        },
    }));

    actions.appendChild(createElement('button', {
        className: 'cea-action-link',
        innerHTML: '<i class="fas fa-check"></i> I fixed it',
        title: 'I fixed this issue manually',
        'aria-label': `Mark as manually fixed: ${escapeHtml(error.message || '')}`,
        onClick: (e) => {
            e.stopPropagation();
            removeUnderline(editorEl, error.id);
            manuallyFixError(error.id);
        },
    }));

    // Feedback buttons
    const thumbsUp = createElement('button', {
        className: 'cea-action-link',
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
        className: 'cea-action-link',
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
    detailInner.appendChild(actions);

    // Citation link
    if (error.style_guide_citation) {
        const citation = createElement('div', { className: 'cea-detail-citation' });
        const citBtn = createElement('button', {
            'aria-label': `View citation: ${escapeHtml(error.style_guide_citation)}`,
            onClick: (e) => {
                e.stopPropagation();
                _handleCitationClick(error.rule_name || error.type, e.currentTarget);
            },
        });
        citBtn.innerHTML = `<i class="fas fa-book"></i> ${escapeHtml(error.style_guide_citation)}`;
        citation.appendChild(citBtn);
        detailInner.appendChild(citation);
    }

    detailWrap.appendChild(detailInner);
    detail.appendChild(detailWrap);
    card.appendChild(detail);

    // Auto-fetch LLM suggestion (rate-limited, deduplicated)
    if (!_fetchedIssueIds.has(error.id)) {
        _fetchedIssueIds.add(error.id);
        _enqueueRequest(() => _autoFetchSuggestion(error, editorEl, card, llmContainer, firstChip));
    }

    return card;
}

/**
 * Create a suggestion chip button.
 */
function _createSuggestionChip(text, error, editorEl) {
    return createElement('button', {
        className: 'cea-suggestion-chip',
        textContent: text,
        'aria-label': `Accept suggestion: ${escapeHtml(text)}`,
        onClick: (e) => {
            e.stopPropagation();
            replaceUnderlineText(editorEl, error.id, text);
            acceptSuggestion(error.id);
        },
    });
}

/**
 * Try to create a fallback suggestion chip when the LLM call fails.
 * Returns true if a chip was inserted, false otherwise.
 */
function _tryFallbackChip(error, editorEl, container) {
    // Try suggestions from the error response
    if (error.suggestions?.length > 0) {
        const text = extractReplacement(error.suggestions[0], error.flagged_text);
        if (text) {
            container.innerHTML = '';
            container.parentNode.insertBefore(_createSuggestionChip(text, error, editorEl), container);
            return true;
        }
    }
    // Try extracting replacement from issue message text
    if (error.message) {
        const msgText = extractFromMessage(error.message, error.flagged_text);
        if (msgText) {
            container.innerHTML = '';
            container.parentNode.insertBefore(_createSuggestionChip(msgText, error, editorEl), container);
            return true;
        }
    }
    return false;
}

/**
 * Auto-fetch an LLM suggestion for the given issue.
 * Shows a spinner while loading, then renders the rewrite or fails silently.
 * Updates the first suggestion chip to use the LLM rewrite text when available.
 */
async function _autoFetchSuggestion(error, editorEl, card, container, existingChip) {
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
        if (existingChip) container.innerHTML = '';
        else _tryFallbackChip(error, editorEl, container);
        return;
    }

    const rewriteText = result.rewritten_text || result.suggestion || result.rewrite || '';
    if (!rewriteText) {
        container.innerHTML = '';
        return;
    }

    // Clear spinner
    container.innerHTML = '';

    // Update existing chip or create new one
    if (existingChip) {
        // LLM rewrite is higher quality — update first chip's handler
        existingChip.onclick = (e) => {
            e.stopPropagation();
            replaceUnderlineText(editorEl, error.id, rewriteText);
            acceptSuggestion(error.id);
        };
    } else {
        // No deterministic suggestion — create chip with LLM text
        const chip = _createSuggestionChip(rewriteText, error, editorEl);
        container.parentNode.insertBefore(chip, container);
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
