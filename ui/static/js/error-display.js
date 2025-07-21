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
                <span class="pf-v5-u-font-weight-bold">${formatRuleType(error.type || error.error_type)}</span>
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
                
                ${error.consolidated_from && error.consolidated_from.length > 1 ? `
                    <div class="pf-v5-u-mt-xs">
                        <span class="pf-v5-c-label pf-m-compact pf-m-blue">
                            <span class="pf-v5-c-label__content">
                                <i class="fas fa-compress-arrows-alt pf-v5-u-mr-xs"></i>
                                Consolidated from ${error.consolidated_from.length} rules
                            </span>
                        </span>
                        ${error.text_span ? `
                            <span class="pf-v5-c-label pf-m-compact pf-m-outline pf-v5-u-ml-xs">
                                <span class="pf-v5-c-label__content">"${error.text_span}"</span>
                            </span>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create enhanced error card for error summaries
function createErrorCard(error, index) {
    const typeStyle = getErrorTypeStyle(error.type);
    const suggestions = Array.isArray(error.suggestions) ? error.suggestions : [];
    
    return `
        <div class="pf-v5-c-card pf-m-compact app-card" style="border-left: 4px solid ${typeStyle.color};">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__title">
                    <h3 class="pf-v5-c-title pf-m-md">
                        <i class="${typeStyle.icon} pf-v5-u-mr-sm" style="color: ${typeStyle.color};"></i>
                        ${formatRuleType(error.type)}
                    </h3>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <p class="pf-v5-u-mb-sm">${error.message}</p>
                
                ${error.text_segment ? `
                    <div class="pf-v5-c-code-block pf-v5-u-mb-sm">
                        <div class="pf-v5-c-code-block__header">
                            <div class="pf-v5-c-code-block__actions">
                                <div class="pf-v5-c-code-block__actions-item">
                                    <span class="pf-v5-c-label pf-m-compact pf-m-outline">
                                        <span class="pf-v5-c-label__content">Text segment</span>
                                    </span>
                                </div>
                            </div>
                        </div>
                        <div class="pf-v5-c-code-block__content">
                            <pre class="pf-v5-c-code-block__pre">
                                <code class="pf-v5-c-code-block__code">${escapeHtml(error.text_segment)}</code>
                            </pre>
                        </div>
                    </div>
                ` : ''}
                
                ${error.consolidated_from && error.consolidated_from.length > 1 ? `
                    <div class="pf-v5-u-mt-xs">
                        <span class="pf-v5-c-label pf-m-compact pf-m-blue">
                            <span class="pf-v5-c-label__content">
                                <i class="fas fa-compress-arrows-alt pf-v5-u-mr-xs"></i>
                                Consolidated from ${error.consolidated_from.length} rules
                            </span>
                        </span>
                        ${error.text_span ? `
                            <span class="pf-v5-c-label pf-m-compact pf-m-outline pf-v5-u-ml-xs">
                                <span class="pf-v5-c-label__content">"${error.text_span}"</span>
                            </span>
                        ` : ''}
                        ${error.consolidation_type ? `
                            <span class="pf-v5-c-label pf-m-compact pf-m-outline pf-v5-u-ml-xs">
                                <span class="pf-v5-c-label__content">${error.consolidation_type}</span>
                            </span>
                        ` : ''}
                    </div>
                ` : ''}
                
                ${error.fix_options && error.fix_options.length > 1 ? `
                    <div class="pf-v5-u-mt-md">
                        <h4 class="pf-v5-c-title pf-m-sm pf-v5-u-mb-sm">
                            <i class="fas fa-tools pf-v5-u-mr-xs"></i>
                            Fix Options
                        </h4>
                        ${error.fix_options.map((option, optionIndex) => `
                            <div class="pf-v5-c-expandable-section pf-v5-u-mb-sm ${optionIndex === 0 ? 'pf-m-expanded' : ''}" 
                                 data-option-index="${optionIndex}">
                                <button type="button" class="pf-v5-c-expandable-section__toggle" 
                                        onclick="toggleFixOption(${index}, ${optionIndex})">
                                    <span class="pf-v5-c-expandable-section__toggle-icon">
                                        <i class="fas fa-angle-right" aria-hidden="true"></i>
                                    </span>
                                    <span class="pf-v5-c-expandable-section__toggle-text">
                                        <strong>${option.type === 'quick' ? '⚡ Quick Fix' : '🎯 Comprehensive Fix'}:</strong>
                                        ${option.description}
                                    </span>
                                </button>
                                <div class="pf-v5-c-expandable-section__content ${optionIndex === 0 ? '' : 'pf-m-hidden'}">
                                    <div class="pf-v5-u-pl-lg pf-v5-u-pt-sm">
                                        <div class="pf-v5-c-label-group pf-v5-u-mb-sm">
                                            <span class="pf-v5-c-label pf-m-compact ${option.scope === 'minimal' ? 'pf-m-green' : 'pf-m-blue'}">
                                                <span class="pf-v5-c-label__content">
                                                    Target: "${option.text_span}"
                                                </span>
                                            </span>
                                            <span class="pf-v5-c-label pf-m-compact pf-m-outline">
                                                <span class="pf-v5-c-label__content">
                                                    ${option.scope} scope
                                                </span>
                                            </span>
                                        </div>
                                        ${option.suggestions && option.suggestions.length > 0 ? `
                                            <ul class="pf-v5-c-list">
                                                ${option.suggestions.map(suggestion => `
                                                    <li>${suggestion}</li>
                                                `).join('')}
                                            </ul>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : suggestions.length > 0 ? `
                    <div class="pf-v5-u-mt-md">
                        <h4 class="pf-v5-c-title pf-m-sm pf-v5-u-mb-sm">
                            <i class="fas fa-lightbulb pf-v5-u-mr-xs"></i>
                            Suggestions
                        </h4>
                        <ul class="pf-v5-c-list">
                            ${suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${error.line_number ? `
                    <div class="pf-v5-u-mt-sm">
                        <span class="pf-v5-c-label pf-m-compact pf-m-outline">
                            <span class="pf-v5-c-label__content">Line ${error.line_number}</span>
                        </span>
                    </div>
                ` : ''}
            </div>
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
                                            ${formatRuleType(type)} Issues (${errorsByType[type].length})
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

// Add toggle function for fix options
function toggleFixOption(errorIndex, optionIndex) {
    const expandableSection = document.querySelector(`[data-option-index="${optionIndex}"]`);
    if (!expandableSection) return;
    
    const content = expandableSection.querySelector('.pf-v5-c-expandable-section__content');
    const icon = expandableSection.querySelector('.pf-v5-c-expandable-section__toggle-icon i');
    
    if (content.classList.contains('pf-m-hidden')) {
        // Expand
        content.classList.remove('pf-m-hidden');
        expandableSection.classList.add('pf-m-expanded');
        icon.style.transform = 'rotate(90deg)';
    } else {
        // Collapse
        content.classList.add('pf-m-hidden');
        expandableSection.classList.remove('pf-m-expanded');
        icon.style.transform = 'rotate(0deg)';
    }
} 