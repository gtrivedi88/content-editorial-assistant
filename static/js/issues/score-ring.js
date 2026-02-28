/**
 * Score Ring — SVG donut chart for quality score.
 */

import { createElement } from '../shared/dom-utils.js';

const RADIUS = 38;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

export class ScoreRing {
    constructor(containerEl, store) {
        this._container = containerEl;
        this._store = store;
        this._render(0);

        store.subscribe('qualityScore', (score) => this._update(score));
    }

    _render(score) {
        const color = this._getColor(score);
        const offset = CIRCUMFERENCE * (1 - score / 100);

        this._container.innerHTML = `
            <div class="cea-score-section">
                <div class="cea-score-ring">
                    <svg width="88" height="88" viewBox="0 0 88 88">
                        <circle class="cea-score-ring__bg" cx="44" cy="44" r="${RADIUS}"></circle>
                        <circle class="cea-score-ring__fill" cx="44" cy="44" r="${RADIUS}"
                            stroke="${color}"
                            stroke-dasharray="${CIRCUMFERENCE}"
                            stroke-dashoffset="${offset}"></circle>
                    </svg>
                    <div class="cea-score-ring__value">${score}</div>
                </div>
                <div class="cea-score-label">Content Quality Score</div>
            </div>
        `;
    }

    _update(score) {
        const fill = this._container.querySelector('.cea-score-ring__fill');
        const value = this._container.querySelector('.cea-score-ring__value');

        if (fill && value) {
            const offset = CIRCUMFERENCE * (1 - score / 100);
            fill.style.strokeDashoffset = offset;
            fill.style.stroke = this._getColor(score);
            value.textContent = score;
        } else {
            this._render(score);
        }
    }

    _getColor(score) {
        if (score >= 90) return 'var(--cea-score-excellent)';
        if (score >= 70) return 'var(--cea-score-good)';
        if (score >= 50) return 'var(--cea-score-fair)';
        return 'var(--cea-score-poor)';
    }
}
