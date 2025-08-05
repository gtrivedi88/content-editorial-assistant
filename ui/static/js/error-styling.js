/**
 * Error Styling Module
 * Handles error type styling, visual appearance, color schemes, and inline error display
 */

/**
 * Get error type styling configuration including colors and icons
 * @param {string} ruleType - The type of rule/error
 * @returns {Object} - Configuration object with color and icon
 */
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

/**
 * Get comprehensive error type styling for inline errors including background colors and modifiers
 * @param {string} errorType - The type of error
 * @returns {Object} - Complete styling configuration
 */
function getInlineErrorStyle(errorType) {
    const type = (errorType || 'style').toLowerCase();
    
    const errorTypes = {
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
    
    return errorTypes[type] || errorTypes['style'];
}

/**
 * Get color mapping for text highlighting based on error type
 * @param {string} errorType - The type of error
 * @returns {string} - CSS color value
 */
function getHighlightColor(errorType) {
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
    
    return colorMap[errorType] || colorMap['STYLE'];
}

/**
 * Create enhanced inline error display with modern design and confidence indicators
 * @param {Object} error - Error object containing type, message, suggestions, etc.
 * @returns {string} - HTML string for inline error display
 */
function createInlineError(error) {
    // Use ConfidenceSystem if available
    const confidenceScore = window.ConfidenceSystem ? 
        window.ConfidenceSystem.extractConfidenceScore(error) : 
        (error.confidence_score || 0.5);
    
    const confidenceLevel = window.ConfidenceSystem ? 
        window.ConfidenceSystem.getConfidenceLevel(confidenceScore) : 
        (confidenceScore >= 0.7 ? 'HIGH' : confidenceScore >= 0.5 ? 'MEDIUM' : 'LOW');
    
    const errorType = (error.type || error.error_type || 'style').toLowerCase();
    const typeStyle = getInlineErrorStyle(errorType);
    
    // Apply confidence-based styling adjustments
    let opacityModifier = '';
    if (confidenceLevel === 'LOW') {
        opacityModifier = 'opacity: 0.8;';
    }
    
    // Create confidence badge using ConfidenceSystem if available
    const confidenceBadge = window.ConfidenceSystem ? 
        window.ConfidenceSystem.createConfidenceBadge(confidenceScore) : 
        `<span class="pf-v5-c-label pf-m-compact">${Math.round(confidenceScore * 100)}%</span>`;
    
    // Safe encoding function
    const safeEncode = window.ConfidenceSystem ? 
        window.ConfidenceSystem.safeBase64Encode : 
        (str) => btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (match, p1) => String.fromCharCode('0x' + p1)));
    
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
                    ${confidenceBadge}
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
                                onclick="showConfidenceDetails('${safeEncode(JSON.stringify(error))}')">
                            <i class="fas fa-info-circle"></i> Details
                        </button>
                    ` : ''}
                </div>
                
                <!-- Feedback Section -->
                <div class="pf-v5-u-mt-sm">
                    ${window.FeedbackSystem ? window.FeedbackSystem.createFeedbackButtons(error, 'inline') : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Apply confidence-based styling to error elements
 * @param {HTMLElement} element - DOM element to style
 * @param {string} confidenceLevel - 'HIGH', 'MEDIUM', or 'LOW'
 */
function applyConfidenceBasedStyling(element, confidenceLevel) {
    if (confidenceLevel === 'LOW') {
        element.style.opacity = '0.8';
        element.style.borderLeftStyle = 'dashed';
    }
}

/**
 * Generate CSS styles for error display styling
 * @returns {string} - CSS string for styling
 */
function generateErrorDisplayStyles() {
    return `
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
        
        .inline-error-metadata {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            align-items: center;
        }
        
        .enhanced-error {
            margin-bottom: 1rem;
        }
        
        .enhanced-error .pf-v5-c-alert__title {
            font-size: 0.9rem;
            margin-bottom: 0.5rem;
        }
        
        .enhanced-error .pf-v5-c-alert__description {
            font-size: 0.875rem;
            line-height: 1.4;
        }
        
        .enhanced-error .pf-v5-c-card.pf-m-plain {
            margin: 0.5rem 0;
        }
    `;
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.ErrorStyling = {
        getErrorTypeStyle,
        getInlineErrorStyle,
        getHighlightColor,
        createInlineError,
        applyConfidenceBasedStyling,
        generateErrorDisplayStyles
    };
}