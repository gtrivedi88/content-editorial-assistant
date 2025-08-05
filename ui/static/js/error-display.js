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
                
                <!-- Feedback Section -->
                <div class="pf-v5-u-mt-sm">
                    ${createFeedbackButtons(error, 'inline')}
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
                
                <!-- Feedback Section -->
                <div class="pf-v5-u-mt-md pf-v5-u-pt-sm" style="border-top: 1px solid var(--pf-v5-global--BorderColor--300);">
                    ${createFeedbackButtons(error, 'card')}
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

// ===========================================================================
// FEEDBACK COLLECTION SYSTEM
// ===========================================================================

// Session-based feedback tracking
const FeedbackTracker = {
    feedback: {},
    
    // Initialize feedback tracking
    init() {
        this.loadFromSession();
    },
    
    // Load feedback from sessionStorage
    loadFromSession() {
        try {
            const stored = sessionStorage.getItem('error_feedback');
            this.feedback = stored ? JSON.parse(stored) : {};
        } catch (e) {
            console.warn('Failed to load feedback from session:', e);
            this.feedback = {};
        }
    },
    
    // Save feedback to sessionStorage
    saveToSession() {
        try {
            sessionStorage.setItem('error_feedback', JSON.stringify(this.feedback));
        } catch (e) {
            console.warn('Failed to save feedback to session:', e);
        }
    },
    
    // Generate unique error ID for tracking
    generateErrorId(error) {
        const components = [
            error.type || 'unknown',
            error.message ? error.message.substring(0, 50) : 'nomessage',
            error.line_number || 'noline',
            error.text_segment ? error.text_segment.substring(0, 20) : 'notext'
        ];
        return btoa(components.join('|')).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
    },
    
    // Record feedback for an error
    recordFeedback(error, feedbackType, reason = null) {
        const errorId = this.generateErrorId(error);
        this.feedback[errorId] = {
            type: feedbackType, // 'helpful', 'not_helpful'
            reason: reason,
            timestamp: Date.now(),
            error_type: error.type,
            confidence_score: extractConfidenceScore(error)
        };
        this.saveToSession();
        return errorId;
    },
    
    // Get feedback for an error
    getFeedback(error) {
        const errorId = this.generateErrorId(error);
        return this.feedback[errorId] || null;
    },
    
    // Get feedback statistics
    getStats() {
        const values = Object.values(this.feedback);
        return {
            total: values.length,
            helpful: values.filter(f => f.type === 'helpful').length,
            not_helpful: values.filter(f => f.type === 'not_helpful').length,
            by_type: values.reduce((acc, f) => {
                acc[f.error_type] = acc[f.error_type] || { helpful: 0, not_helpful: 0 };
                acc[f.error_type][f.type]++;
                return acc;
            }, {})
        };
    }
};

// Create feedback buttons for error
function createFeedbackButtons(error, context = 'card') {
    const existingFeedback = FeedbackTracker.getFeedback(error);
    const errorId = FeedbackTracker.generateErrorId(error);
    
    if (existingFeedback) {
        // Show feedback confirmation
        return `
            <div class="feedback-section feedback-given" data-error-id="${errorId}">
                <div class="pf-v5-c-label pf-m-compact ${existingFeedback.type === 'helpful' ? 'pf-m-green' : 'pf-m-orange'}">
                    <span class="pf-v5-c-label__content">
                        <i class="fas ${existingFeedback.type === 'helpful' ? 'fa-thumbs-up' : 'fa-thumbs-down'} pf-v5-u-mr-xs"></i>
                        ${existingFeedback.type === 'helpful' ? 'Marked as helpful' : 'Marked as not helpful'}
                    </span>
                </div>
                <button type="button" 
                        class="pf-v5-c-button pf-m-link pf-m-small feedback-change-btn pf-v5-u-ml-xs" 
                        onclick="changeFeedback('${errorId}')"
                        title="Change feedback">
                    <i class="fas fa-edit"></i> Change
                </button>
            </div>
        `;
    }
    
    return `
        <div class="feedback-section" data-error-id="${errorId}">
            <div class="feedback-buttons-container">
                <span class="feedback-prompt pf-v5-u-mr-sm" style="font-size: 0.875rem; color: var(--pf-v5-global--Color--200);">
                    Was this helpful?
                </span>
                <button type="button" 
                        class="pf-v5-c-button pf-m-link pf-m-small feedback-btn feedback-helpful" 
                        onclick="submitFeedback('${errorId}', 'helpful', '${safeBase64Encode(JSON.stringify(error))}')"
                        title="This error detection was helpful">
                    <i class="fas fa-thumbs-up pf-v5-u-mr-xs"></i>
                    <span class="feedback-btn-text">Helpful</span>
                </button>
                <button type="button" 
                        class="pf-v5-c-button pf-m-link pf-m-small feedback-btn feedback-not-helpful pf-v5-u-ml-xs" 
                        onclick="submitFeedback('${errorId}', 'not_helpful', '${safeBase64Encode(JSON.stringify(error))}')"
                        title="This error detection was not helpful">
                    <i class="fas fa-thumbs-down pf-v5-u-mr-xs"></i>
                    <span class="feedback-btn-text">Not helpful</span>
                </button>
            </div>
        </div>
    `;
}

// Submit feedback with optional reason selection
function submitFeedback(errorId, feedbackType, encodedError) {
    try {
        const errorJson = safeBase64Decode(encodedError);
        const error = JSON.parse(errorJson);
        
        if (feedbackType === 'not_helpful') {
            // Show reason selection modal for negative feedback
            showFeedbackReasonModal(errorId, feedbackType, error);
        } else {
            // Direct submission for positive feedback
            processFeedbackSubmission(errorId, feedbackType, error, null);
        }
    } catch (e) {
        console.error('Failed to process feedback:', e);
        showFeedbackConfirmation(errorId, feedbackType, 'Error processing feedback. Please try again.');
    }
}

// Process the actual feedback submission
function processFeedbackSubmission(errorId, feedbackType, error, reason) {
    // Record feedback
    FeedbackTracker.recordFeedback(error, feedbackType, reason);
    
    // Update UI to show feedback confirmation
    const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
    if (feedbackSection) {
        feedbackSection.innerHTML = createFeedbackButtons(error);
    }
    
    // Show confirmation message
    const confirmationMessage = feedbackType === 'helpful' 
        ? 'Thank you! Your feedback helps improve error detection.'
        : 'Thank you for your feedback. This helps us improve error detection accuracy.';
    
    showFeedbackConfirmation(errorId, feedbackType, confirmationMessage);
}

// Change existing feedback
function changeFeedback(errorId) {
    const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
    if (!feedbackSection) return;
    
    // Find the error data to reconstruct the feedback buttons
    const errorCards = document.querySelectorAll('[data-error-id]');
    let error = null;
    
    // Extract error from existing feedback data
    const existingFeedback = Object.values(FeedbackTracker.feedback).find(f => 
        FeedbackTracker.generateErrorId({type: f.error_type}) === errorId
    );
    
    if (existingFeedback) {
        // Remove existing feedback
        delete FeedbackTracker.feedback[errorId];
        FeedbackTracker.saveToSession();
        
        // Show fresh feedback buttons
        feedbackSection.innerHTML = `
            <div class="feedback-buttons-container">
                <span class="feedback-prompt pf-v5-u-mr-sm" style="font-size: 0.875rem; color: var(--pf-v5-global--Color--200);">
                    Was this helpful?
                </span>
                <button type="button" 
                        class="pf-v5-c-button pf-m-link pf-m-small feedback-btn feedback-helpful" 
                        onclick="submitFeedback('${errorId}', 'helpful', '')"
                        title="This error detection was helpful">
                    <i class="fas fa-thumbs-up pf-v5-u-mr-xs"></i>
                    <span class="feedback-btn-text">Helpful</span>
                </button>
                <button type="button" 
                        class="pf-v5-c-button pf-m-link pf-m-small feedback-btn feedback-not-helpful pf-v5-u-ml-xs" 
                        onclick="submitFeedback('${errorId}', 'not_helpful', '')"
                        title="This error detection was not helpful">
                    <i class="fas fa-thumbs-down pf-v5-u-mr-xs"></i>
                    <span class="feedback-btn-text">Not helpful</span>
                </button>
            </div>
        `;
    }
}

// Show feedback reason selection modal for negative feedback
function showFeedbackReasonModal(errorId, feedbackType, error) {
    const modalContent = `
        <div class="feedback-reason-modal">
            <div class="pf-v5-c-modal-box pf-m-medium">
                <div class="pf-v5-c-modal-box__header">
                    <h2 class="pf-v5-c-modal-box__title">
                        <i class="fas fa-comment-alt pf-v5-u-mr-sm" style="color: var(--app-warning-color);"></i>
                        Help Us Improve
                    </h2>
                    <div class="pf-v5-c-modal-box__description">
                        Please let us know why this error detection wasn't helpful
                    </div>
                </div>
                <div class="pf-v5-c-modal-box__body">
                    <div class="error-context pf-v5-u-mb-md">
                        <div class="pf-v5-c-card pf-m-plain" style="background-color: var(--pf-v5-global--palette--black-150); padding: 1rem;">
                            <h4 class="pf-v5-c-title pf-m-sm">${formatRuleType(error.type)}</h4>
                            <p style="margin: 0.5rem 0;">${error.message}</p>
                            ${error.text_segment ? `
                                <div class="pf-v5-c-code-block pf-m-plain">
                                    <div class="pf-v5-c-code-block__content">
                                        <code class="pf-v5-c-code-block__code">"${error.text_segment}"</code>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <form id="feedback-reason-form">
                        <div class="pf-v5-c-form__group">
                            <fieldset class="pf-v5-c-form__fieldset">
                                <legend class="pf-v5-c-form__legend">
                                    <span class="pf-v5-c-form__legend-text">What's the main issue?</span>
                                </legend>
                                <div class="pf-v5-c-form__group-control">
                                    <div class="pf-v5-c-radio">
                                        <input class="pf-v5-c-radio__input" type="radio" id="reason-incorrect" name="feedback-reason" value="incorrect" />
                                        <label class="pf-v5-c-radio__label" for="reason-incorrect">
                                            <i class="fas fa-times-circle pf-v5-u-mr-xs" style="color: var(--app-danger-color);"></i>
                                            This is not actually an error
                                        </label>
                                    </div>
                                    <div class="pf-v5-c-radio pf-v5-u-mt-sm">
                                        <input class="pf-v5-c-radio__input" type="radio" id="reason-unclear" name="feedback-reason" value="unclear" />
                                        <label class="pf-v5-c-radio__label" for="reason-unclear">
                                            <i class="fas fa-question-circle pf-v5-u-mr-xs" style="color: var(--app-warning-color);"></i>
                                            The suggestion is unclear or confusing
                                        </label>
                                    </div>
                                    <div class="pf-v5-c-radio pf-v5-u-mt-sm">
                                        <input class="pf-v5-c-radio__input" type="radio" id="reason-context" name="feedback-reason" value="context" />
                                        <label class="pf-v5-c-radio__label" for="reason-context">
                                            <i class="fas fa-context pf-v5-u-mr-xs" style="color: var(--app-primary-color);"></i>
                                            Missing important context
                                        </label>
                                    </div>
                                    <div class="pf-v5-c-radio pf-v5-u-mt-sm">
                                        <input class="pf-v5-c-radio__input" type="radio" id="reason-style" name="feedback-reason" value="style" />
                                        <label class="pf-v5-c-radio__label" for="reason-style">
                                            <i class="fas fa-palette pf-v5-u-mr-xs" style="color: var(--app-secondary-color);"></i>
                                            This matches my writing style preference
                                        </label>
                                    </div>
                                    <div class="pf-v5-c-radio pf-v5-u-mt-sm">
                                        <input class="pf-v5-c-radio__input" type="radio" id="reason-other" name="feedback-reason" value="other" />
                                        <label class="pf-v5-c-radio__label" for="reason-other">
                                            <i class="fas fa-ellipsis-h pf-v5-u-mr-xs" style="color: var(--pf-v5-global--Color--200);"></i>
                                            Other reason
                                        </label>
                                    </div>
                                </div>
                            </fieldset>
                        </div>
                        
                        <div class="pf-v5-c-form__group pf-v5-u-mt-md">
                            <label class="pf-v5-c-form__label" for="feedback-comment">
                                <span class="pf-v5-c-form__label-text">Additional comments (optional)</span>
                            </label>
                            <div class="pf-v5-c-form__group-control">
                                <textarea class="pf-v5-c-form-control" 
                                          id="feedback-comment" 
                                          name="feedback-comment"
                                          placeholder="Help us understand how we can improve this error detection..."
                                          rows="3"></textarea>
                            </div>
                        </div>
                    </form>
                </div>
                <div class="pf-v5-c-modal-box__footer">
                    <button class="pf-v5-c-button pf-m-primary" 
                            onclick="submitFeedbackWithReason('${errorId}', '${feedbackType}', '${safeBase64Encode(JSON.stringify(error))}')">
                        Submit Feedback
                    </button>
                    <button class="pf-v5-c-button pf-m-link" onclick="closeFeedbackReasonModal()">
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Show modal
    const modal = document.createElement('div');
    modal.className = 'feedback-reason-modal-backdrop';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        backdrop-filter: blur(2px);
    `;
    
    modal.innerHTML = modalContent;
    modal.onclick = (e) => {
        if (e.target === modal) closeFeedbackReasonModal();
    };
    
    document.body.appendChild(modal);
    window.currentFeedbackModal = modal;
}

// Submit feedback with reason from modal
function submitFeedbackWithReason(errorId, feedbackType, encodedError) {
    try {
        const form = document.getElementById('feedback-reason-form');
        const selectedReason = form.querySelector('input[name="feedback-reason"]:checked');
        const comment = form.querySelector('#feedback-comment').value.trim();
        
        if (!selectedReason) {
            // Highlight the fieldset to show error
            const fieldset = form.querySelector('fieldset');
            fieldset.style.border = '2px solid var(--app-danger-color)';
            setTimeout(() => {
                fieldset.style.border = '';
            }, 3000);
            return;
        }
        
        const errorJson = safeBase64Decode(encodedError);
        const error = JSON.parse(errorJson);
        
        const reason = {
            category: selectedReason.value,
            comment: comment || null
        };
        
        // Close modal first
        closeFeedbackReasonModal();
        
        // Process feedback
        processFeedbackSubmission(errorId, feedbackType, error, reason);
        
    } catch (e) {
        console.error('Failed to submit feedback with reason:', e);
        showFeedbackConfirmation(errorId, feedbackType, 'Error submitting feedback. Please try again.');
    }
}

// Close feedback reason modal
function closeFeedbackReasonModal() {
    if (window.currentFeedbackModal) {
        window.currentFeedbackModal.remove();
        window.currentFeedbackModal = null;
    }
}

// Show feedback confirmation message
function showFeedbackConfirmation(errorId, feedbackType, message) {
    // Create toast notification
    const toast = document.createElement('div');
    toast.className = 'pf-v5-c-alert pf-m-success feedback-toast';
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10001;
        max-width: 400px;
        animation: slideInRight 0.3s ease-out;
    `;
    
    toast.innerHTML = `
        <div class="pf-v5-c-alert__icon">
            <i class="fas fa-check-circle" aria-hidden="true"></i>
        </div>
        <div class="pf-v5-c-alert__title">
            Feedback Received
        </div>
        <div class="pf-v5-c-alert__description">
            ${message}
        </div>
        <div class="pf-v5-c-alert__action">
            <button class="pf-v5-c-button pf-m-plain" onclick="this.closest('.feedback-toast').remove()">
                <i class="fas fa-times" aria-hidden="true"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }
    }, 5000);
}

// Initialize confidence styling and feedback system when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Initialize feedback tracking
    FeedbackTracker.init();
    
    // Add confidence-based and feedback CSS classes for styling
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
        
        /* Feedback system styling */
        .feedback-section {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            flex-wrap: wrap;
        }
        
        .feedback-buttons-container {
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }
        
        .feedback-btn {
            font-size: 0.875rem;
            padding: 0.25rem 0.5rem;
            transition: all 0.2s ease;
        }
        
        .feedback-btn:hover {
            transform: translateY(-1px);
        }
        
        .feedback-helpful:hover {
            color: var(--app-success-color) !important;
        }
        
        .feedback-not-helpful:hover {
            color: var(--app-warning-color) !important;
        }
        
        .feedback-given {
            animation: fadeInScale 0.3s ease-out;
        }
        
        .feedback-change-btn {
            font-size: 0.75rem;
            opacity: 0.7;
        }
        
        .feedback-change-btn:hover {
            opacity: 1;
        }
        
        .feedback-prompt {
            font-size: 0.875rem;
            color: var(--pf-v5-global--Color--200);
            font-weight: 500;
        }
        
        /* Feedback modal styling */
        .feedback-reason-modal .pf-v5-c-modal-box {
            max-width: 600px;
        }
        
        .feedback-reason-modal .error-context {
            border-left: 4px solid var(--app-primary-color);
        }
        
        .feedback-reason-modal .pf-v5-c-radio {
            margin-bottom: 0.75rem;
        }
        
        .feedback-reason-modal .pf-v5-c-radio__label {
            display: flex;
            align-items: center;
            padding: 0.5rem;
            border-radius: var(--pf-v5-global--BorderRadius--sm);
            transition: background-color 0.2s ease;
        }
        
        .feedback-reason-modal .pf-v5-c-radio__label:hover {
            background-color: var(--pf-v5-global--palette--black-150);
        }
        
        .feedback-reason-modal .pf-v5-c-radio__input:checked + .pf-v5-c-radio__label {
            background-color: var(--app-primary-color)20;
            border: 1px solid var(--app-primary-color);
        }
        
        /* Toast notification animations */
        @keyframes slideInRight {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        @keyframes slideOutRight {
            from {
                transform: translateX(0);
                opacity: 1;
            }
            to {
                transform: translateX(100%);
                opacity: 0;
            }
        }
        
        @keyframes fadeInScale {
            from {
                opacity: 0;
                transform: scale(0.9);
            }
            to {
                opacity: 1;
                transform: scale(1);
            }
        }
        
        .feedback-toast {
            animation: slideInRight 0.3s ease-out;
        }
    `;
    document.head.appendChild(style);
}); 