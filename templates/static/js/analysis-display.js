// Analysis display functions

// Display structural blocks (ideal UI)
function displayStructuralBlocks(blocks) {
    return `
        <div class="mb-3">
            <h6>Document Structure:</h6>
            <div class="structural-blocks">
                ${blocks.map(block => createStructuralBlock(block)).join('')}
            </div>
        </div>
    `;
}

// Display flat content (fallback)
function displayFlatContent(content, errors) {
    return `
        <div class="mb-3">
            <h6>Original Content:</h6>
            <div class="border rounded p-3 bg-light">
                ${highlightErrors(content, errors)}
            </div>
        </div>
        
        ${errors.length > 0 ? `
        <div class="mb-3">
            <h6>Detected Issues (${errors.length}):</h6>
            <div class="analysis-container">
                ${errors.map(error => createErrorCard(error)).join('')}
            </div>
        </div>
        ` : '<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>No issues detected!</div>'}
    `;
}

// Create a structural block display
function createStructuralBlock(block) {
    const blockTypeColors = {
        'heading': 'primary',
        'paragraph': 'secondary',
        'list': 'info',
        'admonition': 'warning',
        'code': 'dark',
        'literal': 'dark',
        'listing': 'dark',
        'quote': 'success',
        'sidebar': 'info',
        'attribute_entry': 'light'
    };
    
    const blockTypeIcons = {
        'heading': 'fas fa-heading',
        'paragraph': 'fas fa-paragraph',
        'list': 'fas fa-list',
        'admonition': 'fas fa-exclamation-triangle',
        'code': 'fas fa-code',
        'literal': 'fas fa-terminal',
        'listing': 'fas fa-code',
        'quote': 'fas fa-quote-left',
        'sidebar': 'fas fa-window-maximize',
        'attribute_entry': 'fas fa-cog'
    };
    
    const color = blockTypeColors[block.block_type] || 'secondary';
    const icon = blockTypeIcons[block.block_type] || 'fas fa-file-alt';
    
    const blockTitle = block.block_type.toUpperCase() + 
        (block.level > 0 ? ` (Level ${block.level})` : '') +
        (block.admonition_type ? ` - ${block.admonition_type.toUpperCase()}` : '');
    
    return `
        <div class="structural-block mb-3 border rounded">
            <div class="block-header bg-${color} text-white p-2 d-flex justify-content-between align-items-center">
                <div>
                    <i class="${icon} me-2"></i>
                    <strong>BLOCK ${block.block_id + 1}: ${blockTitle}</strong>
                </div>
                <small class="opacity-75">
                    ${block.should_skip_analysis ? 'Analysis skipped' : (block.errors ? block.errors.length : 0) + ' issues'}
                </small>
            </div>
            
            <div class="block-content p-3">
                ${block.should_skip_analysis ? 
                    `<div class="text-muted fst-italic">
                        <i class="fas fa-info-circle me-2"></i>Analysis skipped for this block type.
                    </div>` : 
                    `<div class="block-text bg-light p-3 rounded mb-3" style="white-space: pre-wrap; font-family: monospace;">
                        ${escapeHtml(block.content)}
                    </div>`
                }
                
                ${!block.should_skip_analysis && block.errors && block.errors.length > 0 ? `
                <div class="block-errors">
                    <h6 class="text-danger">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        ${block.errors.length} Issue${block.errors.length > 1 ? 's' : ''} Found:
                    </h6>
                    <div class="error-list">
                        ${block.errors.map(error => createInlineError(error)).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${!block.should_skip_analysis && (!block.errors || block.errors.length === 0) ? `
                <div class="alert alert-success alert-sm mb-0">
                    <i class="fas fa-check-circle me-2"></i>No issues found in this block.
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create inline error display for structural blocks
function createInlineError(error) {
    return `
        <div class="error-item mb-2 p-2 border-start border-danger border-3 bg-light">
            <div class="d-flex align-items-start">
                <div class="me-3">
                    <span class="badge bg-danger">${error.error_type || 'STYLE'}</span>
                </div>
                <div class="flex-grow-1">
                    <div class="error-message">
                        <strong>${error.message || 'Style issue detected'}</strong>
                    </div>
                    ${error.suggestion ? `
                    <div class="error-suggestion mt-1 text-muted">
                        <i class="fas fa-lightbulb me-1"></i>
                        Suggestion: ${error.suggestion}
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// Display analysis results
function displayAnalysisResults(analysis, content, structuralBlocks = null) {
    const resultsContainer = document.getElementById('analysis-results');
    if (!resultsContainer) return;
    
    let html = `
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0"><i class="fas fa-file-alt me-2"></i>Content Analysis</h5>
                        <span class="badge ${analysis.overall_score >= 80 ? 'bg-success' : analysis.overall_score >= 60 ? 'bg-warning' : 'bg-danger'}">
                            Score: ${analysis.overall_score.toFixed(1)}%
                        </span>
                    </div>
                    <div class="card-body">
                        ${structuralBlocks ? displayStructuralBlocks(structuralBlocks) : displayFlatContent(content, analysis.errors)}
                        
                        ${analysis.errors.length > 0 ? `
                        <div class="text-center mt-4">
                            <button class="btn btn-primary btn-lg" onclick="rewriteContent()">
                                <i class="fas fa-magic me-2"></i>Rewrite with AI
                            </button>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                ${generateStatisticsCard(analysis)}
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
}

// Generate statistics card (full implementation)
function generateStatisticsCard(analysis) {
    return `
        <!-- Ultra-Modern Technical Writing Statistics Card -->
        <div class="card border-0 shadow-lg" style="border-radius: 24px; overflow: hidden; background: white;">
            <!-- Modern gradient header -->
            <div class="card-header border-0 pb-2" style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%); color: white; border-radius: 0;">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0 fw-bold">
                        <i class="fas fa-chart-line me-2"></i>Writing Analytics
                    </h5>
                    <button class="btn btn-sm btn-light btn-outline-light rounded-pill opacity-90" data-bs-toggle="modal" data-bs-target="#metricsHelpModal" style="border: 1px solid rgba(255,255,255,0.3);">
                        <i class="fas fa-question-circle"></i>
                    </button>
                </div>
            </div>
            <div class="card-body pt-3" style="color: #2d3748; background: white;">
                
                <!-- Grade Level Assessment - Hero Section -->
                <div class="text-center mb-4 p-4 rounded-4" style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 2px solid #e2e8f0;">
                    <div class="d-flex justify-content-center align-items-center mb-3">
                        <div class="me-4">
                            <h1 class="mb-1 fw-bold" style="color: ${analysis.technical_writing_metrics?.meets_target_grade ? '#059669' : '#d97706'}; font-size: 2.5rem;">
                                ${analysis.technical_writing_metrics?.estimated_grade_level?.toFixed(1) || 'N/A'}
                            </h1>
                            <small class="text-muted fw-medium">Grade Level</small>
                        </div>
                        <div class="text-start">
                            <div class="badge fs-6 mb-2" style="background: ${analysis.technical_writing_metrics?.meets_target_grade ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #f59e0b, #d97706)'}; color: white; padding: 8px 16px;">
                                ${analysis.technical_writing_metrics?.grade_level_category || 'Unknown'}
                            </div>
                            <div class="small d-flex align-items-center">
                                ${analysis.technical_writing_metrics?.meets_target_grade ? 
                                    '<i class="fas fa-check-circle me-2" style="color: #059669;"></i><span style="color: #059669;">Perfect for technical docs</span>' : 
                                    '<i class="fas fa-exclamation-triangle me-2" style="color: #d97706;"></i><span style="color: #d97706;">Outside target (9-11th grade)</span>'
                                }
                            </div>
                        </div>
                    </div>
                    <div class="small text-muted p-3 rounded-3" style="background: white; border: 1px solid #e2e8f0;">
                        ${getGradeLevelInsight(analysis.technical_writing_metrics?.estimated_grade_level, analysis.technical_writing_metrics?.meets_target_grade)}
                    </div>
                </div>

                <!-- Document Overview - Clean Modern Cards -->
                <div class="row g-3 mb-4">
                    <div class="col-4">
                        <div class="text-center p-3 rounded-3" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);">
                            <h3 class="mb-1 fw-bold">${analysis.statistics.word_count || 0}</h3>
                            <small class="fw-medium">Words</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center p-3 rounded-3" style="background: linear-gradient(135deg, #06b6d4, #0891b2); color: white; box-shadow: 0 4px 12px rgba(6, 182, 212, 0.25);">
                            <h3 class="mb-1 fw-bold">${analysis.statistics.sentence_count || 0}</h3>
                            <small class="fw-medium">Sentences</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center p-3 rounded-3" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.25);">
                            <h3 class="mb-1 fw-bold">${Math.ceil((analysis.statistics.word_count || 0) / 250)}</h3>
                            <small class="fw-medium">Pages</small>
                        </div>
                    </div>
                </div>

                <!-- Readability Scores - Light Modern Cards -->
                <div class="mb-4">
                    <h6 class="text-center mb-3 fw-semibold d-flex align-items-center justify-content-center" style="color: #374151;">
                        <i class="fas fa-tachometer-alt me-2" style="color: #6366f1;"></i>Readability Metrics
                    </h6>
                    <div class="row g-2">
                        ${generateModernReadabilityCard('Flesch Score', analysis.statistics.flesch_reading_ease, 'Higher = easier to read', 'fas fa-book-open', getFleschColor(analysis.statistics.flesch_reading_ease))}
                        ${generateModernReadabilityCard('Fog Index', analysis.statistics.gunning_fog_index, 'Education years needed', 'fas fa-graduation-cap', getFogColor(analysis.statistics.gunning_fog_index))}
                        ${generateModernReadabilityCard('SMOG Grade', analysis.statistics.smog_index, 'School grade level', 'fas fa-school', getGradeColor(analysis.statistics.smog_index))}
                        ${generateModernReadabilityCard('ARI Score', analysis.statistics.automated_readability_index, 'Age to understand', 'fas fa-user-graduate', getGradeColor(analysis.statistics.automated_readability_index))}
                    </div>
                </div>

                <!-- Writing Quality - Light Background Progress Bars -->
                <div class="mb-4">
                    <h6 class="text-center mb-3 fw-semibold d-flex align-items-center justify-content-center" style="color: #374151;">
                        <i class="fas fa-clipboard-check me-2" style="color: #059669;"></i>Writing Quality
                    </h6>
                    
                    <!-- Modern Passive Voice Indicator -->
                    <div class="mb-3 p-3 rounded-3" style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.1);">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-exchange-alt me-2" style="color: #3b82f6;"></i>
                                <span class="fw-medium" style="color: #1f2937;">Passive Voice</span>
                                <span class="badge bg-light text-dark ms-2 rounded-pill" data-bs-toggle="tooltip" title="Keep under 15% for active writing" style="font-size: 0.7rem;">?</span>
                            </div>
                            <span class="fw-bold" style="color: #1f2937;">${(analysis.statistics.passive_voice_percentage || 0).toFixed(1)}%</span>
                        </div>
                        <div class="progress mb-2" style="height: 8px; background: rgba(59, 130, 246, 0.1); border-radius: 10px;">
                            <div class="progress-bar" 
                                 style="width: ${Math.min(100, (analysis.statistics.passive_voice_percentage || 0) * 6.67)}%; border-radius: 10px; background: ${getModernPassiveVoiceGradient(analysis.statistics.passive_voice_percentage)};"></div>
                        </div>
                        <div class="small" style="color: #6b7280;">
                            ${getPassiveVoiceInsight(analysis.statistics.passive_voice_percentage)}
                        </div>
                    </div>

                    <!-- Modern Sentence Length Indicator -->
                    <div class="mb-3 p-3 rounded-3" style="background: rgba(6, 182, 212, 0.05); border: 1px solid rgba(6, 182, 212, 0.1);">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-text-width me-2" style="color: #06b6d4;"></i>
                                <span class="fw-medium" style="color: #1f2937;">Sentence Length</span>
                                <span class="badge bg-light text-dark ms-2 rounded-pill" data-bs-toggle="tooltip" title="Aim for 15-20 words per sentence" style="font-size: 0.7rem;">?</span>
                            </div>
                            <span class="fw-bold" style="color: #1f2937;">${(analysis.statistics.avg_sentence_length || 0).toFixed(1)} words</span>
                        </div>
                        <div class="progress mb-2" style="height: 8px; background: rgba(6, 182, 212, 0.1); border-radius: 10px;">
                            <div class="progress-bar" 
                                 style="width: ${Math.min(100, (analysis.statistics.avg_sentence_length || 0) * 2.5)}%; border-radius: 10px; background: ${getModernSentenceLengthGradient(analysis.statistics.avg_sentence_length)};"></div>
                        </div>
                        <div class="small" style="color: #6b7280;">
                            ${getSentenceLengthInsight(analysis.statistics.avg_sentence_length)}
                        </div>
                    </div>

                    <!-- Modern Word Complexity Indicator -->
                    <div class="mb-3 p-3 rounded-3" style="background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.1);">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-brain me-2" style="color: #8b5cf6;"></i>
                                <span class="fw-medium" style="color: #1f2937;">Complex Words</span>
                                <span class="badge bg-light text-dark ms-2 rounded-pill" data-bs-toggle="tooltip" title="Words with 3+ syllables" style="font-size: 0.7rem;">?</span>
                            </div>
                            <span class="fw-bold" style="color: #1f2937;">${(analysis.statistics.complex_words_percentage || 0).toFixed(1)}%</span>
                        </div>
                        <div class="progress mb-2" style="height: 8px; background: rgba(139, 92, 246, 0.1); border-radius: 10px;">
                            <div class="progress-bar" 
                                 style="width: ${Math.min(100, (analysis.statistics.complex_words_percentage || 0) * 3.33)}%; border-radius: 10px; background: ${getModernComplexWordsGradient(analysis.statistics.complex_words_percentage)};"></div>
                        </div>
                        <div class="small" style="color: #6b7280;">
                            ${getComplexWordsInsight(analysis.statistics.complex_words_percentage)}
                        </div>
                    </div>
                </div>

                <!-- Smart Recommendations - Clean Modern Design -->
                <div class="mt-4">
                    <h6 class="text-center mb-3 fw-semibold d-flex align-items-center justify-content-center" style="color: #374151;">
                        <i class="fas fa-lightbulb me-2" style="color: #f59e0b;"></i>Smart Recommendations
                    </h6>
                    <div class="smart-recommendations">
                        ${generateModernSmartRecommendations(analysis)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// HTML escape utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper functions for statistics card
function getGradeLevelInsight(gradeLevel, meetsTarget) {
    if (!gradeLevel) return 'Grade level could not be determined.';
    
    if (meetsTarget) {
        return 'Perfect! Your content is accessible to your target technical audience.';
    } else if (gradeLevel < 9) {
        return 'Content may be too simple for technical documentation.';
    } else {
        return 'Consider simplifying complex sentences for better accessibility.';
    }
}

function generateModernReadabilityCard(title, value, description, icon, color) {
    return `
        <div class="col-6 mb-2">
            <div class="text-center p-2 rounded-3" style="background: ${color}; color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div class="d-flex align-items-center justify-content-center mb-1">
                    <i class="${icon} me-2" style="font-size: 0.9rem;"></i>
                    <span class="fw-bold" style="font-size: 1.1rem;">${(value || 0).toFixed(1)}</span>
                </div>
                <div class="small fw-medium">${title}</div>
                <div class="small opacity-75" style="font-size: 0.7rem;">${description}</div>
            </div>
        </div>
    `;
}

function getFleschColor(score) {
    if (score >= 70) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score >= 50) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getFogColor(score) {
    if (score <= 12) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score <= 16) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getGradeColor(score) {
    if (score <= 12) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score <= 16) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernPassiveVoiceGradient(percentage) {
    if (percentage <= 15) return 'linear-gradient(135deg, #10b981, #059669)';
    if (percentage <= 25) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernSentenceLengthGradient(length) {
    if (length >= 15 && length <= 20) return 'linear-gradient(135deg, #10b981, #059669)';
    if (length <= 25) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernComplexWordsGradient(percentage) {
    if (percentage <= 20) return 'linear-gradient(135deg, #10b981, #059669)';
    if (percentage <= 30) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getPassiveVoiceInsight(percentage) {
    if (percentage <= 15) return 'Excellent active voice usage!';
    if (percentage <= 25) return 'Consider reducing passive voice usage.';
    return 'Too much passive voice. Rewrite for active voice.';
}

function getSentenceLengthInsight(length) {
    if (length >= 15 && length <= 20) return 'Perfect sentence length for technical writing!';
    if (length < 15) return 'Sentences might be too short. Consider combining some.';
    return 'Sentences are too long. Break them down for clarity.';
}

function getComplexWordsInsight(percentage) {
    if (percentage <= 20) return 'Good balance of complex and simple words.';
    if (percentage <= 30) return 'Consider simplifying some complex terms.';
    return 'Too many complex words may hurt readability.';
}

function generateModernSmartRecommendations(analysis) {
    const recommendations = [];
    
    // Add recommendations based on analysis
    if (analysis.statistics.passive_voice_percentage > 25) {
        recommendations.push('🎯 Reduce passive voice usage for clearer, more direct writing');
    }
    
    if (analysis.statistics.avg_sentence_length > 25) {
        recommendations.push('📝 Break down long sentences for better readability');
    }
    
    if (analysis.statistics.complex_words_percentage > 30) {
        recommendations.push('💡 Simplify complex terms where possible');
    }
    
    if (analysis.statistics.flesch_reading_ease < 50) {
        recommendations.push('📚 Improve readability with shorter sentences and simpler words');
    }
    
    if (recommendations.length === 0) {
        recommendations.push('✨ Excellent writing! Your content meets technical writing standards.');
    }
    
    return recommendations.map(rec => `
        <div class="alert alert-light border-start border-primary border-3 py-2 px-3 mb-2">
            <small class="text-dark">${rec}</small>
        </div>
    `).join('');
}
