/**
 * Confidence System Module
 * Handles confidence level calculations, scoring, badge generation, and related UI components
 */

// Confidence level thresholds and styling configuration
const CONFIDENCE_LEVELS = {
    HIGH: { threshold: 0.7, class: 'pf-m-green', icon: 'fas fa-check-circle', label: 'High Confidence' },
    MEDIUM: { threshold: 0.5, class: 'pf-m-orange', icon: 'fas fa-info-circle', label: 'Medium Confidence' },
    LOW: { threshold: 0.0, class: 'pf-m-red', icon: 'fas fa-exclamation-triangle', label: 'Low Confidence' }
};

/**
 * Get confidence level classification for a given score
 * @param {number} score - Confidence score between 0 and 1
 * @returns {string} - 'HIGH', 'MEDIUM', or 'LOW'
 */
function getConfidenceLevel(score) {
    if (score >= CONFIDENCE_LEVELS.HIGH.threshold) return 'HIGH';
    if (score >= CONFIDENCE_LEVELS.MEDIUM.threshold) return 'MEDIUM';
    return 'LOW';
}

/**
 * Extract confidence score from error object with fallback hierarchy
 * @param {Object} error - Error object that may contain confidence information
 * @returns {number} - Confidence score between 0 and 1
 */
function extractConfidenceScore(error) {
    return error.confidence_score || error.confidence || 
           (error.validation_result && error.validation_result.confidence_score) || 0.5;
}

/**
 * Safe Base64 encoding that handles Unicode characters
 * @param {string} str - String to encode
 * @returns {string} - Base64 encoded string
 */
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

/**
 * Safe Base64 decoding that handles Unicode characters
 * @param {string} encodedStr - Base64 encoded string
 * @returns {string} - Decoded string
 */
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

/**
 * Create confidence indicator badge with tooltip
 * @param {number} confidenceScore - Confidence score between 0 and 1
 * @param {boolean} showTooltip - Whether to include tooltip
 * @returns {string} - HTML string for confidence badge
 */
function createConfidenceBadge(confidenceScore, showTooltip = true) {
    const level = getConfidenceLevel(confidenceScore);
    const config = CONFIDENCE_LEVELS[level];
    const percentage = Math.round(confidenceScore * 100);
    
    const tooltipId = `confidence-tooltip-${Math.random().toString(36).substr(2, 9)}`;
    
    return `
        <span class="pf-v5-c-label pf-m-compact ${config.class}">
            <span class="pf-v5-c-label__content">
                <i class="${config.icon} pf-v5-u-mr-xs"></i>
                ${percentage}%
            </span>
        </span>
    `;
}

/**
 * Create enhanced confidence tooltip with detailed breakdown
 * @param {Object} error - Error object with confidence information
 * @returns {string} - HTML string for confidence tooltip
 */
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

/**
 * Show confidence details in a modal dialog
 * @param {string} encodedError - Base64 encoded error object
 */
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

/**
 * Close confidence modal dialog
 */
function closeConfidenceModal() {
    const modal = document.querySelector('.confidence-modal-backdrop');
    if (modal) {
        modal.remove();
    }
}

/**
 * Filter errors by minimum confidence level
 * @param {Array} errors - Array of error objects
 * @param {number} minConfidence - Minimum confidence threshold (0-1)
 * @returns {Array} - Filtered array of errors
 */
function filterErrorsByConfidence(errors, minConfidence = 0.5) {
    if (!errors || !Array.isArray(errors)) return [];
    
    return errors.filter(error => {
        const confidence = extractConfidenceScore(error);
        return confidence >= minConfidence;
    });
}

/**
 * Sort errors by confidence score (highest first)
 * @param {Array} errors - Array of error objects
 * @returns {Array} - Sorted array of errors
 */
function sortErrorsByConfidence(errors) {
    if (!errors || !Array.isArray(errors)) return [];
    
    return [...errors].sort((a, b) => {
        const confA = extractConfidenceScore(a);
        const confB = extractConfidenceScore(b);
        return confB - confA;
    });
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.ConfidenceSystem = {
        CONFIDENCE_LEVELS,
        getConfidenceLevel,
        extractConfidenceScore,
        safeBase64Encode,
        safeBase64Decode,
        createConfidenceBadge,
        createConfidenceTooltip,
        showConfidenceDetails,
        closeConfidenceModal,
        filterErrorsByConfidence,
        sortErrorsByConfidence
    };
}