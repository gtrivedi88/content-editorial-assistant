/**
 * Readability Display — renders readability metric cards with gauges and context.
 * Handles the backend format: { "Flesch Reading Ease": { score, help_text }, ... }
 */

import { escapeHtml } from '../shared/dom-utils.js';

/**
 * Determine status tier for a higher-is-better metric.
 */
function statusHigherBetter(value, good, warn) {
    if (value >= good) return 'success';
    if (value >= warn) return 'warning';
    return 'danger';
}

/**
 * Determine status tier for a lower-is-better metric.
 */
function statusLowerBetter(value, good, warn) {
    if (value <= good) return 'success';
    if (value <= warn) return 'warning';
    return 'danger';
}

/**
 * Metric configuration — defines how each readability metric is displayed.
 */
const METRIC_CONFIG = {
    'Flesch Reading Ease': {
        label: 'Flesch Reading Ease',
        ideal: '60\u201370',
        max: 100,
        invert: false, // higher is better
        getStatus: (v) => statusHigherBetter(v, 60, 30),
        why: 'The gold standard for readability. Scores 60\u201370 mean your content is accessible to most technical professionals without being oversimplified.',
    },
    'Flesch-Kincaid Grade': {
        label: 'Flesch-Kincaid Grade',
        ideal: '8\u201312',
        max: 20,
        invert: true, // lower is better
        getStatus: (v) => statusLowerBetter(v, 12, 14),
        why: 'Maps to US school grade level. Grade 8\u201312 ensures your technical docs are clear to professionals without requiring advanced academic training.',
    },
    'Gunning Fog': {
        label: 'Gunning Fog Index',
        ideal: '8\u201312',
        max: 20,
        invert: true,
        getStatus: (v) => statusLowerBetter(v, 12, 14),
        why: 'Designed for business and technical writing. Penalizes complex words \u2014 keep below 12 for docs that engineers actually read.',
    },
    'Coleman-Liau': {
        label: 'Coleman-Liau Index',
        ideal: '10\u201314',
        max: 20,
        invert: true,
        getStatus: (v) => statusLowerBetter(v, 14, 16),
        why: 'Character-based formula \u2014 especially reliable for technical vocabulary where syllable counting can be misleading.',
    },
};

/**
 * Build a small SVG arc gauge for a metric score.
 */
function buildGauge(value, max, invert, status) {
    const clamped = Math.max(0, Math.min(value, max));
    const pct = invert ? (1 - clamped / max) : (clamped / max);
    const radius = 28;
    const circumference = Math.PI * radius; // half circle
    const offset = circumference * (1 - pct);

    const colorMap = {
        success: 'var(--pf-v5-global--success-color--100)',
        warning: 'var(--pf-v5-global--warning-color--100)',
        danger: 'var(--cea-color-issues, #c9190b)',
    };
    const color = colorMap[status] || colorMap.warning;

    return `<svg class="cea-report-gauge" viewBox="0 0 64 36" width="64" height="36">
        <path d="M4,34 A28,28 0 0,1 60,34" fill="none"
              stroke="var(--pf-v5-global--BorderColor--100)" stroke-width="5" stroke-linecap="round"/>
        <path d="M4,34 A28,28 0 0,1 60,34" fill="none"
              stroke="${color}" stroke-width="5" stroke-linecap="round"
              stroke-dasharray="${circumference}" stroke-dashoffset="${offset}"/>
    </svg>`;
}

/**
 * Render readability scores section as HTML string.
 * Accepts the new backend format: { metricName: { score, help_text } }
 */
export function renderReadability(readability) {
    if (!readability || typeof readability !== 'object') return '';

    const entries = Object.entries(readability);
    if (entries.length === 0) return '';

    let cards = '';
    for (const [name, data] of entries) {
        const config = METRIC_CONFIG[name];
        if (!config) continue;

        const score = Number(data.score ?? 0);
        const helpText = data.help_text || config.why;
        const status = config.getStatus(score);
        const gauge = buildGauge(score, config.max, config.invert, status);

        cards += `<div class="cea-report-metric-card cea-report-metric-card--${status}">
            <div class="cea-report-metric-card__header">
                ${gauge}
                <div class="cea-report-metric-card__score">${score.toFixed(1)}</div>
            </div>
            <div class="cea-report-metric-card__label">${escapeHtml(config.label)}</div>
            <div class="cea-report-metric-card__ideal">Ideal: ${config.ideal}</div>
            <details class="cea-report-detail">
                <summary>Why it matters</summary>
                <p>${escapeHtml(helpText)}</p>
            </details>
        </div>`;
    }

    if (!cards) return '';

    return `<div class="cea-report-section">
        <h3 class="cea-report-section__title">Readability Metrics</h3>
        <div class="cea-report-grid">${cards}</div>
    </div>`;
}
