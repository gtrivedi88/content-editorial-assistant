/**
 * Issue Card — renders a single issue with accept/dismiss actions.
 */

import { acceptSuggestion, dismissError, selectError, submitFeedback } from '../state/actions.js';
import { getGroupMeta, formatRuleType } from '../shared/style-guide-groups.js';
import { createElement, escapeHtml } from '../shared/dom-utils.js';
import { replaceUnderlineText, removeUnderline } from '../editor/underline-renderer.js';

/**
 * Extract the replacement text from an instruction-style suggestion.
 * Examples:
 *   "Change 'functionality' to 'function'"  → "function"
 *   "Change 'functionality' to 'function'." → "function"
 *   "Use 'function' instead of 'functionality'" → "function"
 *   "Replace with 'function'" → "function"
 *   "do not" (raw replacement, e.g. contractions) → "do not"
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

    // If no instruction pattern found, use the suggestion as-is
    // (handles raw replacements like "do not" from contractions rule)
    return suggestion;
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

    // Header: neutral badge + rule name
    const header = createElement('div', { className: 'cea-issue-card__header' });
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

    // Suggestion
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

    // Actions
    const actions = createElement('div', { className: 'cea-issue-card__actions' });

    if (replacementText) {
        const acceptBtn = createElement('button', {
            className: 'cea-issue-btn cea-issue-btn--accept',
            textContent: 'Accept',
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

    // Citation
    if (error.style_guide_citation) {
        card.appendChild(createElement('div', {
            className: 'cea-issue-card__citation',
            innerHTML: `<i class="fas fa-book"></i> ${escapeHtml(error.style_guide_citation)}`,
        }));
    }

    return card;
}
