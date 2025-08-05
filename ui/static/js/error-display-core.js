/**
 * Error Display Core Module
 * Main coordinator for all error display functionality, initialization, and public API
 * This module ties together all the modular error display components
 */

/**
 * Initialize error display system when page loads
 */
function initializeErrorDisplay() {
    // Initialize feedback tracking
    if (window.FeedbackSystem && window.FeedbackSystem.FeedbackTracker) {
        window.FeedbackSystem.FeedbackTracker.init();
    }
    
    // Inject CSS styles from all modules
    injectErrorDisplayStyles();
    
    console.log('Error Display System initialized with modular components');
}

/**
 * Inject CSS styles from all error display modules
 */
function injectErrorDisplayStyles() {
    const style = document.createElement('style');
    let combinedStyles = '';
    
    // Add styles from each module if available
    if (window.ErrorStyling && window.ErrorStyling.generateErrorDisplayStyles) {
        combinedStyles += window.ErrorStyling.generateErrorDisplayStyles();
    }
    
    if (window.ErrorCards && window.ErrorCards.generateErrorCardStyles) {
        combinedStyles += window.ErrorCards.generateErrorCardStyles();
    }
    
    if (window.ErrorHighlighting && window.ErrorHighlighting.generateHighlightingStyles) {
        combinedStyles += window.ErrorHighlighting.generateHighlightingStyles();
    }
    
    if (window.FeedbackSystem && window.FeedbackSystem.generateFeedbackStyles) {
        combinedStyles += window.FeedbackSystem.generateFeedbackStyles();
    }
    
    // Add core confidence styling
    combinedStyles += `
        .confidence-modal-backdrop {
            backdrop-filter: blur(2px);
        }
        
        .confidence-tooltip-content div {
            margin-bottom: 0.25rem;
        }
        
        /* PatternFly tooltip styling enhancements */
        .pf-v5-c-tooltip {
            max-width: 300px;
            word-wrap: break-word;
            white-space: normal;
        }
    `;
    
    style.textContent = combinedStyles;
    document.head.appendChild(style);
}

/**
 * Main public API function for creating inline error display
 * Delegates to ErrorStyling module if available, otherwise provides fallback
 * @param {Object} error - Error object
 * @returns {string} - HTML string for inline error
 */
function createInlineError(error) {
    if (window.ErrorStyling && window.ErrorStyling.createInlineError) {
        return window.ErrorStyling.createInlineError(error);
    }
    
    // Fallback implementation
    return createFallbackInlineError(error);
}

/**
 * Main public API function for creating error cards
 * Delegates to ErrorCards module if available, otherwise provides fallback
 * @param {Object} error - Error object
 * @param {number} index - Error index
 * @returns {string} - HTML string for error card
 */
function createErrorCard(error, index) {
    if (window.ErrorCards && window.ErrorCards.createErrorCard) {
        return window.ErrorCards.createErrorCard(error, index);
    }
    
    // Fallback implementation
    return createFallbackErrorCard(error, index);
}

/**
 * Main public API function for creating error summaries
 * Delegates to ErrorHighlighting module if available, otherwise provides fallback
 * @param {Array} errors - Array of error objects
 * @returns {string} - HTML string for error summary
 */
function createErrorSummary(errors) {
    if (window.ErrorHighlighting && window.ErrorHighlighting.createErrorSummary) {
        return window.ErrorHighlighting.createErrorSummary(errors);
    }
    
    // Fallback implementation
    return createFallbackErrorSummary(errors);
}

/**
 * Main public API function for highlighting errors in content
 * Delegates to ErrorHighlighting module if available, otherwise provides fallback
 * @param {string} content - Content to highlight
 * @param {Array} errors - Array of error objects
 * @returns {string} - HTML string with highlighted content
 */
function highlightErrors(content, errors) {
    if (window.ErrorHighlighting && window.ErrorHighlighting.highlightErrors) {
        return window.ErrorHighlighting.highlightErrors(content, errors);
    }
    
    // Fallback implementation
    return escapeHtml(content);
}

/**
 * Main public API function for filtering errors by confidence
 * Delegates to ConfidenceSystem module if available, otherwise provides fallback
 * @param {Array} errors - Array of error objects
 * @param {number} minConfidence - Minimum confidence threshold
 * @returns {Array} - Filtered array of errors
 */
function filterErrorsByConfidence(errors, minConfidence = 0.5) {
    if (window.ConfidenceSystem && window.ConfidenceSystem.filterErrorsByConfidence) {
        return window.ConfidenceSystem.filterErrorsByConfidence(errors, minConfidence);
    }
    
    // Fallback implementation
    return errors || [];
}

/**
 * Main public API function for sorting errors by confidence
 * Delegates to ConfidenceSystem module if available, otherwise provides fallback
 * @param {Array} errors - Array of error objects
 * @returns {Array} - Sorted array of errors
 */
function sortErrorsByConfidence(errors) {
    if (window.ConfidenceSystem && window.ConfidenceSystem.sortErrorsByConfidence) {
        return window.ConfidenceSystem.sortErrorsByConfidence(errors);
    }
    
    // Fallback implementation
    return errors || [];
}

// ===========================================================================
// FALLBACK IMPLEMENTATIONS
// ===========================================================================

/**
 * Fallback inline error display when modules are not available
 * @param {Object} error - Error object
 * @returns {string} - Basic HTML string for inline error
 */
function createFallbackInlineError(error) {
    return `
        <div class="pf-v5-c-alert pf-m-danger pf-m-inline" role="alert">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <div class="pf-v5-c-alert__title">
                ${formatRuleType(error.type || error.error_type)}
            </div>
            <div class="pf-v5-c-alert__description">
                ${error.message || 'Style issue detected'}
            </div>
        </div>
    `;
}

/**
 * Fallback error card when modules are not available
 * @param {Object} error - Error object
 * @param {number} index - Error index
 * @returns {string} - Basic HTML string for error card
 */
function createFallbackErrorCard(error, index) {
    return `
        <div class="pf-v5-c-card">
            <div class="pf-v5-c-card__header">
                <h3 class="pf-v5-c-title pf-m-md">
                    ${formatRuleType(error.type)}
                </h3>
            </div>
            <div class="pf-v5-c-card__body">
                <p>${error.message}</p>
                ${error.text_segment ? `
                    <div class="pf-v5-c-code-block">
                        <div class="pf-v5-c-code-block__content">
                            <code>"${escapeHtml(error.text_segment)}"</code>
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Fallback error summary when modules are not available
 * @param {Array} errors - Array of error objects
 * @returns {string} - Basic HTML string for error summary
 */
function createFallbackErrorSummary(errors) {
    if (!errors || errors.length === 0) {
        return `
            <div class="pf-v5-c-empty-state">
                <div class="pf-v5-c-empty-state__content">
                    <h2 class="pf-v5-c-title pf-m-lg">No Issues Found</h2>
                    <div class="pf-v5-c-empty-state__body">
                        Your content looks good!
                    </div>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="pf-v5-c-card">
            <div class="pf-v5-c-card__header">
                <h2 class="pf-v5-c-title pf-m-xl">Issues Detected (${errors.length})</h2>
            </div>
            <div class="pf-v5-c-card__body">
                ${errors.map((error, index) => createFallbackErrorCard(error, index)).join('')}
            </div>
        </div>
    `;
}

/**
 * Basic HTML escape utility for fallback implementations
 * @param {string} text - Text to escape
 * @returns {string} - HTML-escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ===========================================================================
// GLOBAL FUNCTION ALIASES FOR BACKWARD COMPATIBILITY
// ===========================================================================

// These functions are exposed globally to maintain compatibility with existing code
window.createInlineError = createInlineError;
window.createErrorCard = createErrorCard;
window.createErrorSummary = createErrorSummary;
window.highlightErrors = highlightErrors;
window.filterErrorsByConfidence = filterErrorsByConfidence;
window.sortErrorsByConfidence = sortErrorsByConfidence;

// Expose confidence functions if available
if (window.ConfidenceSystem) {
    window.showConfidenceDetails = window.ConfidenceSystem.showConfidenceDetails;
    window.closeConfidenceModal = window.ConfidenceSystem.closeConfidenceModal;
}

// Expose card functions if available
if (window.ErrorCards) {
    window.toggleFixOption = window.ErrorCards.toggleFixOption;
    window.toggleConfidenceSection = window.ErrorCards.toggleConfidenceSection;
}

// Expose feedback functions if available
if (window.FeedbackSystem) {
    window.submitFeedback = window.FeedbackSystem.submitFeedback;
    window.changeFeedback = window.FeedbackSystem.changeFeedback;
    window.submitFeedbackWithReason = window.FeedbackSystem.submitFeedbackWithReason;
    window.closeFeedbackReasonModal = window.FeedbackSystem.closeFeedbackReasonModal;
}

// Expose highlighting functions if available
if (window.ErrorHighlighting) {
    window.toggleErrorTypeSection = window.ErrorHighlighting.toggleErrorTypeSection;
}

// ===========================================================================
// INITIALIZATION
// ===========================================================================

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', initializeErrorDisplay);

// Export the main functions for module usage
if (typeof window !== 'undefined') {
    window.ErrorDisplayCore = {
        initializeErrorDisplay,
        injectErrorDisplayStyles,
        createInlineError,
        createErrorCard,
        createErrorSummary,
        highlightErrors,
        filterErrorsByConfidence,
        sortErrorsByConfidence,
        createFallbackInlineError,
        createFallbackErrorCard,
        createFallbackErrorSummary,
        escapeHtml
    };
}