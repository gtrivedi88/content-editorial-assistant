/**
 * Inline Popup — floating tooltip near underlined text in the editor.
 *
 * Appears on underline click with category, message, suggestion chip(s),
 * and dismiss button. Does NOT expand the card in the right sidebar.
 * Follows the CitationPopover pattern: custom event, getBoundingClientRect,
 * click-outside dismiss, scroll dismiss.
 */

import { createElement, escapeHtml } from '../shared/dom-utils.js';
import { getCategory, getCategoryLabel } from '../shared/style-guide-groups.js';
import { extractReplacement, extractFromMessage } from '../issues/issue-card.js';
import { replaceUnderlineText, removeUnderline } from './underline-renderer.js';
import { acceptSuggestion, dismissError } from '../state/actions.js';

export class InlinePopup {
    constructor(store, editorEl) {
        this._store = store;
        this._editorEl = editorEl;
        this._popupEl = null;
        this._currentErrorId = null;
        this._currentMarkEl = null;
        this._clickOutsideHandler = null;
        this._scrollHandler = null;

        // Listen for underline click events
        globalThis.addEventListener('cea:show-inline-popup', (e) => {
            const { errorId, markEl } = e.detail;
            this._handleShow(errorId, markEl);
        });

        // Auto-hide when sidebar selection changes (card clicked in panel)
        this._store.subscribe('selectedErrorId', (errorId) => {
            if (errorId && this._popupEl) {
                this.hide();
            }
        });

        // Auto-hide when analysis restarts
        this._store.subscribe('analysisStatus', (status) => {
            if (status === 'analyzing' || status === 'idle') {
                this.hide();
            }
        });
    }

    /**
     * Handle show-inline-popup event.
     */
    _handleShow(errorId, markEl) {
        // Toggle off if same underline clicked again
        if (this._currentErrorId === errorId && this._popupEl) {
            this.hide();
            return;
        }

        // Hide any existing popup
        this.hide();

        // Look up the error from the store
        const errors = this._store.get('errors') || [];
        const error = errors.find(e => e.id === errorId);
        if (!error) return;

        this._currentErrorId = errorId;
        this._currentMarkEl = markEl;

        // Highlight the underline (Gap 2 fix)
        markEl.classList.add('cea-underline--active');

        // Build and show the popup
        this._createPopup(error, markEl);
    }

    /**
     * Build the popup DOM and position it near the mark element.
     */
    _createPopup(error, markEl) {
        const cat = getCategory(error);

        const popup = createElement('div', {
            className: 'cea-inline-popup',
            role: 'tooltip',
            'aria-live': 'polite',
        });

        // ── Header: category dot + label + close button ──
        const header = createElement('div', { className: 'cea-inline-popup__header' });

        header.appendChild(createElement('span', {
            className: `cea-inline-popup__dot cea-inline-popup__dot--${cat}`,
        }));
        header.appendChild(createElement('span', {
            className: 'cea-inline-popup__cat',
            textContent: getCategoryLabel(cat),
            dataset: { cat },
        }));

        const closeBtn = createElement('button', {
            className: 'cea-inline-popup__close',
            'aria-label': 'Close popup',
            innerHTML: '<i class="fas fa-xmark"></i>',
            onClick: () => this.hide(),
        });
        header.appendChild(closeBtn);
        popup.appendChild(header);

        // ── Body: error message ──
        popup.appendChild(createElement('div', {
            className: 'cea-inline-popup__body',
            textContent: error.message,
        }));

        // ── Actions: suggestion chips + dismiss ──
        const actions = createElement('div', { className: 'cea-inline-popup__actions' });

        // Suggestion chips (Gap 3 fix: render ALL deterministic alternatives)
        const allSuggestions = (error.suggestions || [])
            .map(s => extractReplacement(s, error.flagged_text))
            .filter(Boolean);

        // Use cached LLM rewrite if available (syncs with side panel)
        if (allSuggestions.length === 0 && error._llmSuggestion) {
            allSuggestions.push(error._llmSuggestion);
        }

        // Fallback: try extracting from message text
        if (allSuggestions.length === 0) {
            const msgText = extractFromMessage(error.message, error.flagged_text);
            if (msgText) allSuggestions.push(msgText);
        }

        if (allSuggestions.length > 0) {
            const chipsWrap = createElement('div', { className: 'cea-suggestion-chips' });
            for (const text of allSuggestions) {
                // Separate display from apply: LLM sentence-scope rewrites
                // show "Apply rewrite" but apply the full rewrite text
                const isLlmSentence = text === error._llmSuggestion
                    && error._llmScope === 'sentence';
                const displayText = isLlmSentence ? 'Apply rewrite' : text;
                const chip = createElement('button', {
                    className: 'cea-suggestion-chip',
                    textContent: displayText,
                    'aria-label': `Accept suggestion: ${escapeHtml(displayText)}`,
                    onClick: (e) => {
                        e.stopPropagation();
                        replaceUnderlineText(this._editorEl, error.id, text, error.sentence, error._llmScope);
                        acceptSuggestion(error.id);
                        this.hide();
                    },
                });
                chipsWrap.appendChild(chip);
            }
            actions.appendChild(chipsWrap);
        }

        // Dismiss button
        actions.appendChild(createElement('button', {
            className: 'cea-action-link',
            innerHTML: '<i class="fas fa-times"></i> Dismiss',
            'aria-label': `Dismiss issue: ${escapeHtml(error.message || '')}`,
            onClick: (e) => {
                e.stopPropagation();
                removeUnderline(this._editorEl, error.id);
                dismissError(error.id);
                this.hide();
            },
        }));

        popup.appendChild(actions);

        // Add to DOM and position
        document.body.appendChild(popup);
        this._popupEl = popup;
        this._positionPopup(markEl);

        // Entrance animation
        requestAnimationFrame(() => {
            popup.classList.add('cea-inline-popup--visible');
        });

        // Focus into popup for keyboard accessibility (Gap 4 fix)
        setTimeout(() => {
            if (this._popupEl) {
                this._popupEl.querySelector('.cea-suggestion-chip, .cea-action-link')?.focus();
            }
        }, 50);

        // Click outside to dismiss
        this._clickOutsideHandler = (e) => {
            if (this._popupEl &&
                !this._popupEl.contains(e.target) &&
                e.target !== markEl &&
                !markEl.contains(e.target)) {
                this.hide();
            }
        };
        setTimeout(() => {
            document.addEventListener('click', this._clickOutsideHandler);
        }, 0);

        // Scroll dismiss
        const editorArea = this._editorEl.closest('.cea-editor-area');
        if (editorArea) {
            this._scrollHandler = () => this.hide();
            editorArea.addEventListener('scroll', this._scrollHandler, { passive: true, once: true });
        }
    }

    /**
     * Position the popup below (or above) the mark element.
     */
    _positionPopup(markEl) {
        if (!this._popupEl || !markEl) return;

        const markRect = markEl.getBoundingClientRect();
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollLeft = window.scrollX || document.documentElement.scrollLeft;
        const viewportWidth = document.documentElement.clientWidth;
        const viewportHeight = document.documentElement.clientHeight;
        const popupWidth = 340;
        const gap = 8;

        // Default: position below
        let top = markRect.bottom + scrollTop + gap;
        let left = markRect.left + scrollLeft;
        let above = false;

        // Flip above if not enough space below
        const spaceBelow = viewportHeight - markRect.bottom;
        if (spaceBelow < 200) {
            top = markRect.top + scrollTop - gap;
            above = true;
        }

        // Prevent overflow right
        if (left + popupWidth > viewportWidth + scrollLeft - 8) {
            left = viewportWidth + scrollLeft - popupWidth - 8;
        }

        // Prevent overflow left
        if (left < scrollLeft + 8) {
            left = scrollLeft + 8;
        }

        // Arrow horizontal position relative to popup
        const markCenter = markRect.left + scrollLeft + (markRect.width / 2);
        const arrowLeft = Math.max(16, Math.min(markCenter - left, popupWidth - 16));

        this._popupEl.style.top = above ? '' : `${top}px`;
        this._popupEl.style.bottom = above ? `${document.documentElement.scrollHeight - (markRect.top + scrollTop) + gap}px` : '';
        this._popupEl.style.left = `${left}px`;
        this._popupEl.style.setProperty('--arrow-left', `${arrowLeft}px`);

        if (above) {
            this._popupEl.classList.add('cea-inline-popup--above');
        }
    }

    /**
     * Hide and remove the popup.
     */
    hide() {
        // Clean up active underline highlight (Gap 2 fix)
        if (this._currentMarkEl) {
            this._currentMarkEl.classList.remove('cea-underline--active');
            this._currentMarkEl = null;
        }

        if (this._popupEl) {
            this._popupEl.classList.remove('cea-inline-popup--visible');
            const el = this._popupEl;
            setTimeout(() => {
                if (el && el.parentNode) {
                    el.remove();
                }
            }, 200);
            this._popupEl = null;
        }

        if (this._clickOutsideHandler) {
            document.removeEventListener('click', this._clickOutsideHandler);
            this._clickOutsideHandler = null;
        }

        if (this._scrollHandler) {
            const editorArea = this._editorEl.closest('.cea-editor-area');
            if (editorArea) {
                editorArea.removeEventListener('scroll', this._scrollHandler);
            }
            this._scrollHandler = null;
        }

        this._currentErrorId = null;

        // Return focus to editor (Gap 4 fix)
        this._editorEl.focus();
    }
}
