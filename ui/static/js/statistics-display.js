/**
 * Statistics Display Module - Enhanced PatternFly Version
 * Contains comprehensive statistics card generation using PatternFly components.
 */

// Generate statistics card using PatternFly Card, Grid, and Progress components
function generateStatisticsCard(analysis) {
    const { statistics, technical_writing_metrics } = analysis;

    // Helper to determine status for progress bars and colors
    const getStatus = (value, thresholds) => {
        if (value <= thresholds.success) return 'success';
        if (value <= thresholds.warning) return 'warning';
        return 'danger';
    };

    const passiveVoiceStatus = getStatus(statistics.passive_voice_percentage, { success: 15, warning: 25 });
    const sentenceLengthStatus = (() => {
        if (statistics.avg_sentence_length >= 15 && statistics.avg_sentence_length <= 20) return 'success';
        if (statistics.avg_sentence_length > 25 || statistics.avg_sentence_length < 10) return 'danger';
        return 'warning';
    })();
    const complexWordsStatus = getStatus(statistics.complex_words_percentage, { success: 20, warning: 30 });

    return `
        <div class="pf-v5-c-card app-card" id="statistics-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h2 class="pf-v5-c-title pf-m-xl">
                        <i class="fas fa-chart-line pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                        Writing Analytics
                    </h2>
                </div>
                <div class="pf-v5-c-card__actions">
                    <div class="pf-v5-c-dropdown">
                        <button class="pf-v5-c-dropdown__toggle pf-m-plain" type="button" aria-expanded="false" onclick="exportAnalysis()">
                            <i class="fas fa-download" aria-hidden="true"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-l-stack pf-m-gutter">
                    <!-- Grade Level Hero Section -->
                    <div class="pf-v5-l-stack__item">
                        <div class="pf-v5-c-card pf-m-plain pf-m-bordered" style="background: linear-gradient(135deg, rgba(0, 102, 204, 0.05) 0%, rgba(0, 64, 128, 0.08) 100%);">
                            <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                                <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-center pf-m-space-items-lg">
                                    <div class="pf-v5-l-flex__item">
                                        <div class="pf-v5-c-title pf-m-4xl" style="color: ${technical_writing_metrics?.meets_target_grade ? 'var(--app-success-color)' : 'var(--app-warning-color)'};">
                                            ${technical_writing_metrics?.estimated_grade_level?.toFixed(1) || 'N/A'}
                                        </div>
                                        <div class="pf-v5-u-font-size-lg pf-v5-u-font-weight-bold pf-v5-u-color-200">Grade Level</div>
                                    </div>
                                    <div class="pf-v5-l-flex__item">
                                        <span class="pf-v5-c-label pf-m-${technical_writing_metrics?.meets_target_grade ? 'green' : 'gold'} pf-m-large">
                                            <span class="pf-v5-c-label__content">
                                                <i class="fas fa-${technical_writing_metrics?.meets_target_grade ? 'check-circle' : 'exclamation-triangle'} pf-v5-c-label__icon"></i>
                                                ${technical_writing_metrics?.grade_level_category || 'Unknown'}
                                            </span>
                                        </span>
                                        <p class="pf-v5-u-font-size-sm pf-v5-u-color-200 pf-v5-u-mt-sm">
                                            ${getGradeLevelInsight(technical_writing_metrics?.estimated_grade_level, technical_writing_metrics?.meets_target_grade)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Document Overview -->
                    <div class="pf-v5-l-stack__item">
                        <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">Document Overview</h3>
                        <div class="pf-v5-l-grid pf-m-gutter">
                            <div class="pf-v5-l-grid__item pf-m-3-col">
                                <div class="pf-v5-c-card pf-m-plain pf-m-bordered pf-v5-u-text-align-center app-card">
                                    <div class="pf-v5-c-card__body">
                                        <div class="pf-v5-c-title pf-m-2xl" style="color: var(--app-primary-color);">${statistics.word_count || 0}</div>
                                        <div class="pf-v5-u-font-size-sm pf-v5-u-color-200">Words</div>
                                    </div>
                                </div>
                            </div>
                            <div class="pf-v5-l-grid__item pf-m-3-col">
                                <div class="pf-v5-c-card pf-m-plain pf-m-bordered pf-v5-u-text-align-center app-card">
                                    <div class="pf-v5-c-card__body">
                                        <div class="pf-v5-c-title pf-m-2xl" style="color: var(--app-success-color);">${statistics.sentence_count || 0}</div>
                                        <div class="pf-v5-u-font-size-sm pf-v5-u-color-200">Sentences</div>
                                    </div>
                                </div>
                            </div>
                            <div class="pf-v5-l-grid__item pf-m-3-col">
                                <div class="pf-v5-c-card pf-m-plain pf-m-bordered pf-v5-u-text-align-center app-card">
                                    <div class="pf-v5-c-card__body">
                                        <div class="pf-v5-c-title pf-m-2xl" style="color: var(--app-warning-color);">${statistics.paragraph_count || 0}</div>
                                        <div class="pf-v5-u-font-size-sm pf-v5-u-color-200">Paragraphs</div>
                                    </div>
                                </div>
                            </div>
                            <div class="pf-v5-l-grid__item pf-m-3-col">
                                <div class="pf-v5-c-card pf-m-plain pf-m-bordered pf-v5-u-text-align-center app-card">
                                    <div class="pf-v5-c-card__body">
                                        <div class="pf-v5-c-title pf-m-2xl" style="color: var(--app-danger-color);">${Math.ceil((statistics.word_count || 0) / 250)}</div>
                                        <div class="pf-v5-u-font-size-sm pf-v5-u-color-200">Pages</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Writing Quality Metrics -->
                    <div class="pf-v5-l-stack__item">
                        <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">Writing Quality</h3>
                        <div class="pf-v5-l-stack pf-m-gutter">
                            ${generateQualityProgress('Passive Voice Usage', `${(statistics.passive_voice_percentage || 0).toFixed(1)}%`, statistics.passive_voice_percentage, passiveVoiceStatus, 'Keep under 15% for active writing')}
                            ${generateQualityProgress('Average Sentence Length', `${(statistics.avg_sentence_length || 0).toFixed(1)} words`, Math.min(100, (statistics.avg_sentence_length || 0) * 4), sentenceLengthStatus, 'Aim for 15-20 words per sentence')}
                            ${generateQualityProgress('Complex Words', `${(statistics.complex_words_percentage || 0).toFixed(1)}%`, statistics.complex_words_percentage, complexWordsStatus, 'Keep under 20% for clarity')}
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="pf-v5-l-stack__item">
                        <div class="pf-v5-c-card pf-m-plain">
                            <div class="pf-v5-c-card__body">
                                <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-center">
                                    <div class="pf-v5-l-flex__item">
                                        <button class="pf-v5-c-button pf-m-primary" type="button" onclick="rewriteContent()">
                                            <i class="fas fa-magic pf-v5-u-mr-sm"></i>
                                            AI Rewrite
                                        </button>
                                    </div>
                                    <div class="pf-v5-l-flex__item">
                                        <button class="pf-v5-c-button pf-m-secondary" type="button" onclick="generateReport()">
                                            <i class="fas fa-file-alt pf-v5-u-mr-sm"></i>
                                            Generate Report
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Enhanced PatternFly Progress component for quality metrics
function generateQualityProgress(title, label, value, status, description) {
    const progressValue = Math.min(100, Math.max(0, value || 0));
    const statusIcon = status === 'success' ? 'check-circle' : status === 'warning' ? 'exclamation-triangle' : 'times-circle';
    const statusColor = status === 'success' ? 'var(--app-success-color)' : status === 'warning' ? 'var(--app-warning-color)' : 'var(--app-danger-color)';

    return `
        <div class="pf-v5-l-stack__item">
            <div class="pf-v5-c-card pf-m-plain pf-m-bordered">
                <div class="pf-v5-c-card__body">
                    <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-space-between pf-v5-u-mb-sm">
                        <div class="pf-v5-l-flex__item">
                            <h4 class="pf-v5-c-title pf-m-md">${title}</h4>
                        </div>
                        <div class="pf-v5-l-flex__item">
                            <div class="pf-v5-l-flex pf-m-align-items-center">
                                <span class="pf-v5-u-font-weight-bold pf-v5-u-mr-sm">${label}</span>
                                <i class="fas fa-${statusIcon}" style="color: ${statusColor};"></i>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-c-progress pf-m-sm progress-custom">
                        <div class="pf-v5-c-progress__bar">
                            <div class="pf-v5-c-progress__indicator" style="width: ${progressValue}%; background-color: ${statusColor};" role="progressbar" aria-valuenow="${progressValue}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                    </div>
                    <div class="pf-v5-u-font-size-sm pf-v5-u-color-200 pf-v5-u-mt-xs">${description}</div>
                </div>
            </div>
        </div>
    `;
}

// Enhanced insight generation functions
function getGradeLevelInsight(gradeLevel, meetsTarget) {
    if (!gradeLevel) return 'Grade level could not be determined from the content.';
    if (meetsTarget) return 'Perfect readability for a professional technical audience.';
    if (gradeLevel < 9) return 'Content may be too simple for technical documentation.';
    if (gradeLevel > 16) return 'Consider simplifying complex sentences for better accessibility.';
    return 'Good readability level for most professional audiences.';
}

// Export analysis function
function exportAnalysis() {
    if (!currentAnalysis) {
        showNotification('No analysis data to export.', 'warning');
        return;
    }
    
    // Create downloadable analysis report
    const reportData = {
        timestamp: new Date().toISOString(),
        statistics: currentAnalysis.statistics,
        technical_writing_metrics: currentAnalysis.technical_writing_metrics,
        errors: currentAnalysis.errors,
        content_preview: currentContent ? currentContent.substring(0, 200) + '...' : ''
    };
    
    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `writing-analysis-${new Date().getTime()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Analysis exported successfully!', 'success');
}

// Generate detailed report
function generateReport() {
    if (!currentAnalysis) {
        showNotification('No analysis data available for report generation.', 'warning');
        return;
    }
    
    showNotification('Generating detailed report...', 'info');
    
    // This would typically call a backend endpoint to generate a formatted report
    // For now, we'll show a placeholder
    setTimeout(() => {
        showNotification('Report generation feature coming soon!', 'info');
    }, 1500);
}
