/**
 * Statistics Display — document overview metrics.
 */

export function renderStatistics(statistics) {
    if (!statistics) return '';

    const wordCount = statistics.word_count ?? 0;
    const sentenceCount = statistics.sentence_count ?? 0;
    const avgSentenceLen = statistics.avg_sentence_length ?? 0;
    const uniqueWords = statistics.unique_words ?? 0;

    return `<div class="cea-report-section">
        <h3 class="cea-report-section__title">Document Overview</h3>
        <div class="cea-report-grid">
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${wordCount}</div>
                <div class="cea-report-stat__label">Words</div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${sentenceCount}</div>
                <div class="cea-report-stat__label">Sentences</div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${Number(avgSentenceLen).toFixed(1)}</div>
                <div class="cea-report-stat__label">Avg. words per sentence</div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${uniqueWords}</div>
                <div class="cea-report-stat__label">Unique words</div>
            </div>
        </div>
    </div>`;
}
