/**
 * Checking Indicator — Grammarly-style "Checking your content..." per-group checklist.
 * Shows all 11 IBM Style Guide groups sweeping from pending → active → done.
 * Stays visible throughout the entire analysis pipeline (deterministic + LLM)
 * and only hides when analysisStatus transitions to 'complete'.
 */

import { getAllGroups, getGroupMeta } from '../shared/style-guide-groups.js';
import { createElement } from '../shared/dom-utils.js';

export class CheckingIndicator {
    constructor(containerEl, store) {
        this._container = containerEl;
        this._store = store;
        this._el = null;
        this._groups = getAllGroups();

        store.subscribe('analysisStatus', (status) => {
            if (status === 'analyzing') {
                this._show();
            } else {
                this._hide();
            }
        });
    }

    _show() {
        this._hide();

        const wrapper = createElement('div', { className: 'cea-checking' });

        // Header
        const header = createElement('div', { className: 'cea-checking__header' });
        const icon = createElement('div', { className: 'cea-checking__icon' });
        icon.innerHTML = '<i class="fas fa-magnifying-glass"></i>';
        header.appendChild(icon);

        const info = createElement('div');
        info.appendChild(createElement('div', {
            className: 'cea-checking__title',
            textContent: 'Checking your content...',
        }));
        info.appendChild(createElement('div', {
            className: 'cea-checking__subtitle',
            textContent: 'Analyzing against IBM Style Guide',
        }));
        header.appendChild(info);
        wrapper.appendChild(header);

        // Group rows
        const groupsContainer = createElement('div', { className: 'cea-checking__groups' });
        for (const groupKey of this._groups) {
            const meta = getGroupMeta(groupKey);
            const row = createElement('div', {
                className: 'cea-checking__group cea-checking__group--pending',
                dataset: { group: groupKey },
            });
            row.appendChild(createElement('span', {
                className: 'cea-checking__group-icon',
                innerHTML: '<i class="fas fa-circle" style="font-size:6px"></i>',
            }));
            row.appendChild(createElement('span', { textContent: meta.label }));
            groupsContainer.appendChild(row);
        }
        wrapper.appendChild(groupsContainer);

        this._el = wrapper;
        this._container.insertBefore(wrapper, this._container.firstChild);

        // Start sweep animation
        this._startSweep();
    }

    _hide() {
        if (this._el) {
            this._el.remove();
            this._el = null;
        }
        if (this._sweepTimer) {
            clearTimeout(this._sweepTimer);
            this._sweepTimer = null;
        }
    }

    /**
     * Sweep through groups with a timed animation, independent of backend progress.
     * Each group transitions: pending → active (spinner) → done (check).
     * After all groups complete, shows an AI analysis phase with a spinner.
     */
    _startSweep() {
        if (!this._el) return;
        const rows = this._el.querySelectorAll('.cea-checking__group');
        let idx = 0;

        const next = () => {
            if (!this._el) return;

            // Mark previous as done
            if (idx > 0 && rows[idx - 1]) {
                rows[idx - 1].className = 'cea-checking__group cea-checking__group--done';
                rows[idx - 1].querySelector('.cea-checking__group-icon').innerHTML =
                    '<i class="fas fa-check"></i>';
            }

            // Mark current as active
            if (idx < rows.length) {
                rows[idx].className = 'cea-checking__group cea-checking__group--active';
                rows[idx].querySelector('.cea-checking__group-icon').innerHTML =
                    '<i class="fas fa-spinner fa-spin"></i>';
                idx++;
                this._sweepTimer = setTimeout(next, 350);
            } else {
                // All style groups done — show AI analysis phase
                this._showAiPhase();
            }
        };

        next();
    }

    /**
     * Show the AI analysis phase after style checks complete.
     * Updates the header and adds a spinner row that stays active
     * until _hide() removes the entire indicator.
     */
    _showAiPhase() {
        if (!this._el) return;

        const subtitle = this._el.querySelector('.cea-checking__subtitle');
        if (subtitle) {
            subtitle.textContent = 'Running AI-powered analysis';
        }

        const groupsContainer = this._el.querySelector('.cea-checking__groups');
        if (groupsContainer) {
            const aiRow = createElement('div', {
                className: 'cea-checking__group cea-checking__group--active',
            });
            aiRow.appendChild(createElement('span', {
                className: 'cea-checking__group-icon',
                innerHTML: '<i class="fas fa-spinner fa-spin"></i>',
            }));
            aiRow.appendChild(createElement('span', { textContent: 'AI-powered analysis' }));
            groupsContainer.appendChild(aiRow);
        }
    }
}
