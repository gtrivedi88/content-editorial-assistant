// Enhanced Utility functions for PatternFly UI

// Show loading state using PatternFly EmptyState and Spinner
function showLoading(elementId, message = 'Processing...') {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-empty-state pf-m-lg">
                    <div class="pf-v5-c-empty-state__content">
                        <div class="pf-v5-c-empty-state__icon">
                            <span class="pf-v5-c-spinner pf-m-xl" role="status" aria-label="Loading...">
                                <span class="pf-v5-c-spinner__clipper"></span>
                                <span class="pf-v5-c-spinner__lead-ball"></span>
                                <span class="pf-v5-c-spinner__tail-ball"></span>
                            </span>
                        </div>
                        <h2 class="pf-v5-c-title pf-m-xl">Analyzing Your Content</h2>
                        <div class="pf-v5-c-empty-state__body">
                            <p class="pf-v5-u-mb-lg">${message}</p>
                            
                            <div class="pf-v5-l-grid pf-m-gutter">
                                <div class="pf-v5-l-grid__item pf-m-6-col">
                                    <div class="pf-v5-c-card pf-m-plain">
                                        <div class="pf-v5-c-card__body">
                                            <h3 class="pf-v5-c-title pf-m-md pf-v5-u-mb-sm">
                                                <i class="fas fa-search pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                                Analysis Features
                                            </h3>
                                            <ul class="pf-v5-c-list">
                                                <li class="pf-v5-c-list__item">Sentence length and complexity</li>
                                                <li class="pf-v5-c-list__item">Passive voice detection</li>
                                                <li class="pf-v5-c-list__item">Wordy phrases and redundancy</li>
                                                <li class="pf-v5-c-list__item">Readability scores</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                <div class="pf-v5-l-grid__item pf-m-6-col">
                                    <div class="pf-v5-c-card pf-m-plain">
                                        <div class="pf-v5-c-card__body">
                                            <h3 class="pf-v5-c-title pf-m-md pf-v5-u-mb-sm">
                                                <i class="fas fa-chart-line pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                                                Metrics Calculated
                                            </h3>
                                            <ul class="pf-v5-c-list">
                                                <li class="pf-v5-c-list__item">Grade level assessment</li>
                                                <li class="pf-v5-c-list__item">Technical writing quality</li>
                                                <li class="pf-v5-c-list__item">Word complexity analysis</li>
                                                <li class="pf-v5-c-list__item">Improvement recommendations</li>
                                            </ul>
                                        </div>
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

// Show error message using enhanced PatternFly Alert
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="pf-v5-c-alert pf-m-danger pf-m-inline fade-in" role="alert">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h4 class="pf-v5-c-alert__title">Analysis Error</h4>
            <div class="pf-v5-c-alert__description">
                <p>${message}</p>
                <div class="pf-v5-u-mt-sm">
                    <button class="pf-v5-c-button pf-m-link pf-m-inline" type="button" onclick="location.reload()">
                        <i class="fas fa-redo pf-v5-u-mr-xs"></i>
                        Try Again
                    </button>
                </div>
            </div>
            <div class="pf-v5-c-alert__action">
                <button class="pf-v5-c-button pf-m-plain" type="button" onclick="this.closest('.pf-v5-c-alert').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
}

// Show success message using enhanced PatternFly Alert
function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="pf-v5-c-alert pf-m-success pf-m-inline fade-in" role="alert">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <h4 class="pf-v5-c-alert__title">${message}</h4>
            <div class="pf-v5-c-alert__action">
                <button class="pf-v5-c-button pf-m-plain" type="button" onclick="this.closest('.pf-v5-c-alert').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
}

// Basic highlight errors function (enhanced version is in error-display.js)
function highlightErrors(text, errors) {
    if (!errors || errors.length === 0) return escapeHtml(text);
    
    let highlightedText = escapeHtml(text);
    
    // Simple highlighting - just mark error text
    errors.forEach(error => {
        if (error.text_segment) {
            const segment = escapeHtml(error.text_segment);
            const highlightedSegment = `<mark style="background-color: rgba(201, 25, 11, 0.1); border-bottom: 2px solid var(--app-danger-color);">${segment}</mark>`;
            highlightedText = highlightedText.replace(segment, highlightedSegment);
        }
    });
    
    return highlightedText;
}

// Basic error card function (enhanced version is in error-display.js)
function createErrorCard(error, index = 0) {
    const errorType = error.error_type || 'STYLE';
    const message = error.message || 'Style issue detected';
    
    return `
        <div class="pf-v5-c-alert pf-m-warning pf-m-inline pf-v5-u-mb-sm">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="pf-v5-c-alert__title">${errorType.replace(/_/g, ' ')}</div>
            <div class="pf-v5-c-alert__description">${message}</div>
        </div>
    `;
}

// Enhanced display rewrite results (now properly implemented)
function displayRewriteResults(data) {
    const resultsContainer = document.getElementById('rewrite-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-c-card app-card">
                    <div class="pf-v5-c-card__header">
                        <div class="pf-v5-c-card__header-main">
                            <h2 class="pf-v5-c-title pf-m-xl">
                                <i class="fas fa-magic pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                AI Rewrite Results
                            </h2>
                        </div>
                        <div class="pf-v5-c-card__actions">
                            <div class="pf-v5-l-flex pf-m-space-items-sm">
                                <div class="pf-v5-l-flex__item">
                                    <span class="pf-v5-c-label pf-m-green">
                                        <span class="pf-v5-c-label__content">
                                            <i class="fas fa-check-circle pf-v5-c-label__icon"></i>
                                            Improved
                                        </span>
                                    </span>
                                </div>
                                <div class="pf-v5-l-flex__item">
                                    <button class="pf-v5-c-button pf-m-secondary" type="button" onclick="refineContent('${escapeHtml(data.rewritten_content)}')">
                                        <i class="fas fa-star pf-v5-u-mr-xs"></i>
                                        Refine Further
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <div class="pf-v5-c-code-block">
                            <div class="pf-v5-c-code-block__header">
                                <div class="pf-v5-c-code-block__header-main">
                                    <span class="pf-v5-c-code-block__title">Improved Content</span>
                                </div>
                                <div class="pf-v5-c-code-block__actions">
                                    <button class="pf-v5-c-button pf-m-plain pf-m-small" type="button" onclick="copyToClipboard('${escapeHtml(data.rewritten_content).replace(/'/g, "\\'")}')">
                                        <i class="fas fa-copy" aria-hidden="true"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="pf-v5-c-code-block__content">
                                <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; word-wrap: break-word;"><code class="pf-v5-c-code-block__code">${escapeHtml(data.rewritten_content)}</code></pre>
                            </div>
                        </div>
                        
                        ${data.improvements && data.improvements.length > 0 ? `
                            <div class="pf-v5-u-mt-lg">
                                <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">Key Improvements</h3>
                                <div class="pf-v5-l-stack pf-m-gutter">
                                    ${data.improvements.map(improvement => `
                                        <div class="pf-v5-l-stack__item">
                                            <div class="pf-v5-c-alert pf-m-success pf-m-inline">
                                                <div class="pf-v5-c-alert__icon">
                                                    <i class="fas fa-arrow-up"></i>
                                                </div>
                                                <div class="pf-v5-c-alert__title">
                                                    ${improvement}
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// Enhanced display refinement results (now properly implemented)
function displayRefinementResults(data) {
    const resultsContainer = document.getElementById('rewrite-results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-c-card app-card">
                    <div class="pf-v5-c-card__header">
                        <div class="pf-v5-c-card__header-main">
                            <h2 class="pf-v5-c-title pf-m-xl">
                                <i class="fas fa-sparkles pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                AI Refinement Results (Pass 2)
                            </h2>
                        </div>
                        <div class="pf-v5-c-card__actions">
                            <span class="pf-v5-c-label pf-m-green pf-m-large">
                                <span class="pf-v5-c-label__content">
                                    <i class="fas fa-star pf-v5-c-label__icon"></i>
                                    Refined
                                </span>
                            </span>
                        </div>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <div class="pf-v5-c-code-block">
                            <div class="pf-v5-c-code-block__header">
                                <div class="pf-v5-c-code-block__header-main">
                                    <span class="pf-v5-c-code-block__title">Refined Content</span>
                                </div>
                                <div class="pf-v5-c-code-block__actions">
                                    <button class="pf-v5-c-button pf-m-plain pf-m-small" type="button" onclick="copyToClipboard('${escapeHtml(data.refined_content).replace(/'/g, "\\'")}')">
                                        <i class="fas fa-copy" aria-hidden="true"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="pf-v5-c-code-block__content">
                                <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; word-wrap: break-word;"><code class="pf-v5-c-code-block__code">${escapeHtml(data.refined_content)}</code></pre>
                            </div>
                        </div>
                        
                        ${data.refinements && data.refinements.length > 0 ? `
                            <div class="pf-v5-u-mt-lg">
                                <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">Refinements Made</h3>
                                <div class="pf-v5-l-stack pf-m-gutter">
                                    ${data.refinements.map(refinement => `
                                        <div class="pf-v5-l-stack__item">
                                            <div class="pf-v5-c-alert pf-m-info pf-m-inline">
                                                <div class="pf-v5-c-alert__icon">
                                                    <i class="fas fa-lightbulb"></i>
                                                </div>
                                                <div class="pf-v5-c-alert__title">
                                                    ${refinement}
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
