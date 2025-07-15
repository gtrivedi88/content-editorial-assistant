/**
 * Error Display Module - Enhanced Error Cards and Inline Error Display
 * Handles all error-related UI components and styling with modern PatternFly design
 */

// Create enhanced inline error display with modern design
function createInlineError(error) {
    const errorTypes = {
        // Style and Grammar
        'style': { 
            color: 'var(--app-danger-color)', 
            bg: 'rgba(201, 25, 11, 0.05)', 
            icon: 'fas fa-exclamation-circle',
            modifier: 'danger'
        },
        'grammar': { 
            color: 'var(--app-warning-color)', 
            bg: 'rgba(240, 171, 0, 0.05)', 
            icon: 'fas fa-spell-check',
            modifier: 'warning'
        },
        'abbreviations': { 
            color: 'var(--app-warning-color)', 
            bg: 'rgba(240, 171, 0, 0.05)', 
            icon: 'fas fa-font',
            modifier: 'warning'
        },
        'articles': { 
            color: 'var(--app-warning-color)', 
            bg: 'rgba(240, 171, 0, 0.05)', 
            icon: 'fas fa-language',
            modifier: 'warning'
        },
        'capitalization': { 
            color: 'var(--app-success-color)', 
            bg: 'rgba(62, 134, 53, 0.05)', 
            icon: 'fas fa-font',
            modifier: 'success'
        },
        'second_person': { 
            color: 'var(--app-danger-color)', 
            bg: 'rgba(201, 25, 11, 0.05)', 
            icon: 'fas fa-user',
            modifier: 'danger'
        },
        'ambiguity': { 
            color: 'var(--app-danger-color)', 
            bg: 'rgba(201, 25, 11, 0.05)', 
            icon: 'fas fa-question-circle',
            modifier: 'danger'
        },
        // Structure and Format
        'structure': { 
            color: 'var(--app-primary-color)', 
            bg: 'rgba(0, 102, 204, 0.05)', 
            icon: 'fas fa-sitemap',
            modifier: 'info'
        },
        'punctuation': { 
            color: '#6b21a8', 
            bg: 'rgba(107, 33, 168, 0.05)', 
            icon: 'fas fa-quote-right',
            modifier: 'info'
        },
        'terminology': { 
            color: '#c2410c', 
            bg: 'rgba(194, 65, 12, 0.05)', 
            icon: 'fas fa-book',
            modifier: 'warning'
        },
        'passive_voice': { 
            color: 'var(--app-warning-color)', 
            bg: 'rgba(240, 171, 0, 0.05)', 
            icon: 'fas fa-exchange-alt',
            modifier: 'warning'
        },
        'readability': { 
            color: '#0e7490', 
            bg: 'rgba(14, 116, 144, 0.05)', 
            icon: 'fas fa-eye',
            modifier: 'info'
        },
        'admonitions': { 
            color: 'var(--app-primary-color)', 
            bg: 'rgba(0, 102, 204, 0.05)', 
            icon: 'fas fa-info-circle',
            modifier: 'info'
        },
        'headings': { 
            color: '#7c2d12', 
            bg: 'rgba(124, 45, 18, 0.05)', 
            icon: 'fas fa-heading',
            modifier: 'warning'
        },
        'lists': { 
            color: 'var(--app-success-color)', 
            bg: 'rgba(62, 134, 53, 0.05)', 
            icon: 'fas fa-list',
            modifier: 'success'
        },
        'procedures': { 
            color: '#0e7490', 
            bg: 'rgba(14, 116, 144, 0.05)', 
            icon: 'fas fa-tasks',
            modifier: 'info'
        }
    };
    
    const errorType = (error.type || error.error_type || 'style').toLowerCase();
    const typeStyle = errorTypes[errorType] || errorTypes['style'];
    
    return `
        <div class="pf-v5-c-alert pf-m-${typeStyle.modifier} pf-m-inline" role="alert" style="border-left: 4px solid ${typeStyle.color}; background-color: ${typeStyle.bg};">
            <div class="pf-v5-c-alert__icon">
                <i class="${typeStyle.icon}" style="color: ${typeStyle.color};"></i>
            </div>
            <div class="pf-v5-c-alert__title">
                <span class="pf-v5-u-font-weight-bold">${(error.type || error.error_type || 'Style Issue').replace(/_/g, ' ')}</span>
            </div>
            <div class="pf-v5-c-alert__description">
                <p class="pf-v5-u-mb-sm">${error.message || 'Style issue detected'}</p>
                ${error.suggestions && error.suggestions.length > 0 ? `
                    <div class="pf-v5-c-card pf-m-plain" style="background-color: rgba(255, 255, 255, 0.8); border-radius: var(--pf-v5-global--BorderRadius--sm); padding: 0.5rem;">
                        <div class="pf-v5-l-flex pf-m-align-items-flex-start">
                            <div class="pf-v5-l-flex__item">
                                <i class="fas fa-lightbulb" style="color: var(--app-warning-color); margin-right: 0.5rem;"></i>
                            </div>
                            <div class="pf-v5-l-flex__item">
                                <strong>Suggestion:</strong> ${Array.isArray(error.suggestions) ? error.suggestions[0] : error.suggestions || error.suggestion || 'No specific suggestion available'}
                            </div>
                        </div>
                    </div>
                ` : ''}
                ${error.line_number ? `
                    <div class="pf-v5-u-mt-xs">
                        <span class="pf-v5-c-label pf-m-compact pf-m-outline">
                            <span class="pf-v5-c-label__content">Line ${error.line_number}</span>
                        </span>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create enhanced error card for error summaries
function createErrorCard(error, index) {
    const errorTypes = {
        'STYLE': { icon: 'fas fa-exclamation-circle', color: 'var(--app-danger-color)', modifier: 'danger' },
        'GRAMMAR': { icon: 'fas fa-spell-check', color: 'var(--app-warning-color)', modifier: 'warning' },
        'STRUCTURE': { icon: 'fas fa-sitemap', color: 'var(--app-primary-color)', modifier: 'info' },
        'PUNCTUATION': { icon: 'fas fa-quote-right', color: '#6b21a8', modifier: 'info' },
        'CAPITALIZATION': { icon: 'fas fa-font', color: 'var(--app-success-color)', modifier: 'success' },
        'TERMINOLOGY': { icon: 'fas fa-book', color: '#c2410c', modifier: 'warning' },
        'PASSIVE_VOICE': { icon: 'fas fa-exchange-alt', color: 'var(--app-warning-color)', modifier: 'warning' },
        'READABILITY': { icon: 'fas fa-eye', color: '#0e7490', modifier: 'info' },
        'ADMONITIONS': { icon: 'fas fa-info-circle', color: 'var(--app-primary-color)', modifier: 'info' },
        'HEADINGS': { icon: 'fas fa-heading', color: '#7c2d12', modifier: 'warning' },
        'LISTS': { icon: 'fas fa-list', color: 'var(--app-success-color)', modifier: 'success' },
        'PROCEDURES': { icon: 'fas fa-tasks', color: '#0e7490', modifier: 'info' }
    };
    
    const errorType = error.error_type || 'STYLE';
    const typeStyle = errorTypes[errorType] || errorTypes['STYLE'];
    
    return `
        <div class="pf-v5-c-card pf-m-compact app-card" style="border-left: 4px solid ${typeStyle.color};">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <div class="pf-v5-l-flex pf-m-align-items-center">
                        <div class="pf-v5-l-flex__item">
                            <i class="${typeStyle.icon}" style="color: ${typeStyle.color}; font-size: 1.2rem;"></i>
                        </div>
                        <div class="pf-v5-l-flex__item pf-v5-u-ml-sm">
                            <h3 class="pf-v5-c-title pf-m-md">${errorType.replace(/_/g, ' ')}</h3>
                        </div>
                    </div>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-${typeStyle.modifier} pf-m-outline">
                        <span class="pf-v5-c-label__content">#${index + 1}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <p class="pf-v5-u-mb-sm">${error.message || 'Style issue detected'}</p>
                
                ${error.text_segment ? `
                    <div class="pf-v5-c-code-block pf-v5-u-mb-sm">
                        <div class="pf-v5-c-code-block__header">
                            <div class="pf-v5-c-code-block__header-main">
                                <span class="pf-v5-c-code-block__title">Found text:</span>
                            </div>
                        </div>
                        <div class="pf-v5-c-code-block__content">
                            <pre class="pf-v5-c-code-block__pre"><code class="pf-v5-c-code-block__code">${escapeHtml(error.text_segment)}</code></pre>
                        </div>
                    </div>
                ` : ''}
                
                ${error.suggestion ? `
                    <div class="pf-v5-c-alert pf-m-inline pf-m-plain" style="background-color: rgba(240, 171, 0, 0.1);">
                        <div class="pf-v5-c-alert__icon">
                            <i class="fas fa-lightbulb" style="color: var(--app-warning-color);"></i>
                        </div>
                        <div class="pf-v5-c-alert__title">
                            <strong>Suggestion</strong>
                        </div>
                        <div class="pf-v5-c-alert__description">
                            ${error.suggestion}
                        </div>
                    </div>
                ` : ''}
            </div>
            
            ${error.line_number || error.position ? `
                <div class="pf-v5-c-card__footer">
                    <div class="pf-v5-l-flex pf-m-space-items-sm">
                        ${error.line_number ? `
                            <div class="pf-v5-l-flex__item">
                                <span class="pf-v5-c-label pf-m-compact">
                                    <span class="pf-v5-c-label__content">
                                        <i class="fas fa-map-marker-alt pf-v5-c-label__icon"></i>
                                        Line ${error.line_number}
                                    </span>
                                </span>
                            </div>
                        ` : ''}
                        ${error.position ? `
                            <div class="pf-v5-l-flex__item">
                                <span class="pf-v5-c-label pf-m-compact">
                                    <span class="pf-v5-c-label__content">
                                        <i class="fas fa-crosshairs pf-v5-c-label__icon"></i>
                                        Pos ${error.position}
                                    </span>
                                </span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

// Create highlighted text for errors in content
function highlightErrors(content, errors) {
    if (!errors || errors.length === 0) {
        return escapeHtml(content);
    }
    
    let highlightedContent = escapeHtml(content);
    
    // Sort errors by position to avoid overlapping highlights
    const sortedErrors = errors
        .filter(error => error.text_segment && error.position !== undefined)
        .sort((a, b) => b.position - a.position); // Reverse order to avoid offset issues
    
    sortedErrors.forEach(error => {
        const segment = escapeHtml(error.text_segment);
        const errorType = error.error_type || 'STYLE';
        const colorMap = {
            'STYLE': 'var(--app-danger-color)',
            'GRAMMAR': 'var(--app-warning-color)', 
            'STRUCTURE': 'var(--app-primary-color)',
            'PUNCTUATION': '#6b21a8',
            'CAPITALIZATION': 'var(--app-success-color)',
            'TERMINOLOGY': '#c2410c',
            'PASSIVE_VOICE': 'var(--app-warning-color)',
            'READABILITY': '#0e7490'
        };
        
        const color = colorMap[errorType] || colorMap['STYLE'];
        const highlightedSegment = `<mark style="background-color: ${color}20; border-bottom: 2px solid ${color}; padding: 2px 4px; border-radius: 3px;" title="${error.message || 'Style issue'}" data-toggle="tooltip">${segment}</mark>`;
        
        highlightedContent = highlightedContent.replace(segment, highlightedSegment);
    });
    
    return highlightedContent;
}

// Enhanced error summary display
function createErrorSummary(errors) {
    if (!errors || errors.length === 0) {
        return `
            <div class="pf-v5-c-empty-state pf-m-lg">
                <div class="pf-v5-c-empty-state__content">
                    <i class="fas fa-check-circle pf-v5-c-empty-state__icon" style="color: var(--app-success-color);"></i>
                    <h2 class="pf-v5-c-title pf-m-lg">Excellent!</h2>
                    <div class="pf-v5-c-empty-state__body">
                        No issues detected in your content. Your writing follows best practices for style and clarity.
                    </div>
                </div>
            </div>
        `;
    }
    
    // Group errors by type
    const errorsByType = errors.reduce((acc, error) => {
        const type = error.error_type || 'STYLE';
        if (!acc[type]) acc[type] = [];
        acc[type].push(error);
        return acc;
    }, {});
    
    const errorTypeOrder = ['STYLE', 'GRAMMAR', 'STRUCTURE', 'PUNCTUATION', 'TERMINOLOGY', 'PASSIVE_VOICE', 'READABILITY'];
    
    return `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h2 class="pf-v5-c-title pf-m-xl">
                        <i class="fas fa-exclamation-triangle pf-v5-u-mr-sm" style="color: var(--app-warning-color);"></i>
                        Issues Detected (${errors.length})
                    </h2>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-l-stack pf-m-gutter">
                    ${errorTypeOrder
                        .filter(type => errorsByType[type])
                        .map(type => `
                            <div class="pf-v5-l-stack__item">
                                <div class="pf-v5-c-expandable-section" ${errorsByType[type].length <= 3 ? 'aria-expanded="true"' : ''}>
                                    <button type="button" class="pf-v5-c-expandable-section__toggle" aria-expanded="${errorsByType[type].length <= 3}">
                                        <span class="pf-v5-c-expandable-section__toggle-icon">
                                            <i class="fas fa-angle-right" aria-hidden="true"></i>
                                        </span>
                                        <span class="pf-v5-c-expandable-section__toggle-text">
                                            ${type.replace(/_/g, ' ')} Issues (${errorsByType[type].length})
                                        </span>
                                    </button>
                                    <div class="pf-v5-c-expandable-section__content">
                                        <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-mt-md">
                                            ${errorsByType[type].map((error, index) => `
                                                <div class="pf-v5-l-stack__item">
                                                    ${createErrorCard(error, index)}
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                </div>
            </div>
        </div>
    `;
} 