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
 * Get severity keyword and styling based on percentage
 * @param {number} percentage - Error percentage (0-100)
 * @returns {Object} - Object containing keyword, class, and icon
 */
function getSeverityInfo(percentage) {
    if (percentage >= 85) {
        return { keyword: 'Critical', class: 'pf-m-danger', icon: 'fas fa-exclamation-triangle' };
    } else if (percentage >= 70) {
        return { keyword: 'Error', class: 'pf-m-danger', icon: 'fas fa-times-circle' };
    } else if (percentage >= 50) {
        return { keyword: 'Warning', class: 'pf-m-warning', icon: 'fas fa-exclamation-circle' };
    } else {
        return { keyword: 'Suggestion', class: 'pf-m-info', icon: 'fas fa-lightbulb' };
    }
}

/**
 * Create confidence indicator badge with tooltip and severity keyword
 * @param {number} confidenceScore - Confidence score between 0 and 1
 * @param {boolean} showTooltip - Whether to include tooltip
 * @returns {string} - HTML string for confidence badge
 */
function createConfidenceBadge(confidenceScore, showTooltip = true) {
    const level = getConfidenceLevel(confidenceScore);
    const config = CONFIDENCE_LEVELS[level];
    const percentage = Math.round(confidenceScore * 100);
    
    // Get severity information based on percentage
    const severityInfo = getSeverityInfo(percentage);
    
    const tooltipId = `confidence-tooltip-${Math.random().toString(36).substr(2, 9)}`;
    
    return `
        <span class="pf-v5-c-label pf-m-compact ${config.class}">
            <span class="pf-v5-c-label__content">
                <i class="${config.icon} pf-v5-u-mr-xs"></i>
                ${percentage}%
            </span>
        </span>
        <span class="pf-v5-c-label pf-m-compact ${severityInfo.class} pf-v5-u-ml-xs">
            <span class="pf-v5-c-label__content">
                <i class="${severityInfo.icon} pf-v5-u-mr-xs"></i>
                ${severityInfo.keyword}
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
 * Create user-friendly confidence content for modal display
 * @param {Object} error - Error object
 * @param {number} confidenceScore - Confidence score (0-1)
 * @param {string} level - Confidence level (HIGH/MEDIUM/LOW)
 * @param {Object} config - Confidence level configuration
 * @returns {string} - HTML string for user-friendly confidence content
 */
function createUserFriendlyConfidenceContent(error, confidenceScore, level, config) {
    const percentage = Math.round(confidenceScore * 100);
    
    // Determine confidence explanation
    let confidenceExplanation = '';
    if (level === 'HIGH') {
        confidenceExplanation = 'The system is highly confident this is a valid issue that should be addressed.';
    } else if (level === 'MEDIUM') {
        confidenceExplanation = 'The system has moderate confidence this is an issue. Review carefully to confirm.';
    } else {
        confidenceExplanation = 'The system has low confidence about this issue. Consider it as a suggestion rather than a definitive problem.';
    }
    
    // Check if this is a consolidated error
    const isConsolidated = error.is_consolidated || (error.consolidated_from && error.consolidated_from.length > 1);
    
    // Create factors that influenced the confidence score
    let confidenceFactors = [];
    
    // Add rule type factor
    const errorType = error.type || error.error_type || 'unknown';
    confidenceFactors.push(`Issue type: ${formatRuleType(errorType)}`);
    
    // Add severity factor
    if (error.severity) {
        confidenceFactors.push(`Severity level: ${error.severity}`);
    }
    
    // Add consolidation factor if applicable
    if (isConsolidated) {
        const ruleCount = error.consolidated_from ? error.consolidated_from.length : error.consolidation_count || 2;
        confidenceFactors.push(`Multiple rules (${ruleCount}) detected similar issues`);
    }
    
    // Add validation factors if available
    if (error.validation_result) {
        const validation = error.validation_result;
        if (validation.passes_count) {
            confidenceFactors.push(`Passed ${validation.passes_count} validation checks`);
        }
        if (validation.consensus_score) {
            const consensusPercent = Math.round(validation.consensus_score * 100);
            confidenceFactors.push(`${consensusPercent}% validation consensus`);
        }
    }
    
    // Enhanced validation badge removed per user request
    let enhancedBadge = '';
    
    return `
        ${enhancedBadge}
        
        <!-- Main Confidence Score -->
        <div class="pf-v5-c-card pf-v5-u-mb-lg">
            <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                <div style="font-size: 3rem; font-weight: bold; color: ${config.class === 'pf-m-green' ? '#3E8635' : config.class === 'pf-m-orange' ? '#F0AB00' : '#C9190B'};">
                    ${percentage}%
                </div>
                <div class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">${config.label}</div>
                <p class="pf-v5-u-color-400">${confidenceExplanation}</p>
            </div>
        </div>
        
        <!-- Confidence Factors -->
        <div class="pf-v5-u-mb-lg">
            <h4 class="pf-v5-c-title pf-m-md pf-v5-u-mb-sm">
                <i class="fas fa-list-ul pf-v5-u-mr-xs"></i>
                What influenced this confidence score:
            </h4>
            <ul class="pf-v5-c-list">
                ${confidenceFactors.map(factor => `<li>${factor}</li>`).join('')}
            </ul>
        </div>
        
        <!-- Recommendation -->
        <div class="pf-v5-c-alert ${config.class === 'pf-m-green' ? 'pf-m-success' : config.class === 'pf-m-orange' ? 'pf-m-warning' : 'pf-m-info'}" role="alert">
            <div class="pf-v5-c-alert__icon">
                <i class="${config.icon}"></i>
            </div>
            <div class="pf-v5-c-alert__title">
                Recommendation
            </div>
            <div class="pf-v5-c-alert__description">
                ${level === 'HIGH' ? 'Address this issue to improve your content quality.' : 
                  level === 'MEDIUM' ? 'Consider addressing this issue if it aligns with your style goals.' : 
                  'Review this suggestion and apply only if it improves clarity or readability.'}
            </div>
        </div>
        
        ${isConsolidated ? `
            <div class="pf-v5-u-mt-lg">
                <div class="pf-v5-c-card">
                    <div class="pf-v5-c-card__header">
                        <h5 class="pf-v5-c-title pf-m-sm">
                            <i class="fas fa-compress-arrows-alt pf-v5-u-mr-xs"></i>
                            Consolidated Issue
                        </h5>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <p>This represents multiple similar issues found in the same area, combined for easier review. 
                        The confidence score reflects the combined strength of all detected issues.</p>
                    </div>
                </div>
            </div>
        ` : ''}
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
        
        // Create user-friendly content focusing on confidence analysis
        const userFriendlyContent = createUserFriendlyConfidenceContent(error, confidenceScore, level, config);
        
        // Create modal content
        const modalContent = `
            <div class="confidence-details-modal">
                <div class="pf-v5-c-modal-box pf-m-lg">
                    <div class="pf-v5-c-modal-box__header">
                        <h2 class="pf-v5-c-modal-box__title">
                            <i class="${config.icon} pf-v5-u-mr-sm" style="color: ${config.class === 'pf-m-green' ? '#3E8635' : config.class === 'pf-m-orange' ? '#F0AB00' : '#C9190B'};"></i>
                            Confidence Analysis
                        </h2>
                        <div class="pf-v5-c-modal-box__description">
                            How confident the system is about this issue
                        </div>
                    </div>
                    <div class="pf-v5-c-modal-box__body">
                        ${userFriendlyContent}
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

/**
 * Format rule type for display
 * @param {string} ruleType - Raw rule type string
 * @returns {string} - Formatted rule type
 */
function formatRuleType(ruleType) {
    if (!ruleType) return 'Unknown';
    
    // Convert snake_case and camelCase to readable format
    return ruleType
        .replace(/_/g, ' ')
        .replace(/([a-z])([A-Z])/g, '$1 $2')
        .toLowerCase()
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.ConfidenceSystem = {
        CONFIDENCE_LEVELS,
        getConfidenceLevel,
        extractConfidenceScore,
        safeBase64Encode,
        safeBase64Decode,
        getSeverityInfo,
        createConfidenceBadge,
        createConfidenceTooltip,
        createUserFriendlyConfidenceContent,
        showConfidenceDetails,
        closeConfidenceModal,
        filterErrorsByConfidence,
        sortErrorsByConfidence,
        formatRuleType
    };
}