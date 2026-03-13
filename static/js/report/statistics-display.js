/**
 * Statistics Display — document overview metrics with contextual labels.
 */

/**
 * Get a contextual label for vocabulary diversity.
 */
function getDiversityLabel(diversity) {
    if (diversity >= 0.8) return 'Excellent variety';
    if (diversity >= 0.6) return 'Good variety';
    if (diversity >= 0.4) return 'Moderate';
    return 'Limited variety';
}

/**
 * Get a contextual label for average sentence length.
 */
function getSentenceLengthLabel(avg) {
    if (avg <= 10) return 'Very concise';
    if (avg <= 15) return 'Concise';
    if (avg <= 20) return 'Ideal';
    if (avg <= 25) return 'Lengthy';
    return 'Very long';
}

/**
 * Render document overview statistics as HTML string.
 */
export function renderStatistics(statistics) {
    if (!statistics) return '';

    const wordCount = statistics.word_count ?? 0;
    const sentenceCount = statistics.sentence_count ?? 0;
    const paragraphCount = statistics.paragraph_count ?? 0;
    const avgSentenceLen = statistics.avg_sentence_length ?? 0;
    const diversity = statistics.vocabulary_diversity ?? 0;
    const readingTime = statistics.estimated_reading_time || '';

    const diversityPct = Math.round(diversity * 100);
    const diversityLabel = getDiversityLabel(diversity);
    const sentLabel = getSentenceLengthLabel(avgSentenceLen);

    return `<div class="cea-report-section">
        <h3 class="cea-report-section__title">Document Overview</h3>
        <div class="cea-report-grid cea-report-grid--3col">
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${wordCount.toLocaleString()}</div>
                <div class="cea-report-stat__label">Words</div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${sentenceCount}</div>
                <div class="cea-report-stat__label">Sentences</div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${paragraphCount}</div>
                <div class="cea-report-stat__label">Paragraphs</div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${readingTime || '\u2014'}</div>
                <div class="cea-report-stat__label">Reading time</div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${Number(avgSentenceLen).toFixed(1)}</div>
                <div class="cea-report-stat__label">Avg. words/sentence<br><small>${sentLabel}</small></div>
            </div>
            <div class="cea-report-stat">
                <div class="cea-report-stat__value">${diversityPct}%</div>
                <div class="cea-report-stat__label">Vocabulary diversity<br><small>${diversityLabel}</small></div>
            </div>
        </div>
    </div>`;
}
