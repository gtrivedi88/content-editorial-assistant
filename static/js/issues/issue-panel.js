/**
 * Issue Panel — manages the right sidebar: score ring, category chips,
 * flat issue card list, checking indicator, and resolved counter.
 *
 * Flat list design: all issues render in document order as discrete cards.
 * Category chips provide interactive filtering (click to toggle).
 * Lazy rendering: first 50 cards immediately, remainder in idle batches.
 */

import { ScoreRing } from './score-ring.js';
import { CheckingIndicator } from './checking-indicator.js';
import { createIssueCard } from './issue-card.js';
import { getCategory, getCategoryLabel } from '../shared/style-guide-groups.js';
import { scrollToElement, createElement } from '../shared/dom-utils.js';

export class IssuePanel {
    constructor(panelEl, storeRef, editorController) {
        this._panel = panelEl;
        this._store = storeRef;
        this._editor = editorController;
        this._activeCatFilter = null;
        this._lastRenderedErrors = null;

        this._headerEl = panelEl.querySelector('.cea-issue-panel__header');
        this._bodyEl = panelEl.querySelector('.cea-issue-panel__body');
        this._footerEl = panelEl.querySelector('.cea-panel-footer');
        this._emptyState = panelEl.querySelector('.cea-empty-state');

        // Initialize sub-components
        this._scoreRing = new ScoreRing(this._headerEl, storeRef);
        this._checkingIndicator = new CheckingIndicator(this._bodyEl, storeRef);

        // Create issue list container
        this._issueListEl = createElement('div', { className: 'cea-issue-list' });
        this._issueListEl.style.display = 'none';
        this._bodyEl.appendChild(this._issueListEl);

        // Chips container (inserted into header dynamically)
        this._chipsEl = null;

        this._bindSubscriptions();
    }

    _bindSubscriptions() {
        // Handle visibility based on analysis status
        this._store.subscribe('analysisStatus', (status) => {
            this._handleStatusChange(status);
        });

        // Render cards + chips when errors change while analysis is complete
        this._store.subscribe('errors', (errors) => {
            if (this._store.get('analysisStatus') === 'complete') {
                this._onResultsReady(errors);
            }
        });

        // Highlight active card
        this._store.subscribe('selectedErrorId', (errorId) => {
            this._highlightCard(errorId);
        });

        // Update resolved counter
        this._store.subscribe('resolvedErrors', (resolved) => {
            this._updateResolvedCounter(resolved.size);
        });
    }

    _handleStatusChange(status) {
        if (status === 'complete') {
            this._showCompleteState();
            this._onResultsReady(this._store.get('errors'));
        } else if (status === 'analyzing') {
            this._showAnalyzingState();
        } else if (status === 'error') {
            this._showErrorState();
        } else if (status === 'idle') {
            this._showIdleState();
        }
    }

    _showCompleteState() {
        if (this._headerEl) this._headerEl.style.display = '';
        if (this._emptyState) this._emptyState.style.display = 'none';
        if (this._footerEl) this._footerEl.style.display = '';
    }

    _showAnalyzingState() {
        if (this._headerEl) this._headerEl.style.display = 'none';
        if (this._emptyState) this._emptyState.style.display = 'none';
        if (this._footerEl) this._footerEl.style.display = 'none';
        this._issueListEl.style.display = 'none';
        this._removeChips();
        this._lastRenderedErrors = null;
    }

    _showErrorState() {
        if (this._headerEl) this._headerEl.style.display = 'none';
        if (this._footerEl) this._footerEl.style.display = 'none';
        this._issueListEl.style.display = 'none';
        this._removeChips();
        if (this._emptyState) {
            const msg = this._store.get('errorMessage') || 'Analysis failed';
            this._emptyState.style.display = '';
            this._emptyState.querySelector('.cea-empty-state__icon').innerHTML =
                '<i class="fas fa-exclamation-triangle" style="color:var(--cea-color-issues)"></i>';
            this._emptyState.querySelector('.cea-empty-state__title').textContent = 'Analysis failed';
            this._emptyState.querySelector('.cea-empty-state__body').textContent = msg;
        }
    }

    _showIdleState() {
        if (this._headerEl) this._headerEl.style.display = 'none';
        if (this._footerEl) this._footerEl.style.display = 'none';
        this._issueListEl.style.display = 'none';
        this._removeChips();
        this._lastRenderedErrors = null;
        if (this._emptyState) {
            this._emptyState.style.display = '';
            this._emptyState.querySelector('.cea-empty-state__title').textContent = 'Ready to review';
            this._emptyState.querySelector('.cea-empty-state__body').innerHTML =
                'Paste or upload content to see inline suggestions.';
            this._emptyState.querySelector('.cea-empty-state__icon').innerHTML =
                '<i class="fas fa-spell-check"></i>';
        }
    }

    /**
     * Render chips and cards when analysis results are ready.
     * Guards against double-render via reference equality check.
     */
    _onResultsReady(errors) {
        if (this._lastRenderedErrors === errors) return;
        this._lastRenderedErrors = errors;

        if (errors.length > 0) {
            this._renderChips(errors);
            this._renderCards(errors);
            this._issueListEl.style.display = '';
        } else {
            this._issueListEl.style.display = 'none';
            this._removeChips();
            this._showNoIssuesState();
        }
    }

    // ── Category Chips ──

    _renderChips(errors) {
        this._removeChips();

        const counts = { spelling: 0, grammar: 0, style: 0, punctuation: 0, structure: 0 };
        for (const error of errors) {
            const cat = getCategory(error);
            if (counts[cat] !== undefined) counts[cat]++;
        }

        const container = createElement('div', { className: 'cea-chips' });

        // "All" chip — always first, active by default
        const allChip = createElement('span', {
            className: 'cea-chip cea-chip--all cea-chip--active',
            dataset: { cat: 'all' },
        });
        allChip.appendChild(document.createTextNode(`${errors.length} All`));
        allChip.addEventListener('click', () => this._clearChipFilter());
        container.appendChild(allChip);

        for (const [cat, count] of Object.entries(counts)) {
            if (count === 0) continue;
            const chip = createElement('span', {
                className: `cea-chip cea-chip--${cat}`,
                dataset: { cat },
            });
            chip.appendChild(createElement('span', { className: 'cea-chip__dot' }));
            chip.appendChild(document.createTextNode(`${count} ${getCategoryLabel(cat)}`));
            chip.addEventListener('click', () => this._toggleChipFilter(cat));
            container.appendChild(chip);
        }

        if (this._headerEl) {
            this._headerEl.appendChild(container);
        }
        this._chipsEl = container;

        // Stagger visibility animation
        const chips = container.querySelectorAll('.cea-chip');
        chips.forEach((c, i) => {
            setTimeout(() => c.classList.add('cea-visible'), 400 + i * 80);
        });
    }

    _toggleChipFilter(cat) {
        if (this._activeCatFilter === cat) {
            this._clearChipFilter();
        } else {
            this._activeCatFilter = cat;
            if (this._chipsEl) {
                this._chipsEl.querySelectorAll('.cea-chip').forEach(c => c.classList.remove('cea-chip--active'));
                this._chipsEl.querySelector(`.cea-chip--${cat}`)?.classList.add('cea-chip--active');
            }
            this._filterCardsByCategory(cat);
        }
    }

    _clearChipFilter() {
        this._activeCatFilter = null;
        if (this._chipsEl) {
            this._chipsEl.querySelectorAll('.cea-chip').forEach(c => c.classList.remove('cea-chip--active'));
            const allChip = this._chipsEl.querySelector('.cea-chip--all');
            if (allChip) allChip.classList.add('cea-chip--active');
        }
        this._filterCardsByCategory(null);
    }

    /**
     * Show/hide cards based on category filter.
     * null = show all, otherwise show only matching data-cat.
     */
    _filterCardsByCategory(cat) {
        const cards = this._issueListEl.querySelectorAll('.cea-issue-card');
        for (const card of cards) {
            card.style.display = (!cat || card.dataset.cat === cat) ? '' : 'none';
        }
    }

    _removeChips() {
        if (this._chipsEl) {
            this._chipsEl.remove();
            this._chipsEl = null;
        }
        this._activeCatFilter = null;
    }

    // ── Card List ──

    /**
     * Render the flat issue card list with lazy loading.
     * First 50 cards render immediately; remainder in idle batches of 30.
     */
    _renderCards(errors) {
        this._issueListEl.innerHTML = '';
        this._activeCatFilter = null;

        const editorEl = this._editor.getEditorElement();
        const INITIAL_BATCH = 50;
        const BATCH_SIZE = 30;

        // Render first batch immediately
        const firstBatch = errors.slice(0, INITIAL_BATCH);
        for (const error of firstBatch) {
            this._issueListEl.appendChild(createIssueCard(error, editorEl));
        }

        // Render remaining in idle batches
        if (errors.length > INITIAL_BATCH) {
            this._renderRemainingCards(errors, INITIAL_BATCH, BATCH_SIZE, editorEl);
        }
    }

    _renderRemainingCards(errors, startIdx, batchSize, editorEl) {
        let idx = startIdx;
        const renderBatch = () => {
            const end = Math.min(idx + batchSize, errors.length);
            const fragment = document.createDocumentFragment();
            for (; idx < end; idx++) {
                fragment.appendChild(createIssueCard(errors[idx], editorEl));
            }
            this._issueListEl.appendChild(fragment);
            if (idx < errors.length) {
                (globalThis.requestIdleCallback || setTimeout)(renderBatch);
            }
        };
        (globalThis.requestIdleCallback || setTimeout)(renderBatch);
    }

    _showNoIssuesState() {
        if (this._emptyState) {
            this._emptyState.querySelector('.cea-empty-state__title').textContent = 'No issues found';
            this._emptyState.querySelector('.cea-empty-state__body').textContent =
                'Your content looks good! No style issues detected.';
            this._emptyState.querySelector('.cea-empty-state__icon').innerHTML =
                '<i class="fas fa-circle-check"></i>';
            this._emptyState.style.display = '';
        }
    }

    // ── Card Highlighting ──

    _highlightCard(errorId) {
        const prev = this._bodyEl.querySelector('.cea-card-active');
        if (prev) prev.classList.remove('cea-card-active');

        if (!errorId) return;

        const card = this._bodyEl.querySelector(`.cea-issue-card[data-error-id="${errorId}"]`);
        if (card) {
            card.classList.add('cea-card-active');
            scrollToElement(card, 'nearest');
        }
    }

    _updateResolvedCounter(count) {
        const counter = this._bodyEl.querySelector('.cea-resolved-counter');
        if (!counter) return;
        const totalErrors = this._store.get('errors').length + count + this._store.get('dismissedErrors').size;
        const total = count + this._store.get('dismissedErrors').size;
        counter.innerHTML = `<strong>${total}</strong> of ${totalErrors} issues addressed`;
    }
}
