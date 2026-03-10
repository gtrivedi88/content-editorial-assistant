/**
 * Score Ring — compact SVG donut chart for quality score.
 * Renders as a horizontal row: ring + label + issue count.
 */

const RADIUS = 15.5;
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
        const issueCount = this._store.get('errors')?.length || 0;

        this._container.innerHTML = `
            <div class="cea-score-row">
                <div class="cea-score-ring">
                    <svg viewBox="0 0 36 36" width="52" height="52">
                        <circle class="cea-score-ring__bg" cx="18" cy="18" r="${RADIUS}"></circle>
                        <circle class="cea-score-ring__fill" cx="18" cy="18" r="${RADIUS}"
                            stroke="${color}"
                            stroke-dasharray="${CIRCUMFERENCE}"
                            stroke-dashoffset="${offset}"></circle>
                    </svg>
                    <span class="cea-score-ring__value">${score}</span>
                </div>
                <div class="cea-score-info">
                    <div class="cea-score-label">${this._getLabel(score)}</div>
                    <div class="cea-score-sub">${issueCount} issue${issueCount === 1 ? '' : 's'} found</div>
                </div>
            </div>
        `;
    }

    _update(score) {
        const fill = this._container.querySelector('.cea-score-ring__fill');
        const value = this._container.querySelector('.cea-score-ring__value');
        const label = this._container.querySelector('.cea-score-label');
        const sub = this._container.querySelector('.cea-score-sub');

        if (fill && value) {
            const offset = CIRCUMFERENCE * (1 - score / 100);
            fill.style.strokeDashoffset = offset;
            fill.style.stroke = this._getColor(score);
            value.textContent = score;
            if (label) label.textContent = this._getLabel(score);
            if (sub) {
                const issueCount = this._store.get('errors')?.length || 0;
                sub.textContent = `${issueCount} issue${issueCount === 1 ? '' : 's'} found`;
            }
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

    _getLabel(score) {
        if (score >= 90) return 'Excellent';
        if (score >= 75) return 'Good';
        if (score >= 60) return 'Needs Work';
        return 'Poor';
    }
}
