/**
 * Report Panel — slide-over with quality score hero, LLM consumability,
 * readability metrics, document overview, compliance, and issue breakdown.
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
        this._isOpen = false;

        // PDF download button
        const pdfBtn = document.getElementById('cea-report-pdf');
        if (pdfBtn) {
            pdfBtn.addEventListener('click', () => this._downloadPdf());
        }

        // Trap 4 fix: re-render when report data updates (LLM phase completes)
        this._store.subscribe('reportData', () => {
            if (this._isOpen) this._render();
        });
    }

    open() {
        this._isOpen = true;
        this._render();
        if (this._overlay) this._overlay.classList.add('cea-visible');
        if (this._slideover) this._slideover.classList.add('cea-visible');
    }

    close() {
        this._isOpen = false;
        if (this._overlay) this._overlay.classList.remove('cea-visible');
        if (this._slideover) this._slideover.classList.remove('cea-visible');
    }

    _render() {
        if (!this._body) return;

        const state = this._store.getState();
        const {
            readability, statistics, errors, reportData,
            resolvedErrors, dismissedErrors, manuallyFixedErrors,
            qualityScore,
        } = state;

        let html = '';

        // 1. Quality Score Hero
        html += this._renderHero(qualityScore);

        // 2. LLM Consumability
        const llmData = reportData?.llm_consumability;
        if (llmData?.score != null) {
            html += this._renderLlmConsumability(llmData);
        }

        // 3. Readability Metrics
        if (readability) {
            html += renderReadability(readability);
        }

        // 4. Document Overview
        if (statistics) {
            html += renderStatistics(statistics);
        }

        // 5. Style Guide Compliance
        const compliance = reportData?.compliance;
        if (compliance && Object.keys(compliance).length > 0) {
            html += this._renderCompliance(compliance);
        }

        // 6. Issue Breakdown
        const allErrors = [...errors];
        const totalResolved = resolvedErrors.size
            + dismissedErrors.size
            + manuallyFixedErrors.size;
        const totalIssues = allErrors.length + totalResolved;

        if (totalIssues > 0) {
            html += this._renderIssueBreakdown(allErrors, totalIssues);
        }

        // 7. Resolution Summary
        if (totalResolved > 0) {
            html += this._renderResolution(
                resolvedErrors.size, dismissedErrors.size,
                manuallyFixedErrors.size, allErrors.length,
            );
        }

        this._body.innerHTML = html;
    }

    /**
     * Quality Score Hero — large arc gauge with score and label.
     */
    _renderHero(score) {
        const s = Number(score) || 0;
        const { label, color } = _getScoreMeta(s);

        // SVG half-circle arc gauge
        const radius = 70;
        const circumference = Math.PI * radius;
        const pct = Math.min(s, 100) / 100;
        const offset = circumference * (1 - pct);

        return `<div class="cea-report-hero">
            <svg class="cea-report-hero__gauge" viewBox="0 0 160 90" aria-hidden="true">
                <path d="M10,85 A70,70 0 0,1 150,85" fill="none"
                      stroke="var(--pf-v5-global--BorderColor--100)" stroke-width="10" stroke-linecap="round"/>
                <path d="M10,85 A70,70 0 0,1 150,85" fill="none"
                      stroke="${color}" stroke-width="10" stroke-linecap="round"
                      stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"/>
            </svg>
            <div class="cea-report-hero__score" style="color:${color}">${s}</div>
            <div class="cea-report-hero__label">${escapeHtml(label)}</div>
        </div>`;
    }

    /**
     * LLM Consumability — score + 3 dimension bars + strengths/improvements.
     */
    _renderLlmConsumability(data) {
        const dims = data.dimensions || {};
        const barsHtml = _renderDimensionBars([
            { label: 'Structural Clarity', score: dims.structural_clarity?.score ?? 0 },
            { label: 'Content Clarity', score: dims.content_clarity?.score ?? 0 },
            { label: 'Format Compliance', score: dims.format_compliance?.score ?? 0 },
        ]);

        let detailsHtml = '';
        if (data.strengths?.length || data.improvements?.length) {
            detailsHtml = '<details class="cea-report-detail"><summary>Details</summary>';
            if (data.strengths?.length) {
                detailsHtml += '<ul class="cea-report-llm__list cea-report-llm__list--good">';
                for (const s of data.strengths) {
                    detailsHtml += `<li>${escapeHtml(s)}</li>`;
                }
                detailsHtml += '</ul>';
            }
            if (data.improvements?.length) {
                detailsHtml += '<ul class="cea-report-llm__list cea-report-llm__list--improve">';
                for (const s of data.improvements) {
                    detailsHtml += `<li>${escapeHtml(s)}</li>`;
                }
                detailsHtml += '</ul>';
            }
            detailsHtml += '</details>';
        }

        return `<div class="cea-report-section">
            <h3 class="cea-report-section__title">LLM Consumability</h3>
            <div class="cea-report-llm">
                <div class="cea-report-llm__header">
                    <div class="cea-report-llm__score" style="color:${data.color || '#666'}">${data.score}</div>
                    <div class="cea-report-llm__label">${escapeHtml(data.label || '')}</div>
                </div>
                <div class="cea-report-llm__bars">${barsHtml}</div>
                ${detailsHtml}
            </div>
        </div>`;
    }

    /**
     * Style Guide Compliance — horizontal progress bars.
     */
    _renderCompliance(compliance) {
        const labels = {
            ibm_style: 'IBM Style Guide',
            red_hat_style: 'Red Hat Style',
            accessibility: 'Accessibility',
            modular_docs: 'Modular Docs',
        };

        let barsHtml = '';
        for (const [key, value] of Object.entries(compliance)) {
            const pct = Math.round((value ?? 0) * 100);
            const label = labels[key] || key.replaceAll('_', ' ');
            const barColor = _getComplianceColor(pct);
            barsHtml += `<div class="cea-report-compliance__row">
                <div class="cea-report-compliance__label">
                    ${escapeHtml(label)}
                    <span class="cea-report-compliance__pct">${pct}%</span>
                </div>
                <div class="cea-report-progress-bar">
                    <div class="cea-report-progress-bar__fill" style="width:${pct}%;background:${barColor}"></div>
                </div>
            </div>`;
        }

        return `<div class="cea-report-section">
            <h3 class="cea-report-section__title">Style Guide Compliance</h3>
            <div class="cea-report-compliance">${barsHtml}</div>
        </div>`;
    }

    /**
     * Issue Breakdown — category bar chart.
     */
    _renderIssueBreakdown(allErrors, totalIssues) {
        let rows = '';
        for (const groupKey of getAllGroups()) {
            const count = allErrors.filter((e) => e.group === groupKey).length;
            if (count > 0) {
                const meta = getGroupMeta(groupKey);
                const pct = Math.round((count / totalIssues) * 100);
                rows += `<div class="cea-report-compliance__row">
                    <div class="cea-report-compliance__label">
                        ${escapeHtml(meta.label)}
                        <span class="cea-report-compliance__pct">${count}</span>
                    </div>
                    <div class="cea-report-progress-bar">
                        <div class="cea-report-progress-bar__fill" style="width:${pct}%;background:var(--cea-accent-underline, #0066cc)"></div>
                    </div>
                </div>`;
            }
        }

        if (!rows) return '';

        return `<div class="cea-report-section">
            <h3 class="cea-report-section__title">Issue Breakdown</h3>
            <div class="cea-report-compliance">${rows}</div>
        </div>`;
    }

    /**
     * Resolution Summary.
     */
    _renderResolution(fixed, dismissed, manuallyFixed, remaining) {
        return `<div class="cea-report-section">
            <h3 class="cea-report-section__title">Resolution Summary</h3>
            <div class="cea-report-grid">
                <div class="cea-report-stat cea-report-stat--success">
                    <div class="cea-report-stat__value">${fixed}</div>
                    <div class="cea-report-stat__label">Accepted fixes</div>
                </div>
                <div class="cea-report-stat">
                    <div class="cea-report-stat__value">${manuallyFixed}</div>
                    <div class="cea-report-stat__label">Manually fixed</div>
                </div>
                <div class="cea-report-stat">
                    <div class="cea-report-stat__value">${dismissed}</div>
                    <div class="cea-report-stat__label">Dismissed</div>
                </div>
                <div class="cea-report-stat">
                    <div class="cea-report-stat__value">${remaining}</div>
                    <div class="cea-report-stat__label">Remaining</div>
                </div>
            </div>
        </div>`;
    }

    async _downloadPdf() {
        const sessionId = this._store.get('sessionId');
        if (!sessionId) return;
        try {
            await downloadPdfReport(sessionId);
        } catch (err) {
            console.error('[ReportPanel] PDF download failed:', err);
        }
    }
}

// ── Helpers ──────────────────────────────────────────────────────────

function _getScoreMeta(score) {
    if (score >= 90) return { label: 'Excellent \u2014 Publication-ready content', color: '#1A8F57' };
    if (score >= 75) return { label: 'Good \u2014 Minor improvements possible', color: '#2E9E59' };
    if (score >= 60) return { label: 'Needs Work \u2014 Review recommended', color: '#F2BA4D' };
    return { label: 'Requires Revision', color: '#c9190b' };
}

function _getComplianceColor(pct) {
    if (pct >= 80) return 'var(--pf-v5-global--success-color--100)';
    if (pct >= 60) return 'var(--pf-v5-global--warning-color--100)';
    return 'var(--cea-color-issues, #c9190b)';
}

function _getBarColor(score) {
    if (score >= 75) return 'var(--pf-v5-global--success-color--100)';
    if (score >= 50) return 'var(--pf-v5-global--warning-color--100)';
    return 'var(--cea-color-issues, #c9190b)';
}

function _renderDimensionBars(dimensions) {
    let html = '';
    for (const dim of dimensions) {
        const color = _getBarColor(dim.score);
        html += `<div class="cea-report-compliance__row">
            <div class="cea-report-compliance__label">
                ${escapeHtml(dim.label)}
                <span class="cea-report-compliance__pct">${dim.score}</span>
            </div>
            <div class="cea-report-progress-bar">
                <div class="cea-report-progress-bar__fill" style="width:${dim.score}%;background:${color}"></div>
            </div>
        </div>`;
    }
    return html;
}
