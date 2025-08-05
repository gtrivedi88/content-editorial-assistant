/**
 * Error Display Module - Enhanced Error Cards and Inline Error Display
 * Handles all error-related UI components and styling with modern PatternFly design
 * Enhanced with confidence-based features and validation indicators
 */

// Confidence level thresholds and styling
const CONFIDENCE_LEVELS = {
    HIGH: { threshold: 0.7, class: 'pf-m-success', icon: 'fas fa-check-circle', label: 'High Confidence' },
    MEDIUM: { threshold: 0.5, class: 'pf-m-warning', icon: 'fas fa-info-circle', label: 'Medium Confidence' },
    LOW: { threshold: 0.0, class: 'pf-m-danger', icon: 'fas fa-exclamation-triangle', label: 'Low Confidence' }
};

// Get confidence level for a given score
function getConfidenceLevel(score) {
    if (score >= CONFIDENCE_LEVELS.HIGH.threshold) return 'HIGH';
    if (score >= CONFIDENCE_LEVELS.MEDIUM.threshold) return 'MEDIUM';
    return 'LOW';
}

// Extract confidence score from error object
function extractConfidenceScore(error) {
    return error.confidence_score || error.confidence || 
           (error.validation_result && error.validation_result.confidence_score) || 0.5;
}

// Safe Base64 encoding that handles Unicode characters
function safeBase64Encode(str) {
    try {
        // Convert Unicode string to UTF-8 bytes, then base64 encode
        return btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, function(match, p1) {
            return String.fromCharCode('0x' + p1);
        }));
    } catch (e) {
        console.warn('Failed to encode string for confidence details:', e);
        // Fallback: create a simple encoded representation without the problematic data
        try {
            const errorObj = JSON.parse(str);
            return btoa(JSON.stringify({
                type: 'encoding_error',
                message: 'Unable to encode error data for display',
                original_type: (errorObj.type || 'unknown'),
                confidence_score: (errorObj.confidence_score || 0.5)
            }));
        } catch (parseError) {
            // If we can't parse the string, create a minimal fallback
            return btoa(JSON.stringify({
                type: 'encoding_error',
                message: 'Unable to encode error data for display',
                original_type: 'unknown'
            }));
        }
    }
}

// Safe Base64 decoding that handles Unicode characters
function safeBase64Decode(encodedStr) {
    try {
        return decodeURIComponent(Array.prototype.map.call(atob(encodedStr), function(c) {
            return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
        }).join(''));
    } catch (e) {
        console.warn('Failed to decode confidence details:', e);
        return '{"type":"decoding_error","message":"Unable to decode error data"}';
    }
}

// Create confidence indicator badge
function createConfidenceBadge(confidenceScore, showTooltip = true) {
    const level = getConfidenceLevel(confidenceScore);
    const config = CONFIDENCE_LEVELS[level];
    const percentage = Math.round(confidenceScore * 100);
    
    const tooltipId = `confidence-tooltip-${Math.random().toString(36).substr(2, 9)}`;
    
    return `
        <span class="pf-v5-c-label pf-m-compact ${config.class}" 
              ${showTooltip ? `title="Confidence: ${percentage}% - ${config.label}"` : ''}>
            <span class="pf-v5-c-label__content">
                <i class="${config.icon} pf-v5-u-mr-xs"></i>
                ${percentage}%
            </span>
        </span>
    `;
}

// Create enhanced confidence tooltip with breakdown
function createConfidenceTooltip(error) {
    const confidenceScore = extractConfidenceScore(error);
    const level = getConfidenceLevel(confidenceScore);
    const config = CONFIDENCE_LEVELS[level];
    
    let breakdownHtml = '';
    
    // Check if error has detailed confidence breakdown
    if (error.confidence_calculation) {
        const calc = error.confidence_calculation;
        breakdownHtml = `
            <div class="confidence-breakdown" style="font-size: 0.875rem; margin-top: 0.5rem;">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">Confidence Breakdown:</div>
                <div>Method: ${calc.method || 'Standard'}</div>
                ${calc.weighted_average ? `<div>Weighted Average: ${Math.round(calc.weighted_average * 100)}%</div>` : ''}
                ${calc.primary_confidence ? `<div>Primary Score: ${Math.round(calc.primary_confidence * 100)}%</div>` : ''}
                ${calc.consolidation_penalty ? `<div>Consolidation Penalty: ${Math.round(calc.consolidation_penalty * 100)}%</div>` : ''}
            </div>
        `;
    }
    
    // Check if error has validation result details
    if (error.validation_result) {
        const validation = error.validation_result;
        breakdownHtml += `
            <div class="validation-breakdown" style="font-size: 0.875rem; margin-top: 0.5rem;">
                <div style="font-weight: 600; margin-bottom: 0.25rem;">Validation Details:</div>
                ${validation.decision ? `<div>Decision: ${validation.decision}</div>` : ''}
                ${validation.consensus_score ? `<div>Consensus: ${Math.round(validation.consensus_score * 100)}%</div>` : ''}
                ${validation.passes_count ? `<div>Validation Passes: ${validation.passes_count}</div>` : ''}
            </div>
        `;
    }
    
    return `
        <div class="confidence-tooltip-content">
            <div style="font-weight: 600;">${config.label}</div>
            <div style="margin: 0.25rem 0;">Confidence Score: ${Math.round(confidenceScore * 100)}%</div>
            ${breakdownHtml}
        </div>
    `;
}


// Create enhanced inline error display with modern design
function getErrorTypeStyle(ruleType) {
    const errorType = (ruleType || 'style').toLowerCase();

    const errorTypes = {
        'style': { color: 'var(--app-danger-color)', icon: 'fas fa-exclamation-circle' },
        'grammar': { color: 'var(--app-warning-color)', icon: 'fas fa-spell-check' },
        'abbreviations': { color: 'var(--app-warning-color)', icon: 'fas fa-font' },
        'articles': { color: 'var(--app-warning-color)', icon: 'fas fa-language' },
        'capitalization': { color: 'var(--app-success-color)', icon: 'fas fa-font' },
        'second_person': { color: 'var(--app-danger-color)', icon: 'fas fa-user' },
        'ambiguity': { color: 'var(--app-danger-color)', icon: 'fas fa-question-circle' },
        'structure': { color: 'var(--app-primary-color)', icon: 'fas fa-sitemap' },
        'punctuation': { color: '#6b21a8', icon: 'fas fa-quote-right' },
        'terminology': { color: '#c2410c', icon: 'fas fa-book' },
        'passive_voice': { color: 'var(--app-warning-color)', icon: 'fas fa-exchange-alt' },
        'readability': { color: '#0e7490', icon: 'fas fa-eye' },
        'admonitions': { color: 'var(--app-primary-color)', icon: 'fas fa-info-circle' },
        'headings': { color: '#7c2d12', icon: 'fas fa-heading' },
        'lists': { color: 'var(--app-success-color)', icon: 'fas fa-list' },
        'procedures': { color: '#0e7490', icon: 'fas fa-tasks' }
    };
    
    // Return the specific style or the default 'style' style
    return errorTypes[errorType] || errorTypes['style'];
}


// Create enhanced inline error display with modern design and confidence indicators
function createInlineError(error) {
    const errorType = (error.type || error.error_type || 'style').toLowerCase();
    const confidenceScore = extractConfidenceScore(error);
    
    const errorTypes = {
        'style': { color: 'var(--app-danger-color)', bg: 'rgba(201, 25, 11, 0.05)', icon: 'fas fa-exclamation-circle', modifier: 'danger' },
        'grammar': { color: 'var(--app-warning-color)', bg: 'rgba(240, 171, 0, 0.05)', icon: 'fas fa-spell-check', modifier: 'warning' },
        'abbreviations': { color: 'var(--app-warning-color)', bg: 'rgba(240, 171, 0, 0.05)', icon: 'fas fa-font', modifier: 'warning' },
        'articles': { color: 'var(--app-warning-color)', bg: 'rgba(240, 171, 0, 0.05)', icon: 'fas fa-language', modifier: 'warning' },
        'capitalization': { color: 'var(--app-success-color)', bg: 'rgba(62, 134, 53, 0.05)', icon: 'fas fa-font', modifier: 'success' },
        'second_person': { color: 'var(--app-danger-color)', bg: 'rgba(201, 25, 11, 0.05)', icon: 'fas fa-user', modifier: 'danger' },
        'ambiguity': { color: 'var(--app-danger-color)', bg: 'rgba(201, 25, 11, 0.05)', icon: 'fas fa-question-circle', modifier: 'danger' },
        'structure': { color: 'var(--app-primary-color)', bg: 'rgba(0, 102, 204, 0.05)', icon: 'fas fa-sitemap', modifier: 'info' },
        'punctuation': { color: '#6b21a8', bg: 'rgba(107, 33, 168, 0.05)', icon: 'fas fa-quote-right', modifier: 'info' },
        'terminology': { color: '#c2410c', bg: 'rgba(194, 65, 12, 0.05)', icon: 'fas fa-book', modifier: 'warning' },
        'passive_voice': { color: 'var(--app-warning-color)', bg: 'rgba(240, 171, 0, 0.05)', icon: 'fas fa-exchange-alt', modifier: 'warning' },
        'readability': { color: '#0e7490', bg: 'rgba(14, 116, 144, 0.05)', icon: 'fas fa-eye', modifier: 'info' },
        'admonitions': { color: 'var(--app-primary-color)', bg: 'rgba(0, 102, 204, 0.05)', icon: 'fas fa-info-circle', modifier: 'info' },
        'headings': { color: '#7c2d12', bg: 'rgba(124, 45, 18, 0.05)', icon: 'fas fa-heading', modifier: 'warning' },
        'lists': { color: 'var(--app-success-color)', bg: 'rgba(62, 134, 53, 0.05)', icon: 'fas fa-list', modifier: 'success' },
        'procedures': { color: '#0e7490', bg: 'rgba(14, 116, 144, 0.05)', icon: 'fas fa-tasks', modifier: 'info' }
    };
    
    const typeStyle = errorTypes[errorType] || errorTypes['style'];
    
    // Apply confidence-based styling adjustments
    const confidenceLevel = getConfidenceLevel(confidenceScore);
    let opacityModifier = '';
    if (confidenceLevel === 'LOW') {
        opacityModifier = 'opacity: 0.8;';
    }
    
    return `
        <div class="pf-v5-c-alert pf-m-${typeStyle.modifier} pf-m-inline enhanced-error" 
             role="alert" 
             style="border-left: 4px solid ${typeStyle.color}; background-color: ${typeStyle.bg}; ${opacityModifier}"
             data-confidence="${confidenceScore}"
             data-confidence-level="${confidenceLevel}">
            <div class="pf-v5-c-alert__icon">
                <i class="${typeStyle.icon}" style="color: ${typeStyle.color};"></i>
            </div>
            <div class="pf-v5-c-alert__title pf-v5-l-flex pf-m-justify-content-space-between pf-m-align-items-center">
                <span class="pf-v5-u-font-weight-bold">${formatRuleType(error.type || error.error_type)}</span>
                <div class="confidence-indicators">
                    ${createConfidenceBadge(confidenceScore)}
                    ${error.enhanced_validation_available ? `
                        <span class="pf-v5-c-label pf-m-compact pf-m-blue pf-v5-u-ml-xs">
                            <span class="pf-v5-c-label__content">
                                <i class="fas fa-robot pf-v5-u-mr-xs"></i>
                                Enhanced
                            </span>
                        </span>
                    ` : ''}
                </div>
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
                
                <div class="pf-v5-u-mt-xs inline-error-metadata">
                    ${error.line_number ? `
                        <span class="pf-v5-c-label pf-m-compact pf-m-outline">
                            <span class="pf-v5-c-label__content">Line ${error.line_number}</span>
                        </span>
                    ` : ''}
                    
                    ${error.consolidated_from && error.consolidated_from.length > 1 ? `
                        <span class="pf-v5-c-label pf-m-compact pf-m-blue ${error.line_number ? 'pf-v5-u-ml-xs' : ''}">
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
                    ` : ''}
                    
                    ${(error.confidence_calculation || error.validation_result) ? `
                        <button type="button" 
                                class="pf-v5-c-button pf-m-link pf-m-inline confidence-details-btn pf-v5-u-ml-xs" 
                                onclick="showConfidenceDetails('${safeBase64Encode(JSON.stringify(error))}')"
                                title="Show confidence details">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// Create enhanced error card for error summaries with confidence indicators
function createErrorCard(error, index) {
    const typeStyle = getErrorTypeStyle(error.type);
    const suggestions = Array.isArray(error.suggestions) ? error.suggestions : [];
    const confidenceScore = extractConfidenceScore(error);
    const confidenceLevel = getConfidenceLevel(confidenceScore);
    
    // Apply confidence-based styling
    let cardOpacity = '';
    if (confidenceLevel === 'LOW') {
        cardOpacity = 'opacity: 0.85;';
    }
    
    return `
        <div class="pf-v5-c-card pf-m-compact app-card enhanced-error-card" 
             style="border-left: 4px solid ${typeStyle.color}; ${cardOpacity}"
             data-confidence="${confidenceScore}"
             data-confidence-level="${confidenceLevel}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <div class="pf-v5-c-card__title">
                        <h3 class="pf-v5-c-title pf-m-md">
                            <i class="${typeStyle.icon} pf-v5-u-mr-sm" style="color: ${typeStyle.color};"></i>
                            ${formatRuleType(error.type)}
                        </h3>
                    </div>
                </div>
                <div class="pf-v5-c-card__actions">
                    <div class="confidence-indicators">
                        ${createConfidenceBadge(confidenceScore)}
                        ${error.enhanced_validation_available ? `
                            <span class="pf-v5-c-label pf-m-compact pf-m-blue pf-v5-u-ml-xs">
                                <span class="pf-v5-c-label__content">
                                    <i class="fas fa-robot pf-v5-u-mr-xs"></i>
                                    Enhanced
                                </span>
                            </span>
                        ` : ''}
                    </div>
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
                
                <!-- Confidence Details Section -->
                ${(error.confidence_calculation || error.validation_result) ? `
                    <div class="pf-v5-c-expandable-section pf-v5-u-mb-sm" data-confidence-expandable="${index}">
                        <button type="button" class="pf-v5-c-expandable-section__toggle" 
                                onclick="toggleConfidenceSection(${index})">
                            <span class="pf-v5-c-expandable-section__toggle-icon">
                                <i class="fas fa-angle-right" aria-hidden="true"></i>
                            </span>
                            <span class="pf-v5-c-expandable-section__toggle-text">
                                <i class="fas fa-chart-line pf-v5-u-mr-xs"></i>
                                Confidence Analysis
                            </span>
                        </button>
                        <div class="pf-v5-c-expandable-section__content pf-m-hidden">
                            <div class="pf-v5-u-pl-lg pf-v5-u-pt-sm">
                                ${createConfidenceTooltip(error)}
                            </div>
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
                
                <div class="error-card-metadata pf-v5-u-mt-sm">
                    ${error.line_number ? `
                        <span class="pf-v5-c-label pf-m-compact pf-m-outline">
                            <span class="pf-v5-c-label__content">Line ${error.line_number}</span>
                        </span>
                    ` : ''}
                    
                    ${error.sentence_index !== undefined ? `
                        <span class="pf-v5-c-label pf-m-compact pf-m-outline ${error.line_number ? 'pf-v5-u-ml-xs' : ''}">
                            <span class="pf-v5-c-label__content">Sentence ${error.sentence_index + 1}</span>
                        </span>
                    ` : ''}
                </div>
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

// Toggle confidence analysis section
function toggleConfidenceSection(errorIndex) {
    const expandableSection = document.querySelector(`[data-confidence-expandable="${errorIndex}"]`);
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

// Show confidence details in a modal
function showConfidenceDetails(encodedError) {
    try {
        const errorJson = safeBase64Decode(encodedError);
        const error = JSON.parse(errorJson);
        const confidenceScore = extractConfidenceScore(error);
        const level = getConfidenceLevel(confidenceScore);
        const config = CONFIDENCE_LEVELS[level];
        
        // Create modal content
        const modalContent = `
            <div class="confidence-details-modal">
                <div class="pf-v5-c-modal-box pf-m-lg">
                    <div class="pf-v5-c-modal-box__header">
                        <h2 class="pf-v5-c-modal-box__title">
                            <i class="${config.icon} pf-v5-u-mr-sm" style="color: ${config.class === 'pf-m-success' ? 'var(--app-success-color)' : config.class === 'pf-m-warning' ? 'var(--app-warning-color)' : 'var(--app-danger-color)'};"></i>
                            Confidence Analysis
                        </h2>
                        <div class="pf-v5-c-modal-box__description">
                            Detailed confidence breakdown for error detection
                        </div>
                    </div>
                    <div class="pf-v5-c-modal-box__body">
                        ${createConfidenceTooltip(error)}
                        
                        ${error.confidence_calculation ? `
                            <div class="pf-v5-u-mt-md">
                                <h4 class="pf-v5-c-title pf-m-sm">Technical Details</h4>
                                <div class="pf-v5-c-code-block">
                                    <div class="pf-v5-c-code-block__content">
                                        <pre class="pf-v5-c-code-block__pre">
                                            <code class="pf-v5-c-code-block__code">${JSON.stringify(error.confidence_calculation, null, 2)}</code>
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                    <div class="pf-v5-c-modal-box__footer">
                        <button class="pf-v5-c-button pf-m-primary" onclick="closeConfidenceModal()">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Show modal (simplified - in real implementation would use proper modal)
        const modal = document.createElement('div');
        modal.className = 'confidence-modal-backdrop';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        `;
        modal.innerHTML = modalContent;
        modal.onclick = (e) => {
            if (e.target === modal) closeConfidenceModal();
        };
        
        document.body.appendChild(modal);
        
    } catch (e) {
        console.error('Error showing confidence details:', e);
    }
}

// Close confidence modal
function closeConfidenceModal() {
    const modal = document.querySelector('.confidence-modal-backdrop');
    if (modal) {
        modal.remove();
    }
}

// Filter errors by confidence level
function filterErrorsByConfidence(errors, minConfidence = 0.5) {
    if (!errors || !Array.isArray(errors)) return [];
    
    return errors.filter(error => {
        const confidence = extractConfidenceScore(error);
        return confidence >= minConfidence;
    });
}

// Sort errors by confidence (highest first)
function sortErrorsByConfidence(errors) {
    if (!errors || !Array.isArray(errors)) return [];
    
    return [...errors].sort((a, b) => {
        const confA = extractConfidenceScore(a);
        const confB = extractConfidenceScore(b);
        return confB - confA;
    });
}

// Initialize confidence styling when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add confidence-based CSS classes for styling
    const style = document.createElement('style');
    style.textContent = `
        .enhanced-error[data-confidence-level="LOW"] {
            border-left-style: dashed !important;
        }
        
        .enhanced-error-card[data-confidence-level="LOW"] {
            border-left-style: dashed !important;
        }
        
        .confidence-indicators .pf-v5-c-label {
            font-size: 0.75rem;
        }
        
        .confidence-details-btn {
            font-size: 0.75rem;
            padding: 0.25rem 0.5rem;
        }
        
        .confidence-tooltip-content div {
            margin-bottom: 0.25rem;
        }
        
        .confidence-modal-backdrop {
            backdrop-filter: blur(2px);
        }
        
        /* PatternFly tooltip styling enhancements */
        .pf-v5-c-tooltip {
            max-width: 300px;
            word-wrap: break-word;
            white-space: normal;
        }
    `;
    document.head.appendChild(style);
}); 