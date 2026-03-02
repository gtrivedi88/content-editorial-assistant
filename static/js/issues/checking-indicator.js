/**
 * Checking Indicator — Real-time progress driven by Socket.IO stage_progress events.
 * Shows all 11 IBM Style Guide groups, then AI Analysis and Global Review phases.
 * Progress is driven by backend events, not timer-based animation.
 */

import { getAllGroups, getGroupMeta } from '../shared/style-guide-groups.js';
import { createElement } from '../shared/dom-utils.js';

export class CheckingIndicator {
    constructor(containerEl, store) {
        this._container = containerEl;
        this._store = store;
        this._el = null;
        this._groups = getAllGroups();
        this._aiRow = null;
        this._globalRow = null;

        store.subscribe('analysisStatus', (status) => {
            if (status === 'analyzing') {
                this._show();
            } else {
                this._hide();
            }
        });

        store.subscribe('stageProgress', (data) => {
            if (data) this._onStageProgress(data);
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

        // Group rows — start all as active (spinning) since deterministic runs fast
        const groupsContainer = createElement('div', { className: 'cea-checking__groups' });
        for (const groupKey of this._groups) {
            const meta = getGroupMeta(groupKey);
            const row = createElement('div', {
                className: 'cea-checking__group cea-checking__group--active',
                dataset: { group: groupKey },
            });
            row.appendChild(createElement('span', {
                className: 'cea-checking__group-icon',
                innerHTML: '<i class="fas fa-spinner fa-spin"></i>',
            }));
            row.appendChild(createElement('span', { textContent: meta.label }));
            groupsContainer.appendChild(row);
        }
        wrapper.appendChild(groupsContainer);

        this._el = wrapper;
        this._aiRow = null;
        this._globalRow = null;
        this._container.insertBefore(wrapper, this._container.firstChild);
    }

    _hide() {
        if (this._el) {
            this._el.remove();
            this._el = null;
        }
        this._aiRow = null;
        this._globalRow = null;
    }

    /**
     * Handle stage_progress events from the backend.
     * Transitions the UI through deterministic → AI Analysis → Global Review.
     */
    _onStageProgress(data) {
        if (!this._el) return;

        if (data.phase === 'deterministic' && data.status === 'done') {
            this._markAllGroupsDone();
            this._showAiPhase(data.blocks_total);
        } else if (data.phase === 'llm_granular') {
            if (data.status === 'started') {
                this._markAllGroupsDone();
                this._showAiPhase(data.blocks_total);
            } else if (data.status === 'progress') {
                this._updateAiProgress(data.blocks_done, data.blocks_total);
            } else if (data.status === 'done') {
                this._markAiDone();
                this._showGlobalPhase();
            }
        } else if (data.phase === 'llm_global') {
            if (data.status === 'started') {
                this._markAiDone();
                this._showGlobalPhase();
            } else if (data.status === 'done') {
                this._markGlobalDone();
            }
        }
    }

    /**
     * Mark all style guide group rows as done (checkmark).
     */
    _markAllGroupsDone() {
        if (!this._el) return;
        const rows = this._el.querySelectorAll('.cea-checking__group[data-group]');
        for (const row of rows) {
            row.className = 'cea-checking__group cea-checking__group--done';
            row.querySelector('.cea-checking__group-icon').innerHTML =
                '<i class="fas fa-check"></i>';
        }
    }

    /**
     * Show the AI analysis phase row with block count.
     */
    _showAiPhase(blocksTotal) {
        if (!this._el || this._aiRow) return;

        const subtitle = this._el.querySelector('.cea-checking__subtitle');
        if (subtitle) {
            subtitle.textContent = 'Running AI-powered analysis';
        }

        const groupsContainer = this._el.querySelector('.cea-checking__groups');
        if (groupsContainer) {
            const label = blocksTotal
                ? `AI-powered analysis (${blocksTotal} blocks)`
                : 'AI-powered analysis';
            const aiRow = createElement('div', {
                className: 'cea-checking__group cea-checking__group--active',
            });
            aiRow.appendChild(createElement('span', {
                className: 'cea-checking__group-icon',
                innerHTML: '<i class="fas fa-spinner fa-spin"></i>',
            }));
            aiRow.appendChild(createElement('span', { textContent: label }));
            groupsContainer.appendChild(aiRow);
            this._aiRow = aiRow;
        }
    }

    /**
     * Update the AI analysis row with per-block progress.
     */
    _updateAiProgress(blocksDone, blocksTotal) {
        if (!this._aiRow) return;
        const label = this._aiRow.querySelector('span:last-child');
        if (label) {
            label.textContent = `AI-powered analysis (${blocksDone}/${blocksTotal} blocks)`;
        }
    }

    /**
     * Mark the AI analysis row as done.
     */
    _markAiDone() {
        if (this._aiRow) {
            this._aiRow.className = 'cea-checking__group cea-checking__group--done';
            this._aiRow.querySelector('.cea-checking__group-icon').innerHTML =
                '<i class="fas fa-check"></i>';
        }
    }

    /**
     * Show the Global Review phase row.
     */
    _showGlobalPhase() {
        if (!this._el || this._globalRow) return;

        const subtitle = this._el.querySelector('.cea-checking__subtitle');
        if (subtitle) {
            subtitle.textContent = 'Running global review';
        }

        const groupsContainer = this._el.querySelector('.cea-checking__groups');
        if (groupsContainer) {
            const globalRow = createElement('div', {
                className: 'cea-checking__group cea-checking__group--active',
            });
            globalRow.appendChild(createElement('span', {
                className: 'cea-checking__group-icon',
                innerHTML: '<i class="fas fa-spinner fa-spin"></i>',
            }));
            globalRow.appendChild(createElement('span', { textContent: 'Global review' }));
            groupsContainer.appendChild(globalRow);
            this._globalRow = globalRow;
        }
    }

    /**
     * Mark the Global Review row as done.
     */
    _markGlobalDone() {
        if (this._globalRow) {
            this._globalRow.className = 'cea-checking__group cea-checking__group--done';
            this._globalRow.querySelector('.cea-checking__group-icon').innerHTML =
                '<i class="fas fa-check"></i>';
        }
    }
}
