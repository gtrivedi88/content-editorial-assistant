/**
 * Group List — IBM Style Guide group list with issue counts.
 * Replaces FilterBar. Shows "Issues found" (groups with errors, sorted desc)
 * and "Looking good" (groups with 0 errors, green checkmark).
 * Clicking a group drills into cards for that group.
 */

import { filterByGroup } from '../state/actions.js';
import { getGroup, getGroupMeta, getAllGroups } from '../shared/style-guide-groups.js';
import { createElement } from '../shared/dom-utils.js';

export class GroupList {
    constructor(containerEl, store) {
        this._container = containerEl;
        this._store = store;
        this._listEl = null;

        store.subscribe('errors', (errors) => this._render(errors));
        store.subscribe('activeGroup', () => this._updateActive());
        store.subscribe('analysisStatus', (status) => {
            if (status === 'idle' || status === 'analyzing') {
                this._hide();
            }
        });
    }

    _hide() {
        if (this._listEl) {
            this._listEl.remove();
            this._listEl = null;
        }
    }

    _render(errors) {
        if (this._store.get('analysisStatus') !== 'complete') return;

        // Count errors per group
        const counts = {};
        for (const groupKey of getAllGroups()) {
            counts[groupKey] = 0;
        }
        for (const error of errors) {
            const g = error.group || 'general';
            if (counts[g] !== undefined) {
                counts[g]++;
            } else {
                counts.general++;
            }
        }

        const withIssues = getAllGroups()
            .filter((g) => counts[g] > 0)
            .sort((a, b) => counts[b] - counts[a]);
        const clean = getAllGroups().filter((g) => counts[g] === 0);

        // Build list element
        const listEl = createElement('div', { className: 'cea-group-list' });

        if (withIssues.length > 0) {
            listEl.appendChild(createElement('div', {
                className: 'cea-group-section-label',
                textContent: 'Issues found',
            }));
            for (const groupKey of withIssues) {
                listEl.appendChild(this._createGroupRow(groupKey, counts[groupKey], false));
            }
        }

        if (clean.length > 0) {
            listEl.appendChild(createElement('div', {
                className: 'cea-group-section-label',
                textContent: 'Looking good',
            }));
            for (const groupKey of clean) {
                listEl.appendChild(this._createGroupRow(groupKey, 0, true));
            }
        }

        // Replace existing list
        if (this._listEl) {
            this._listEl.replaceWith(listEl);
        } else {
            this._container.appendChild(listEl);
        }
        this._listEl = listEl;

        this._updateActive();
    }

    _createGroupRow(groupKey, count, isClean) {
        const meta = getGroupMeta(groupKey);

        const btn = createElement('button', {
            className: 'cea-group-row',
            dataset: { group: groupKey },
        });

        // Dot indicator
        btn.appendChild(createElement('span', {
            className: `cea-group-row__dot cea-group-row__dot--${isClean ? 'clean' : 'issues'}`,
        }));

        // Label
        btn.appendChild(createElement('span', {
            className: 'cea-group-row__label',
            textContent: meta.label,
        }));

        // Right side: count or checkmark
        if (isClean) {
            btn.appendChild(createElement('span', {
                className: 'cea-group-row__check',
                innerHTML: '<i class="fas fa-check"></i>',
            }));
        } else {
            btn.appendChild(createElement('span', {
                className: 'cea-group-row__count',
                textContent: String(count),
            }));
            btn.addEventListener('click', () => filterByGroup(groupKey));
        }

        return btn;
    }

    _updateActive() {
        if (!this._listEl) return;
        const active = this._store.get('activeGroup');
        const rows = this._listEl.querySelectorAll('.cea-group-row');
        for (const row of rows) {
            row.classList.toggle('cea-group-row--active', row.dataset.group === active);
        }
    }
}
