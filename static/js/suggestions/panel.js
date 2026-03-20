/**
 * Suggestion Panel — on "Get Suggestion" click, shows loading spinner,
 * calls POST /api/v1/suggestions, renders original vs rewritten text.
 * "Apply" button replaces text in editor using range-based DOM replacement.
 * Accessible: focus management, ARIA live region for loading state.
 */

import { getSuggestion } from '../state/actions.js';
import { createElement, escapeHtml } from '../shared/dom-utils.js';
import { replaceUnderlineText } from '../editor/underline-renderer.js';
import { acceptSuggestion } from '../state/actions.js';

export class SuggestionPanel {
    constructor(editorController) {
        this._editor = editorController;
        this._currentPanel = null;

        // Listen for suggestion request events from issue cards
        globalThis.addEventListener('cea:get-suggestion', (e) => {
            const { error, editorEl, anchorEl } = e.detail;
            this._handleSuggestionRequest(error, editorEl, anchorEl);
        });
    }

    /**
     * Handle a "Get Suggestion" request.
     * Shows loading state, fetches suggestion, renders result.
     */
    async _handleSuggestionRequest(error, editorEl, anchorEl) {
        // Remove any existing suggestion panel
        this._removePanel();

        // Create panel with loading state
        const panel = this._createPanel(error, anchorEl);
        this._currentPanel = panel;

        // Show loading
        const body = panel.querySelector('.cea-suggestion-panel__body');
        body.innerHTML = '';
        const loadingEl = createElement('div', {
            className: 'cea-suggestion-loading',
            role: 'status',
            'aria-live': 'assertive',
        });
        loadingEl.innerHTML = '<span class="cea-suggestion-spinner"></span> Getting AI suggestion...';
        body.appendChild(loadingEl);

        // Fetch suggestion
        const result = await getSuggestion(error.id);

        // Guard: panel may have been removed while loading
        if (this._currentPanel !== panel) return;

        if (!result || result.error) {
            body.innerHTML = '';
            body.appendChild(createElement('div', {
                className: 'cea-suggestion-error',
                role: 'alert',
            }, [
                createElement('i', { className: 'fas fa-exclamation-circle' }),
                document.createTextNode(result?.error || 'Could not generate suggestion'),
            ]));
            return;
        }

        // Render suggestion result
        this._renderSuggestion(body, error, result, editorEl);
    }

    /**
     * Create the suggestion panel container and insert it after the anchor card.
     */
    _createPanel(error, anchorEl) {
        const panel = createElement('div', {
            className: 'cea-suggestion-panel',
            'aria-label': 'AI suggestion panel',
        });

        // Header
        const header = createElement('div', { className: 'cea-suggestion-panel__header' });
        header.appendChild(createElement('span', {
            textContent: 'AI Suggestion',
        }));

        const closeBtn = createElement('button', {
            className: 'cea-citation-popover__close',
            'aria-label': 'Close suggestion panel',
            innerHTML: '<i class="fas fa-xmark"></i>',
            onClick: () => this._removePanel(),
        });
        header.appendChild(closeBtn);
        panel.appendChild(header);

        // Body (will be populated with loading or results)
        panel.appendChild(createElement('div', { className: 'cea-suggestion-panel__body' }));

        // Insert after the anchor card
        if (anchorEl && anchorEl.parentNode) {
            anchorEl.parentNode.insertBefore(panel, anchorEl.nextSibling);
        } else {
            document.body.appendChild(panel);
        }

        return panel;
    }

    /**
     * Render the suggestion with original vs rewrite diff and apply button.
     */
    _renderSuggestion(body, error, result, editorEl) {
        body.innerHTML = '';

        // Original text
        const originalSection = createElement('div', { className: 'cea-suggestion-original' });
        originalSection.appendChild(createElement('span', {
            className: 'cea-suggestion-original__label',
            textContent: 'Original',
        }));
        const originalText = createElement('span');
        originalText.textContent = error.flagged_text || '';
        originalSection.appendChild(originalText);
        body.appendChild(originalSection);

        // Rewritten text
        const rewriteSection = createElement('div', { className: 'cea-suggestion-rewrite' });
        rewriteSection.appendChild(createElement('span', {
            className: 'cea-suggestion-rewrite__label',
            textContent: 'Suggested',
        }));
        const rewriteText = result.suggestion || result.rewrite || '';
        const rewriteSpan = createElement('span');
        rewriteSpan.textContent = rewriteText;
        rewriteSection.appendChild(rewriteSpan);
        body.appendChild(rewriteSection);

        // Explanation (if provided)
        if (result.explanation) {
            const explanationEl = createElement('div', {
                className: 'cea-issue-card__message',
                style: { marginBottom: '12px', fontSize: '0.85rem' },
            });
            explanationEl.textContent = result.explanation;
            body.appendChild(explanationEl);
        }

        // Actions
        const actions = createElement('div', { className: 'cea-suggestion-panel__actions' });

        const applyBtn = createElement('button', {
            className: 'cea-suggestion-apply-btn',
            'aria-label': 'Apply this suggestion to the editor',
            onClick: () => {
                replaceUnderlineText(editorEl, error.id, rewriteText, error.sentence, error._llmScope);
                acceptSuggestion(error.id);
                this._removePanel();
            },
        });
        applyBtn.innerHTML = '<i class="fas fa-check"></i> Apply';
        actions.appendChild(applyBtn);

        const cancelBtn = createElement('button', {
            className: 'cea-issue-btn cea-issue-btn--dismiss',
            textContent: 'Cancel',
            'aria-label': 'Cancel and close suggestion panel',
            onClick: () => this._removePanel(),
        });
        actions.appendChild(cancelBtn);

        body.appendChild(actions);

        // Focus the apply button for keyboard accessibility
        requestAnimationFrame(() => {
            applyBtn.focus();
        });
    }

    /**
     * Remove the current suggestion panel.
     */
    _removePanel() {
        if (this._currentPanel) {
            this._currentPanel.remove();
            this._currentPanel = null;
        }
    }
}
