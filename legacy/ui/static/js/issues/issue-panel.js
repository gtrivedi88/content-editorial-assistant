/**
 * Issue Panel — manages the right sidebar: score, group list, cards, checking indicator.
 */

import { store } from '../state/store.js';
import { selectError, filterByGroup } from '../state/actions.js';
import { ScoreRing } from './score-ring.js';
import { GroupList } from './group-list.js';
import { CheckingIndicator } from './checking-indicator.js';
import { createIssueCard } from './issue-card.js';
import { getGroupMeta } from '../shared/style-guide-groups.js';
import { scrollToElement, createElement } from '../shared/dom-utils.js';

export class IssuePanel {
    constructor(panelEl, storeRef, editorController) {
        this._panel = panelEl;
        this._store = storeRef;
        this._editor = editorController;

        this._headerEl = panelEl.querySelector('.cea-issue-panel__header');
        this._bodyEl = panelEl.querySelector('.cea-issue-panel__body');
        this._footerEl = panelEl.querySelector('.cea-panel-footer');
        this._emptyState = panelEl.querySelector('.cea-empty-state');

        // Initialize sub-components
        this._scoreRing = new ScoreRing(this._headerEl, storeRef);
        this._groupList = new GroupList(this._bodyEl, storeRef);
        this._checkingIndicator = new CheckingIndicator(this._bodyEl, storeRef);

        this._bindSubscriptions();
    }

    _bindSubscriptions() {
        // Show cards when a group is drilled into
        this._store.subscribe('activeGroup', (group) => {
            if (group !== 'all') {
                this._showGroupDetail(group);
            } else {
                this._hideGroupDetail();
            }
        });

        // Re-render cards when filtered errors change (while in detail view)
        this._store.subscribe('filteredErrors', (errors) => {
            if (this._store.get('activeGroup') !== 'all') {
                this._renderCards(errors);
            }
        });

        // Highlight active card
        this._store.subscribe('selectedErrorId', (errorId) => {
            this._highlightCard(errorId);
        });

        // Show/hide panel sections based on analysis status
        this._store.subscribe('analysisStatus', (status) => {
            if (status === 'complete') {
                if (this._headerEl) this._headerEl.style.display = '';
                if (this._emptyState) this._emptyState.style.display = 'none';
                if (this._footerEl) this._footerEl.style.display = '';
            } else if (status === 'analyzing') {
                if (this._headerEl) this._headerEl.style.display = 'none';
                if (this._emptyState) this._emptyState.style.display = 'none';
                if (this._footerEl) this._footerEl.style.display = 'none';
            } else if (status === 'error') {
                if (this._headerEl) this._headerEl.style.display = 'none';
                if (this._footerEl) this._footerEl.style.display = 'none';
                if (this._emptyState) {
                    const msg = this._store.get('errorMessage') || 'Analysis failed';
                    this._emptyState.style.display = '';
                    this._emptyState.querySelector('.cea-empty-state__icon').innerHTML =
                        '<i class="fas fa-exclamation-triangle" style="color:var(--cea-color-issues)"></i>';
                    this._emptyState.querySelector('.cea-empty-state__title').textContent = 'Analysis failed';
                    this._emptyState.querySelector('.cea-empty-state__body').textContent = msg;
                }
            } else if (status === 'idle') {
                if (this._headerEl) this._headerEl.style.display = 'none';
                if (this._emptyState) {
                    this._emptyState.style.display = '';
                    this._emptyState.querySelector('.cea-empty-state__title').textContent = 'Ready to review';
                    this._emptyState.querySelector('.cea-empty-state__body').innerHTML =
                        'Paste or upload content to see inline suggestions.';
                    this._emptyState.querySelector('.cea-empty-state__icon').innerHTML =
                        '<i class="fas fa-spell-check"></i>';
                }
                if (this._footerEl) this._footerEl.style.display = 'none';
            }
        });

        // Show resolved counter
        this._store.subscribe('resolvedErrors', (resolved) => {
            this._updateResolvedCounter(resolved.size);
        });
    }

    _showGroupDetail(groupKey) {
        const meta = getGroupMeta(groupKey);
        const errors = this._store.get('filteredErrors');

        // Remove existing detail elements
        this._hideGroupDetail();

        // Back button
        const backBtn = createElement('button', {
            className: 'cea-group-back',
            innerHTML: '<i class="fas fa-arrow-left"></i> All categories',
            onClick: () => filterByGroup('all'),
        });

        // Detail title
        const title = createElement('div', {
            className: 'cea-group-detail-title',
            textContent: `${meta.label} \u2014 ${errors.length} issue${errors.length !== 1 ? 's' : ''}`,
        });

        // Cards container
        const cardsContainer = createElement('div', {
            className: 'cea-group-detail-cards',
        });

        this._backBtn = backBtn;
        this._detailTitle = title;
        this._cardsContainer = cardsContainer;

        this._bodyEl.insertBefore(cardsContainer, this._bodyEl.firstChild);
        this._bodyEl.insertBefore(title, cardsContainer);
        this._bodyEl.insertBefore(backBtn, title);

        // Hide the group list
        const groupListEl = this._bodyEl.querySelector('.cea-group-list');
        if (groupListEl) groupListEl.style.display = 'none';

        this._renderCards(errors);
    }

    _hideGroupDetail() {
        if (this._backBtn) { this._backBtn.remove(); this._backBtn = null; }
        if (this._detailTitle) { this._detailTitle.remove(); this._detailTitle = null; }
        if (this._cardsContainer) { this._cardsContainer.remove(); this._cardsContainer = null; }

        // Show group list again
        const groupListEl = this._bodyEl.querySelector('.cea-group-list');
        if (groupListEl) groupListEl.style.display = '';
    }

    _renderCards(errors) {
        const container = this._cardsContainer || this._bodyEl;

        // Remove existing cards
        const existingCards = container.querySelectorAll('.cea-issue-card');
        existingCards.forEach((c) => c.remove());

        // Remove existing resolved counter
        const existingCounter = container.querySelector('.cea-resolved-counter');
        if (existingCounter) existingCounter.remove();

        const editorEl = this._editor.getEditorElement();

        // Add resolved counter
        const totalErrors = this._store.get('errors').length +
            this._store.get('resolvedErrors').size +
            this._store.get('dismissedErrors').size;
        const resolved = this._store.get('resolvedErrors').size + this._store.get('dismissedErrors').size;

        if (totalErrors > 0 && this._store.get('activeGroup') !== 'all') {
            const counter = document.createElement('div');
            counter.className = 'cea-resolved-counter';
            counter.innerHTML = `<strong>${resolved}</strong> of ${totalErrors} issues addressed`;
            container.insertBefore(counter, container.firstChild);
        }

        // Render cards
        for (const error of errors) {
            const card = createIssueCard(error, editorEl);
            container.appendChild(card);
        }

        // Show empty state if no errors after analysis
        if (errors.length === 0 && this._store.get('analysisStatus') === 'complete') {
            if (this._emptyState) {
                this._emptyState.querySelector('.cea-empty-state__title').textContent = 'No issues found';
                this._emptyState.querySelector('.cea-empty-state__body').textContent =
                    'Your content looks good! No style issues detected.';
                this._emptyState.querySelector('.cea-empty-state__icon').innerHTML =
                    '<i class="fas fa-circle-check"></i>';
                this._emptyState.style.display = '';
            }
        }
    }

    _highlightCard(errorId) {
        // Remove previous active
        const prev = this._bodyEl.querySelector('.cea-issue-card--active');
        if (prev) prev.classList.remove('cea-issue-card--active');

        if (errorId) {
            const card = this._bodyEl.querySelector(`.cea-issue-card[data-error-id="${errorId}"]`);
            if (card) {
                card.classList.add('cea-issue-card--active');
                scrollToElement(card, 'nearest');
            }
        }
    }

    _updateResolvedCounter(count) {
        const counter = this._bodyEl.querySelector('.cea-resolved-counter');
        if (counter) {
            const totalErrors = this._store.get('errors').length + count + this._store.get('dismissedErrors').size;
            const total = count + this._store.get('dismissedErrors').size;
            counter.innerHTML = `<strong>${total}</strong> of ${totalErrors} issues addressed`;
        }
    }
}
