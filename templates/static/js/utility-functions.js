// Utility functions for UI

// Show loading state
function showLoading(elementId, message = 'Processing...') {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-search me-2"></i>Analyzing Your Text
                    <span class="badge bg-primary ms-2">In Progress</span>
                </h5>
            </div>
            <div class="card-body text-center">
                <div class="mb-4">
                    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h6 class="text-primary">${message}</h6>
                </div>
                
                <div class="row text-start">
                    <div class="col-md-6">
                        <h6><i class="fas fa-check-circle text-success me-2"></i>What We're Analyzing:</h6>
                        <ul class="list-unstyled small text-muted">
                            <li><i class="fas fa-arrow-right me-2"></i>Sentence length and complexity</li>
                            <li><i class="fas fa-arrow-right me-2"></i>Passive voice usage</li>
                            <li><i class="fas fa-arrow-right me-2"></i>Wordy phrases and redundancy</li>
                            <li><i class="fas fa-arrow-right me-2"></i>Readability scores (Flesch, Fog, etc.)</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6><i class="fas fa-chart-line text-info me-2"></i>Metrics Calculated:</h6>
                        <ul class="list-unstyled small text-muted">
                            <li><i class="fas fa-arrow-right me-2"></i>Grade level assessment</li>
                            <li><i class="fas fa-arrow-right me-2"></i>Technical writing quality</li>
                            <li><i class="fas fa-arrow-right me-2"></i>Word complexity analysis</li>
                            <li><i class="fas fa-arrow-right me-2"></i>Overall improvement score</li>
                        </ul>
                    </div>
                </div>
                
                <div class="alert alert-info mt-3">
                    <small>
                        <i class="fas fa-lightbulb me-2"></i>
                        <strong>Tip:</strong> Analysis typically takes 2-5 seconds. We use SpaCy NLP for precise style detection.
                    </small>
                </div>
            </div>
        </div>
    `;
}

// Show error message
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="alert alert-danger">
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
        </div>
    `;
}

// Show success message
function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="alert alert-success">
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        </div>
    `;
}

// Highlight errors in text
function highlightErrors(text, errors) {
    if (!errors || errors.length === 0) return text;
    
    let highlightedText = text;
    
    errors.forEach(error => {
        const sentence = error.sentence || '';
        if (sentence) {
            const highlighted = `<span class="error-highlight">${sentence}</span>`;
            highlightedText = highlightedText.replace(sentence, highlighted);
        }
    });
    
    return highlightedText;
}

// Create error card
function createErrorCard(error) {
    const severityClass = error.severity === 'high' ? 'error-high' : 
                         error.severity === 'medium' ? 'error-medium' : 'error-low';
    
    return `
        <div class="card mb-3 border-start border-danger border-3">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <h6 class="card-title text-danger">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            ${error.error_type || 'Style Issue'}
                        </h6>
                        <p class="card-text">${error.message || 'Style issue detected'}</p>
                        
                        ${error.suggestion ? `
                        <div class="alert alert-info alert-sm">
                            <i class="fas fa-lightbulb me-2"></i>
                            <strong>Suggestion:</strong> ${error.suggestion}
                        </div>
                        ` : ''}
                        
                        ${error.sentence ? `
                        <div class="mt-2">
                            <small class="text-muted">
                                <strong>Context:</strong> "${error.sentence}"
                            </small>
                        </div>
                        ` : ''}
                    </div>
                    <span class="badge ${severityClass} ms-2">
                        ${error.severity || 'medium'}
                    </span>
                </div>
            </div>
        </div>
    `;
}

// Generate statistics card (placeholder - to be implemented)
function generateStatisticsCard(analysis) {
    return `
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-chart-line me-2"></i>Statistics
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-6">
                        <div class="text-center">
                            <h3 class="text-primary">${analysis.statistics.word_count || 0}</h3>
                            <small class="text-muted">Words</small>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="text-center">
                            <h3 class="text-info">${analysis.statistics.sentence_count || 0}</h3>
                            <small class="text-muted">Sentences</small>
                        </div>
                    </div>
                </div>
                
                <hr>
                
                <div class="mb-3">
                    <div class="d-flex justify-content-between">
                        <small>Readability Score</small>
                        <small>${(analysis.statistics.flesch_reading_ease || 0).toFixed(1)}</small>
                    </div>
                    <div class="progress">
                        <div class="progress-bar" style="width: ${Math.min(100, analysis.statistics.flesch_reading_ease || 0)}%"></div>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="d-flex justify-content-between">
                        <small>Avg. Sentence Length</small>
                        <small>${(analysis.statistics.avg_sentence_length || 0).toFixed(1)} words</small>
                    </div>
                </div>
                
                <div class="mb-3">
                    <div class="d-flex justify-content-between">
                        <small>Passive Voice</small>
                        <small>${(analysis.statistics.passive_voice_percentage || 0).toFixed(1)}%</small>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Display rewrite results (placeholder)
function displayRewriteResults(data) {
    const resultsContainer = document.getElementById('rewrite-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="card mt-4">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-magic me-2"></i>AI Rewrite Results
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6>Original:</h6>
                        <div class="bg-light p-3 rounded">
                            ${data.original || ''}
                        </div>
                    </div>
                    <div class="col-md-6">
                        <h6>Rewritten:</h6>
                        <div class="bg-success bg-opacity-10 p-3 rounded">
                            ${data.rewritten_text || ''}
                        </div>
                    </div>
                </div>
                
                ${data.improvements && data.improvements.length > 0 ? `
                <div class="mt-4">
                    <h6>Improvements Made:</h6>
                    <ul class="list-unstyled">
                        ${data.improvements.map(improvement => `
                            <li class="mb-2">
                                <i class="fas fa-check-circle text-success me-2"></i>
                                ${improvement}
                            </li>
                        `).join('')}
                    </ul>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Display refinement results (placeholder)
function displayRefinementResults(data) {
    const resultsContainer = document.getElementById('rewrite-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="card mt-4">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-sparkles me-2"></i>AI Refinement Results (Pass 2)
                </h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-4">
                        <h6>Original:</h6>
                        <div class="bg-light p-3 rounded small">
                            ${data.first_pass || ''}
                        </div>
                    </div>
                    <div class="col-md-4">
                        <h6>First Pass:</h6>
                        <div class="bg-info bg-opacity-10 p-3 rounded small">
                            ${data.first_pass || ''}
                        </div>
                    </div>
                    <div class="col-md-4">
                        <h6>Refined:</h6>
                        <div class="bg-success bg-opacity-10 p-3 rounded small">
                            ${data.refined || ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
} 