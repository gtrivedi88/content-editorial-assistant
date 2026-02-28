/**
 * Readability Display — renders readability score cards.
 */

import { escapeHtml } from '../shared/dom-utils.js';

/**
 * Render readability scores section as HTML string.
 */
export function renderReadability(readability) {
    if (!readability) return '';

    const flesch = readability.flesch_reading_ease ?? readability.flesch ?? null;
    const grade = readability.flesch_kincaid_grade ?? readability.grade_level ?? null;
    const smog = readability.smog_index ?? readability.smog ?? null;
    const fog = readability.gunning_fog ?? null;

    let html = `<div class="cea-report-section">
        <h3 class="cea-report-section__title">Readability Scores</h3>
        <div class="cea-report-grid">`;

    if (flesch !== null) {
        const variant = flesch >= 60 ? 'cea-report-stat--success' : flesch >= 30 ? 'cea-report-stat--warning' : 'cea-report-stat--danger';
        html += `<div class="cea-report-stat ${variant}">
            <div class="cea-report-stat__value">${Number(flesch).toFixed(1)}</div>
            <div class="cea-report-stat__label">Flesch Reading Ease<br><small>Higher is easier (60+ recommended)</small></div>
        </div>`;
    }

    if (grade !== null) {
        const variant = grade <= 10 ? 'cea-report-stat--success' : grade <= 14 ? 'cea-report-stat--warning' : 'cea-report-stat--danger';
        html += `<div class="cea-report-stat ${variant}">
            <div class="cea-report-stat__value">${Number(grade).toFixed(1)}</div>
            <div class="cea-report-stat__label">Grade Level<br><small>${getGradeLabel(grade)}</small></div>
        </div>`;
    }

    if (smog !== null) {
        const variant = smog <= 10 ? 'cea-report-stat--success' : smog <= 14 ? 'cea-report-stat--warning' : 'cea-report-stat--danger';
        html += `<div class="cea-report-stat ${variant}">
            <div class="cea-report-stat__value">${Number(smog).toFixed(1)}</div>
            <div class="cea-report-stat__label">SMOG Index<br><small>Years of education needed</small></div>
        </div>`;
    }

    if (fog !== null) {
        const variant = fog <= 10 ? 'cea-report-stat--success' : fog <= 14 ? 'cea-report-stat--warning' : 'cea-report-stat--danger';
        html += `<div class="cea-report-stat ${variant}">
            <div class="cea-report-stat__value">${Number(fog).toFixed(1)}</div>
            <div class="cea-report-stat__label">Gunning Fog Index<br><small>Ideal: 7\u20138 for technical docs</small></div>
        </div>`;
    }

    html += `</div></div>`;
    return html;
}

function getGradeLabel(grade) {
    if (grade <= 6) return 'Elementary';
    if (grade <= 8) return 'Middle School';
    if (grade <= 12) return 'High School';
    if (grade <= 16) return 'College Level';
    return 'Graduate Level';
}
