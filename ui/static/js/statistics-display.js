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

    // Helper to get readability score status with enhanced thresholds
    const getReadabilityStatus = (score, type = 'flesch') => {
        if (type === 'flesch') {
            if (score >= 70) return 'success';
            if (score >= 50) return 'warning';
            return 'danger';
        } else if (type === 'fog' || type === 'smog') {
            if (score <= 10) return 'success';
            if (score <= 15) return 'warning';
            return 'danger';
        } else {
            // For other metrics, use general thresholds
            if (score >= 60) return 'success';
            if (score >= 40) return 'warning';
            return 'danger';
        }
    };

    // Calculate LLM readiness score based on various factors
    const calculateLLMReadiness = () => {
        let score = 100;
        let issues = [];

        // Check word count (LLMs prefer substantial content)
        const wordCount = statistics.word_count || 0;
        if (wordCount < 50) {
            score -= 30;
            issues.push('Content too short for effective LLM processing');
        } else if (wordCount < 100) {
            score -= 15;
            issues.push('Consider adding more content for better LLM understanding');
        }

        // Check sentence structure
        const avgSentenceLength = statistics.avg_sentence_length || 0;
        if (avgSentenceLength > 30) {
            score -= 20;
            issues.push('Very long sentences may confuse LLM processing');
        } else if (avgSentenceLength < 8) {
            score -= 10;
            issues.push('Very short sentences may lack context for LLMs');
        }

        // Check readability (LLMs work better with moderately readable text)
        const fleschScore = technical_writing_metrics?.flesch_reading_ease || 0;
        if (fleschScore < 30) {
            score -= 15;
            issues.push('Very difficult text may challenge LLM comprehension');
        }

        // Check for complex words percentage
        const complexWordsPercentage = statistics.complex_words_percentage || 0;
        if (complexWordsPercentage > 40) {
            score -= 10;
            issues.push('High complex word density may reduce LLM accuracy');
        }

        return {
            score: Math.max(0, Math.min(100, score)),
            issues: issues,
            category: score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : score >= 40 ? 'Fair' : 'Needs Improvement'
        };
    };

    const passiveVoiceStatus = getStatus(statistics.passive_voice_percentage, { success: 15, warning: 25 });
    const sentenceLengthStatus = (() => {
        if (statistics.avg_sentence_length >= 15 && statistics.avg_sentence_length <= 20) return 'success';
        if (statistics.avg_sentence_length > 25 || statistics.avg_sentence_length < 10) return 'danger';
        return 'warning';
    })();
    const complexWordsStatus = getStatus(statistics.complex_words_percentage, { success: 20, warning: 30 });

    // Get readability metrics with fallbacks
    const readabilityMetrics = {
        flesch_reading_ease: technical_writing_metrics?.flesch_reading_ease || statistics?.flesch_reading_ease || 0,
        flesch_kincaid_grade: technical_writing_metrics?.flesch_kincaid_grade || statistics?.flesch_kincaid_grade || 0,
        gunning_fog_index: technical_writing_metrics?.gunning_fog_index || statistics?.gunning_fog_index || 0,
        smog_index: technical_writing_metrics?.smog_index || statistics?.smog_index || 0,
        coleman_liau_index: technical_writing_metrics?.coleman_liau_index || statistics?.coleman_liau_index || 0,
        automated_readability_index: technical_writing_metrics?.automated_readability_index || statistics?.automated_readability_index || 0
    };

    // Calculate LLM readiness
    const llmReadiness = calculateLLMReadiness();

    // Calculate engagement metrics using the new analyzer
    const engagementMetrics = window.EngagementAnalyzer ? 
        window.EngagementAnalyzer.calculateEngagementMetrics(currentContent || '', statistics) : 
        { engagement_score: 0, direct_address_percentage: 0, adverb_density: 0, engagement_category: 'Unknown', recommendations: [] };

    // Get analysis timing info
    const analysisTime = analysis.processing_time || currentAnalysis?.processing_time || currentAnalysis?.server_processing_time || 'Unknown';
    const clientTime = currentAnalysis?.client_processing_time;
    const serverTime = currentAnalysis?.server_processing_time;
    const analysisMode = analysis.analysis_mode || 'Standard';
    const spacyAvailable = analysis.spacy_available !== false;
    const rulesAvailable = analysis.modular_rules_available !== false;

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
                        <div class="pf-v5-c-card pf-m-plain pf-m-bordered grade-level-hero" style="background: linear-gradient(135deg, rgba(0, 102, 204, 0.05) 0%, rgba(0, 64, 128, 0.08) 100%);">
                            <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                                <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-center pf-m-space-items-lg">
                                    <div class="pf-v5-l-flex__item">
                                        <div class="pf-v5-c-title pf-m-4xl" style="color: ${technical_writing_metrics?.meets_target_grade ? 'var(--app-success-color)' : 'var(--app-warning-color)'};">
                                            ${technical_writing_metrics?.estimated_grade_level?.toFixed(1) || 
                                              technical_writing_metrics?.flesch_kincaid_grade?.toFixed(1) || 
                                              readabilityMetrics.flesch_kincaid_grade?.toFixed(1) || 'N/A'}
                                        </div>
                                        <div class="pf-v5-u-font-size-lg pf-v5-u-font-weight-bold pf-v5-u-color-200">Grade Level</div>
                                    </div>
                                    <div class="pf-v5-l-flex__item">
                                        <span class="pf-v5-c-label pf-m-${technical_writing_metrics?.meets_target_grade ? 'green' : 'gold'} pf-m-large">
                                            <span class="pf-v5-c-label__content">
                                                <i class="fas fa-${technical_writing_metrics?.meets_target_grade ? 'check-circle' : 'exclamation-triangle'} pf-v5-c-label__icon"></i>
                                                ${technical_writing_metrics?.grade_level_category || 'Professional'}
                                            </span>
                                        </span>
                                        <p class="pf-v5-u-font-size-sm pf-v5-u-color-200 pf-v5-u-mt-sm">
                                            ${getGradeLevelInsight(technical_writing_metrics?.estimated_grade_level || readabilityMetrics.flesch_kincaid_grade, technical_writing_metrics?.meets_target_grade)}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Readability Scores Section -->
                    <div class="pf-v5-l-stack__item">
                        <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm analytics-section-title">Readability Scores</h3>
                        <div class="pf-v5-l-grid pf-m-gutter readability-scores-grid">
                            ${generateReadabilityScoreBox('Flesch Reading Ease', readabilityMetrics.flesch_reading_ease, getReadabilityStatus(readabilityMetrics.flesch_reading_ease, 'flesch'), 'Higher is easier (60+ recommended)')}
                            ${generateReadabilityScoreBox('SMOG Index', readabilityMetrics.smog_index, getReadabilityStatus(readabilityMetrics.smog_index, 'smog'), 'Years of education needed')}
                            ${generateReadabilityScoreBox('Readability Category', 
                                technical_writing_metrics?.readability_category || getReadabilityCategory(readabilityMetrics.flesch_reading_ease), 
                                getReadabilityStatus(readabilityMetrics.flesch_reading_ease, 'flesch'), 
                                'Overall readability assessment', true)}
                            ${generateEngagementScoreBox('Engagement & Tone', engagementMetrics.engagement_score, 
                                window.EngagementAnalyzer ? window.EngagementAnalyzer.getEngagementStatus(engagementMetrics.engagement_score) : 'warning',
                                `${engagementMetrics.direct_address_percentage.toFixed(1)}% direct address, ${engagementMetrics.adverb_density.toFixed(1)}% adverbs`)}
                        </div>
                    </div>

                    <!-- Document Overview -->
                    <div class="pf-v5-l-stack__item">
                        <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm analytics-section-title">Document Overview</h3>
                        <div class="pf-v5-l-grid pf-m-gutter document-overview-grid">
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
                    <div class="pf-v5-l-stack__item writing-quality-section">
                        <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm analytics-section-title">Writing Quality</h3>
                        <div class="pf-v5-l-stack pf-m-gutter">
                            ${generateQualityProgress('Passive Voice Usage', `${(statistics.passive_voice_percentage || 0).toFixed(1)}%`, statistics.passive_voice_percentage, passiveVoiceStatus, 'Keep under 15% for active writing')}
                            ${generateQualityProgress('Average Sentence Length', `${(statistics.avg_sentence_length || 0).toFixed(1)} words`, Math.min(100, (statistics.avg_sentence_length || 0) * 4), sentenceLengthStatus, 'Aim for 15-20 words per sentence')}
                            ${generateQualityProgress('Complex Words', `${(statistics.complex_words_percentage || 0).toFixed(1)}%`, statistics.complex_words_percentage, complexWordsStatus, 'Keep under 20% for clarity')}
                        </div>
                    </div>

                    <!-- LLM Readiness Section -->
                    <div class="pf-v5-l-stack__item llm-readiness-section">
                        <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm analytics-section-title">AI & LLM Readiness</h3>
                        <div class="pf-v5-c-card pf-m-plain pf-m-bordered llm-readiness-card">
                            <div class="pf-v5-c-card__body">
                                <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-space-between">
                                    <div class="pf-v5-l-flex__item">
                                        <div class="pf-v5-l-flex pf-m-align-items-center">
                                            <div class="pf-v5-l-flex__item pf-v5-u-mr-md">
                                                <div class="llm-score-display llm-score-${llmReadiness.category.toLowerCase().replace(' ', '-')}" style="color: ${llmReadiness.score >= 80 ? 'var(--app-success-color)' : llmReadiness.score >= 60 ? 'var(--app-warning-color)' : 'var(--app-danger-color)'};">
                                                    ${llmReadiness.score.toFixed(0)}%
                                                </div>
                                            </div>
                                            <div class="pf-v5-l-flex__item">
                                                <div class="pf-v5-u-font-size-lg pf-v5-u-font-weight-bold">LLM Consumability</div>
                                                <div class="pf-v5-u-font-size-sm pf-v5-u-color-200">${llmReadiness.category}</div>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="pf-v5-l-flex__item">
                                        <span class="pf-v5-c-label pf-m-${llmReadiness.score >= 80 ? 'green' : llmReadiness.score >= 60 ? 'gold' : 'red'} capability-badge">
                                            <span class="pf-v5-c-label__content">
                                                <i class="fas fa-${llmReadiness.score >= 80 ? 'robot' : 'cog'} pf-v5-c-label__icon"></i>
                                                AI Ready
                                            </span>
                                        </span>
                                    </div>
                                </div>
                                ${llmReadiness.issues.length > 0 ? `
                                    <div class="pf-v5-u-mt-sm">
                                        <div class="pf-v5-u-font-size-sm pf-v5-u-color-200">Improvement suggestions:</div>
                                        <ul class="pf-v5-c-list pf-v5-u-font-size-sm pf-v5-u-mt-xs">
                                            ${llmReadiness.issues.map(issue => `<li class="pf-v5-c-list__item">${issue}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>

                    <!-- Analysis Performance -->
                    <div class="pf-v5-l-stack__item analysis-performance-section">
                        <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm analytics-section-title">Analysis Performance</h3>
                        <div class="pf-v5-l-stack pf-m-gutter">
                            ${generatePerformanceProgress('Server Processing Time', 
                                typeof analysisTime === 'number' ? `${analysisTime.toFixed(2)}s` : (typeof serverTime === 'number' ? `${serverTime.toFixed(2)}s` : analysisTime),
                                'success', 'Time taken for server-side analysis')}
                            ${clientTime ? generatePerformanceProgress('Total Round-trip Time', `${clientTime.toFixed(2)}s`, 'info', 'Complete processing time including network') : 
                              generatePerformanceProgress('Processing Speed', 
                                statistics.word_count ? `${Math.round((statistics.word_count || 0) / Math.max(1, analysisTime || 1))} words/sec` : 'N/A',
                                'info', 'Analysis throughput performance')}
                            ${generatePerformanceProgress('Analysis Mode', 
                                analysisMode.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
                                'warning', 'Analysis engine and capabilities used')}
                        </div>
                        <!-- System Capabilities -->
                        <div class="capabilities-container">
                            <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-center">
                                <div class="pf-v5-l-flex__item">
                                    <span class="capability-status ${spacyAvailable ? 'available' : 'unavailable'} pf-v5-c-label pf-m-${spacyAvailable ? 'green' : 'grey'}">
                                        <span class="pf-v5-c-label__content">
                                            <i class="fas fa-${spacyAvailable ? 'brain' : 'times'} pf-v5-c-label__icon"></i>
                                            SpaCy NLP
                                        </span>
                                    </span>
                                </div>
                                <div class="pf-v5-l-flex__item">
                                    <span class="capability-status ${rulesAvailable ? 'available' : 'unavailable'} pf-v5-c-label pf-m-${rulesAvailable ? 'green' : 'grey'}">
                                        <span class="pf-v5-c-label__content">
                                            <i class="fas fa-${rulesAvailable ? 'rules' : 'times'} pf-v5-c-label__icon"></i>
                                            Style Rules
                                        </span>
                                    </span>
                                </div>
                                <div class="pf-v5-l-flex__item">
                                    <span class="capability-status ${(analysis.errors?.length || 0) === 0 ? 'available' : 'unavailable'} pf-v5-c-label pf-m-${(analysis.errors?.length || 0) === 0 ? 'green' : 'gold'}">
                                        <span class="pf-v5-c-label__content">
                                            <i class="fas fa-${(analysis.errors?.length || 0) === 0 ? 'check-circle' : 'exclamation-triangle'} pf-v5-c-label__icon"></i>
                                            ${analysis.errors?.length || 0} Issues
                                        </span>
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Action Buttons -->
                    <div class="pf-v5-l-stack__item action-buttons-section">
                        <div class="pf-v5-c-card pf-m-plain">
                            <div class="pf-v5-c-card__body">
                                <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-center">

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

// Generate readability score box
function generateReadabilityScoreBox(title, value, status, description, isText = false) {
    const statusIcon = status === 'success' ? 'check-circle' : status === 'warning' ? 'exclamation-triangle' : 'times-circle';
    const statusColor = status === 'success' ? 'var(--app-success-color)' : status === 'warning' ? 'var(--app-warning-color)' : 'var(--app-danger-color)';
    const displayValue = isText ? value : (typeof value === 'number' ? value.toFixed(1) : 'N/A');

    return `
        <div class="pf-v5-l-grid__item pf-m-6-col-on-lg pf-m-12-col">
            <div class="pf-v5-c-card pf-m-plain pf-m-bordered readability-score-box readability-score-display ${status}" style="border-left: 4px solid ${statusColor};">
                <div class="pf-v5-c-card__body pf-v5-u-p-sm">
                    <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-space-between">
                        <div class="pf-v5-l-flex__item">
                            <div class="pf-v5-u-font-size-lg pf-v5-u-font-weight-bold score-value" style="color: ${statusColor};">${displayValue}</div>
                            <div class="pf-v5-u-font-size-sm pf-v5-u-font-weight-bold">${title}</div>
                            <div class="pf-v5-u-font-size-xs pf-v5-u-color-200">${description}</div>
                        </div>
                        <div class="pf-v5-l-flex__item">
                            <i class="fas fa-${statusIcon}" style="color: ${statusColor}; font-size: 1.2rem;"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Generate engagement score box (similar to readability score box)
function generateEngagementScoreBox(title, score, status, description) {
    const statusIcon = status === 'success' ? 'users' : status === 'warning' ? 'user-edit' : 'user-times';
    const statusColor = status === 'success' ? 'var(--app-success-color)' : status === 'warning' ? 'var(--app-warning-color)' : 'var(--app-danger-color)';
    const displayValue = typeof score === 'number' ? `${score}%` : 'N/A';

    return `
        <div class="pf-v5-l-grid__item pf-m-6-col-on-lg pf-m-12-col">
            <div class="pf-v5-c-card pf-m-plain pf-m-bordered readability-score-box readability-score-display ${status}" style="border-left: 4px solid ${statusColor};">
                <div class="pf-v5-c-card__body pf-v5-u-p-sm">
                    <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-space-between">
                        <div class="pf-v5-l-flex__item">
                            <div class="pf-v5-u-font-size-lg pf-v5-u-font-weight-bold score-value" style="color: ${statusColor};">${displayValue}</div>
                            <div class="pf-v5-u-font-size-sm pf-v5-u-font-weight-bold">${title}</div>
                            <div class="pf-v5-u-font-size-xs pf-v5-u-color-200">${description}</div>
                        </div>
                        <div class="pf-v5-l-flex__item">
                            <i class="fas fa-${statusIcon}" style="color: ${statusColor}; font-size: 1.2rem;"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Get readability category from Flesch score
function getReadabilityCategory(fleschScore) {
    if (fleschScore >= 90) return 'Very Easy';
    if (fleschScore >= 80) return 'Easy';
    if (fleschScore >= 70) return 'Fairly Easy';
    if (fleschScore >= 60) return 'Standard';
    if (fleschScore >= 50) return 'Fairly Difficult';
    if (fleschScore >= 30) return 'Difficult';
    return 'Very Difficult';
}

// Enhanced insight generation functions
function getGradeLevelInsight(gradeLevel, meetsTarget) {
    if (!gradeLevel) return 'Grade level could not be determined from the content.';
    if (meetsTarget) return 'Perfect readability for a professional technical audience.';
    if (gradeLevel < 9) return 'Content may be too simple for technical documentation.';
    if (gradeLevel > 16) return 'Consider simplifying complex sentences for better accessibility.';
    return 'Good readability level for most professional audiences.';
}

// Generate performance progress bar (similar to quality progress)
function generatePerformanceProgress(title, value, status, description) {
    const statusIcon = status === 'success' ? 'clock' : status === 'info' ? 'tachometer-alt' : status === 'warning' ? 'cog' : 'info-circle';
    const statusColor = status === 'success' ? 'var(--app-success-color)' : 
                       status === 'info' ? 'var(--app-primary-color)' : 
                       status === 'warning' ? 'var(--app-warning-color)' : 'var(--app-danger-color)';

    return `
        <div class="pf-v5-l-stack__item">
            <div class="pf-v5-c-card pf-m-plain pf-m-bordered performance-progress-card">
                <div class="pf-v5-c-card__body">
                    <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-space-between pf-v5-u-mb-sm">
                        <div class="pf-v5-l-flex__item">
                            <h4 class="pf-v5-c-title pf-m-md">${title}</h4>
                        </div>
                        <div class="pf-v5-l-flex__item">
                            <div class="pf-v5-l-flex pf-m-align-items-center">
                                <span class="pf-v5-u-font-weight-bold pf-v5-u-mr-sm performance-value" style="color: ${statusColor};">${value}</span>
                                <i class="fas fa-${statusIcon}" style="color: ${statusColor};"></i>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-u-font-size-sm pf-v5-u-color-200">${description}</div>
                </div>
            </div>
        </div>
    `;
}

// Export analysis function - now generates comprehensive PDF report
function exportAnalysis() {
    if (!currentAnalysis) {
        showNotification('No analysis data to export.', 'warning');
        return;
    }
    
    if (!currentContent) {
        showNotification('No content available for report generation.', 'warning');
        return;
    }
    
    showNotification('Generating comprehensive PDF report...', 'info');
    
    // Prepare data for PDF generation
    const reportData = {
        analysis: currentAnalysis,
        content: currentContent,
        structural_blocks: currentAnalysis.structural_blocks || []
    };
    
    // Call PDF generation endpoint
    fetch('/generate-pdf-report', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData)
    })
    .then(async response => {
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'PDF generation failed');
        }
        return response.blob();
    })
    .then(blob => {
        // Create download link
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        // Generate filename with timestamp
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        a.download = `writing_analytics_report_${timestamp}.pdf`;
        
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        showNotification('PDF report downloaded successfully!', 'success');
    })
    .catch(error => {
        console.error('PDF generation error:', error);
        showNotification(`PDF generation failed: ${error.message}`, 'error');
    });
}

// Generate detailed report - same as export for consistency
function generateReport() {
    exportAnalysis();
}
