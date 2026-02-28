/**
 * Margin Labels — left-margin annotation labels next to errors in the editor.
 * Labels are positioned absolutely using getBoundingClientRect() relative to
 * the editor wrapper. They show/hide based on active group selection.
 */

import { selectError } from '../state/actions.js';

export class MarginLabels {
    constructor(editorEl, marginContainer, store) {
        this._editor = editorEl;
        this._container = marginContainer;
        this._store = store;
        this._resizeObserver = null;

        // Rebuild labels when errors change (after analysis)
        store.subscribe('errors', (errors) => {
            if (store.get('analysisStatus') === 'complete' && errors.length > 0) {
                // Delay to let underlines render first
                requestAnimationFrame(() => this._buildLabels());
            } else if (errors.length === 0) {
                this._clear();
            }
        });

        // Show/hide labels for active group
        store.subscribe('activeGroup', (group) => {
            this._showForGroup(group);
        });

        // Highlight active label when an error is selected
        store.subscribe('selectedErrorId', (errorId) => {
            this._highlightLabel(errorId);
        });

        // Reposition on scroll
        const editorArea = editorEl.closest('.cea-editor-area');
        if (editorArea) {
            editorArea.addEventListener('scroll', this._debounce(() => {
                this._repositionLabels();
            }, 100));
        }

        // Reposition on resize
        this._resizeObserver = new ResizeObserver(this._debounce(() => {
            this._repositionLabels();
        }, 150));
        this._resizeObserver.observe(editorEl);

        // Click handler for labels
        this._container.addEventListener('click', (e) => {
            const label = e.target.closest('.cea-margin-label');
            if (label) {
                selectError(label.dataset.error);
            }
        });
    }

    _clear() {
        this._container.innerHTML = '';
    }

    _buildLabels() {
        this._container.innerHTML = '';
        const wrapperRect = this._editor.closest('.cea-editor-wrapper').getBoundingClientRect();
        const marks = this._editor.querySelectorAll('.cea-underline');

        for (const mark of marks) {
            const errorId = mark.dataset.errorId;
            const group = mark.dataset.group;
            const labelText = this._getShortLabel(mark.getAttribute('aria-label'));
            if (!labelText) continue;

            const markRect = mark.getBoundingClientRect();
            const top = markRect.top - wrapperRect.top + (markRect.height / 2) - 10;

            const label = document.createElement('div');
            label.className = 'cea-margin-label';
            label.dataset.group = group;
            label.dataset.error = errorId;
            label.textContent = labelText;
            label.style.top = top + 'px';
            this._container.appendChild(label);
        }

        // De-overlap
        this._deOverlap();

        // Show labels for current active group
        this._showForGroup(this._store.get('activeGroup'));
    }

    _getShortLabel(message) {
        if (!message) return '';
        // Take up to first period or comma, truncated to ~30 chars
        const clause = message.split(/[.,;!?]/)[0].trim();
        if (clause.length <= 30) return clause;
        return clause.substring(0, 27) + '...';
    }

    _deOverlap() {
        const labels = [...this._container.querySelectorAll('.cea-margin-label')];
        const labelHeight = 24; // approximate height of a label + gap

        for (let i = 1; i < labels.length; i++) {
            const prevTop = parseFloat(labels[i - 1].style.top);
            const currTop = parseFloat(labels[i].style.top);
            if (currTop - prevTop < labelHeight) {
                labels[i].style.top = (prevTop + labelHeight) + 'px';
            }
        }
    }

    _showForGroup(group) {
        const labels = this._container.querySelectorAll('.cea-margin-label');
        for (const label of labels) {
            if (group === 'all') {
                label.classList.remove('visible');
            } else if (label.dataset.group === group) {
                label.classList.add('visible');
            } else {
                label.classList.remove('visible');
            }
        }
    }

    _highlightLabel(errorId) {
        const labels = this._container.querySelectorAll('.cea-margin-label');
        for (const label of labels) {
            label.classList.toggle('cea-margin-label--active', label.dataset.error === errorId);
        }
    }

    _repositionLabels() {
        if (this._container.children.length === 0) return;
        const wrapperRect = this._editor.closest('.cea-editor-wrapper').getBoundingClientRect();
        const marks = this._editor.querySelectorAll('.cea-underline');
        const labelMap = {};

        // Map labels by error ID
        for (const label of this._container.querySelectorAll('.cea-margin-label')) {
            labelMap[label.dataset.error] = label;
        }

        for (const mark of marks) {
            const label = labelMap[mark.dataset.errorId];
            if (!label) continue;
            const markRect = mark.getBoundingClientRect();
            const top = markRect.top - wrapperRect.top + (markRect.height / 2) - 10;
            label.style.top = top + 'px';
        }

        this._deOverlap();
    }

    _debounce(fn, delay) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn.apply(this, args), delay);
        };
    }
}
