/**
 * Report Panel — slide-over with readability scores, statistics, PDF download.
 */

import { store } from '../state/store.js';
import { downloadPdfReport } from '../services/api-client.js';
import { renderReadability } from './readability-display.js';
import { renderStatistics } from './statistics-display.js';
import { getGroupMeta, getAllGroups } from '../shared/style-guide-groups.js';
import { escapeHtml } from '../shared/dom-utils.js';

export class ReportPanel {
    constructor(slideoverEl, storeRef) {
        this._slideover = slideoverEl;
        this._overlay = document.getElementById('cea-report-overlay');
        this._body = document.getElementById('cea-report-body');
        this._store = storeRef;

        // PDF download button
        const pdfBtn = document.getElementById('cea-report-pdf');
        if (pdfBtn) {
            pdfBtn.addEventListener('click', () => this._downloadPdf());
        }
    }

    open() {
        this._render();
        if (this._overlay) this._overlay.classList.add('cea-visible');
        if (this._slideover) this._slideover.classList.add('cea-visible');
    }

    close() {
        if (this._overlay) this._overlay.classList.remove('cea-visible');
        if (this._slideover) this._slideover.classList.remove('cea-visible');
    }

    _render() {
        if (!this._body) return;

        const state = this._store.getState();
        const { readability, statistics, errors, resolvedErrors, dismissedErrors } = state;

        let html = '';

        // Document overview
        if (statistics) {
            html += renderStatistics(statistics);
        }

        // Readability
        if (readability) {
            html += renderReadability(readability);
        }

        // Issue breakdown
        const allErrors = [...errors];
        const totalIssues = allErrors.length + resolvedErrors.size + dismissedErrors.size;

        if (totalIssues > 0) {
            html += `<div class="cea-report-section">
                <h3 class="cea-report-section__title">Issue Breakdown</h3>
                <table class="cea-report-breakdown">`;

            // Count by group across all errors (including resolved)
            for (const groupKey of getAllGroups()) {
                const count = allErrors.filter((e) => e.group === groupKey).length;
                if (count > 0) {
                    const meta = getGroupMeta(groupKey);
                    const barWidth = Math.max(8, (count / totalIssues) * 120);
                    html += `<tr>
                        <td><span class="cea-report-breakdown__bar" style="width:${barWidth}px; background:var(--cea-accent-underline, #0066cc)"></span>${escapeHtml(meta.label)}</td>
                        <td>${count} issue${count !== 1 ? 's' : ''}</td>
                    </tr>`;
                }
            }

            html += `</table></div>`;
        }

        // Resolution summary
        if (resolvedErrors.size > 0 || dismissedErrors.size > 0) {
            html += `<div class="cea-report-section">
                <h3 class="cea-report-section__title">Resolution Summary</h3>
                <div class="cea-report-grid">
                    <div class="cea-report-stat cea-report-stat--success">
                        <div class="cea-report-stat__value">${resolvedErrors.size}</div>
                        <div class="cea-report-stat__label">Issues fixed</div>
                    </div>
                    <div class="cea-report-stat">
                        <div class="cea-report-stat__value">${dismissedErrors.size}</div>
                        <div class="cea-report-stat__label">Issues dismissed</div>
                    </div>
                    <div class="cea-report-stat">
                        <div class="cea-report-stat__value">${allErrors.length}</div>
                        <div class="cea-report-stat__label">Issues remaining</div>
                    </div>
                </div>
            </div>`;
        }

        this._body.innerHTML = html;
    }

    async _downloadPdf() {
        const state = this._store.getState();
        try {
            await downloadPdfReport(
                state.analysisResult?.analysis,
                state.content,
                state.structuralBlocks
            );
        } catch (err) {
            console.error('[ReportPanel] PDF download failed:', err);
        }
    }
}
