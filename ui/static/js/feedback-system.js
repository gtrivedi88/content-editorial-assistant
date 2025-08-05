/**
 * Feedback System Module
 * Handles user feedback collection, tracking, modal interactions, and session persistence
 */

// Session-based feedback tracking object
const FeedbackTracker = {
    feedback: {},
    
    /**
     * Initialize feedback tracking system
     */
    init() {
        this.loadFromSession();
    },
    
    /**
     * Load feedback data from sessionStorage
     */
    loadFromSession() {
        try {
            const stored = sessionStorage.getItem('error_feedback');
            this.feedback = stored ? JSON.parse(stored) : {};
        } catch (e) {
            console.warn('Failed to load feedback from session:', e);
            this.feedback = {};
        }
    },
    
    /**
     * Save feedback data to sessionStorage
     */
    saveToSession() {
        try {
            sessionStorage.setItem('error_feedback', JSON.stringify(this.feedback));
        } catch (e) {
            console.warn('Failed to save feedback to session:', e);
        }
    },
    
    /**
     * Generate unique error ID for tracking
     * @param {Object} error - Error object
     * @returns {string} - Unique identifier for the error
     */
    generateErrorId(error) {
        const components = [
            error.type || 'unknown',
            error.message ? error.message.substring(0, 50) : 'nomessage',
            error.line_number || 'noline',
            error.text_segment ? error.text_segment.substring(0, 20) : 'notext'
        ];
        return btoa(components.join('|')).replace(/[^a-zA-Z0-9]/g, '').substring(0, 16);
    },
    
    /**
     * Record feedback for an error
     * @param {Object} error - Error object
     * @param {string} feedbackType - 'helpful' or 'not_helpful'
     * @param {Object|null} reason - Detailed reason object
     * @returns {string} - Error ID
     */
    recordFeedback(error, feedbackType, reason = null) {
        const errorId = this.generateErrorId(error);
        const confidenceScore = window.ConfidenceSystem ? 
            window.ConfidenceSystem.extractConfidenceScore(error) : 
            (error.confidence_score || 0.5);
        
        this.feedback[errorId] = {
            type: feedbackType, // 'helpful', 'not_helpful'
            reason: reason,
            timestamp: Date.now(),
            error_type: error.type,
            confidence_score: confidenceScore
        };
        this.saveToSession();
        return errorId;
    },
    
    /**
     * Get feedback for an error
     * @param {Object} error - Error object
     * @returns {Object|null} - Feedback object or null
     */
    getFeedback(error) {
        const errorId = this.generateErrorId(error);
        return this.feedback[errorId] || null;
    },
    
    /**
     * Get feedback statistics
     * @returns {Object} - Statistics object
     */
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

/**
 * Create feedback buttons for error
 * @param {Object} error - Error object
 * @param {string} context - 'card' or 'inline' context
 * @returns {string} - HTML string for feedback buttons
 */
function createFeedbackButtons(error, context = 'card') {
    const existingFeedback = FeedbackTracker.getFeedback(error);
    const errorId = FeedbackTracker.generateErrorId(error);
    
    if (existingFeedback) {
        // Show feedback confirmation
        return createFeedbackConfirmation(errorId, existingFeedback);
    }
    
    return createFeedbackPrompt(errorId, error);
}

/**
 * Create feedback confirmation display
 * @param {string} errorId - Error ID
 * @param {Object} existingFeedback - Existing feedback object
 * @returns {string} - HTML string for feedback confirmation
 */
function createFeedbackConfirmation(errorId, existingFeedback) {
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
                    onclick="changeFeedback('${errorId}')">
                <i class="fas fa-edit"></i> Change
            </button>
        </div>
    `;
}

/**
 * Create feedback prompt with buttons
 * @param {string} errorId - Error ID
 * @param {Object} error - Error object
 * @returns {string} - HTML string for feedback prompt
 */
function createFeedbackPrompt(errorId, error) {
    const safeEncode = window.ConfidenceSystem ? 
        window.ConfidenceSystem.safeBase64Encode : 
        (str) => btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (match, p1) => String.fromCharCode('0x' + p1)));
    
    return `
        <div class="feedback-section" data-error-id="${errorId}">
            <div class="feedback-buttons-container">
                <span class="feedback-prompt pf-v5-u-mr-sm" style="font-size: 0.875rem; color: var(--pf-v5-global--Color--200);">
                    Was this helpful?
                </span>
                <button type="button" 
                        class="pf-v5-c-button pf-m-link pf-m-small feedback-btn feedback-helpful" 
                        onclick="submitFeedback('${errorId}', 'helpful', '${safeEncode(JSON.stringify(error))}')">
                    <i class="fas fa-thumbs-up pf-v5-u-mr-xs"></i>
                    <span class="feedback-btn-text">Helpful</span>
                </button>
                <button type="button" 
                        class="pf-v5-c-button pf-m-link pf-m-small feedback-btn feedback-not-helpful pf-v5-u-ml-xs" 
                        onclick="submitFeedback('${errorId}', 'not_helpful', '${safeEncode(JSON.stringify(error))}')">
                    <i class="fas fa-thumbs-down pf-v5-u-mr-xs"></i>
                    <span class="feedback-btn-text">Not helpful</span>
                </button>
            </div>
        </div>
    `;
}

/**
 * Submit feedback with optional reason selection
 * @param {string} errorId - Error ID
 * @param {string} feedbackType - 'helpful' or 'not_helpful'
 * @param {string} encodedError - Base64 encoded error object
 */
function submitFeedback(errorId, feedbackType, encodedError) {
    try {
        const safeDecode = window.ConfidenceSystem ? 
            window.ConfidenceSystem.safeBase64Decode : 
            (str) => decodeURIComponent(Array.prototype.map.call(atob(str), c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
        
        const errorJson = safeDecode(encodedError);
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
        // Error is logged to console - no toast message needed
    }
}

/**
 * Process the actual feedback submission
 * @param {string} errorId - Error ID
 * @param {string} feedbackType - 'helpful' or 'not_helpful'
 * @param {Object} error - Error object
 * @param {Object|null} reason - Reason object
 */
function processFeedbackSubmission(errorId, feedbackType, error, reason) {
    // Record feedback
    FeedbackTracker.recordFeedback(error, feedbackType, reason);
    
    // Update UI to show feedback confirmation
    const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
    if (feedbackSection) {
        feedbackSection.innerHTML = createFeedbackButtons(error);
    }
    
    // No confirmation message needed - UI state change is sufficient
}

/**
 * Change existing feedback
 * @param {string} errorId - Error ID
 */
function changeFeedback(errorId) {
    const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
    if (!feedbackSection) return;
    
    // Find the error data to reconstruct the feedback buttons
    const existingFeedback = Object.values(FeedbackTracker.feedback).find(f => 
        FeedbackTracker.generateErrorId({type: f.error_type}) === errorId
    );
    
    if (existingFeedback) {
        // Remove existing feedback
        delete FeedbackTracker.feedback[errorId];
        FeedbackTracker.saveToSession();
        
        // Show fresh feedback buttons
        feedbackSection.innerHTML = createFeedbackPrompt(errorId, {type: existingFeedback.error_type});
    }
}

/**
 * Show feedback reason selection modal for negative feedback
 * @param {string} errorId - Error ID
 * @param {string} feedbackType - Feedback type
 * @param {Object} error - Error object
 */
function showFeedbackReasonModal(errorId, feedbackType, error) {
    const safeEncode = window.ConfidenceSystem ? 
        window.ConfidenceSystem.safeBase64Encode : 
        (str) => btoa(encodeURIComponent(str).replace(/%([0-9A-F]{2})/g, (match, p1) => String.fromCharCode('0x' + p1)));
    
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
                    ${createErrorContextSection(error)}
                    ${createFeedbackReasonForm()}
                </div>
                <div class="pf-v5-c-modal-box__footer">
                    <button class="pf-v5-c-button pf-m-primary" 
                            onclick="submitFeedbackWithReason('${errorId}', '${feedbackType}', '${safeEncode(JSON.stringify(error))}')">
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

/**
 * Create error context section for feedback modal
 * @param {Object} error - Error object
 * @returns {string} - HTML string for error context
 */
function createErrorContextSection(error) {
    const escapeHtml = window.ErrorHighlighting ? 
        window.ErrorHighlighting.escapeHtml : 
        (text) => {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        };
    
    return `
        <div class="error-context pf-v5-u-mb-md">
            <div class="pf-v5-c-card pf-m-plain" style="background-color: var(--pf-v5-global--palette--black-150); padding: 1rem;">
                <h4 class="pf-v5-c-title pf-m-sm">${formatRuleType(error.type)}</h4>
                <p style="margin: 0.5rem 0;">${error.message}</p>
                ${error.text_segment ? `
                    <div class="pf-v5-c-code-block pf-m-plain">
                        <div class="pf-v5-c-code-block__content">
                            <code class="pf-v5-c-code-block__code">"${escapeHtml(error.text_segment)}"</code>
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Create feedback reason form
 * @returns {string} - HTML string for feedback reason form
 */
function createFeedbackReasonForm() {
    return `
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
    `;
}

/**
 * Submit feedback with reason from modal
 * @param {string} errorId - Error ID
 * @param {string} feedbackType - Feedback type
 * @param {string} encodedError - Base64 encoded error object
 */
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
        
        const safeDecode = window.ConfidenceSystem ? 
            window.ConfidenceSystem.safeBase64Decode : 
            (str) => decodeURIComponent(Array.prototype.map.call(atob(str), c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
        
        const errorJson = safeDecode(encodedError);
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
        // Error is logged to console - no toast message needed
    }
}

/**
 * Close feedback reason modal
 */
function closeFeedbackReasonModal() {
    if (window.currentFeedbackModal) {
        window.currentFeedbackModal.remove();
        window.currentFeedbackModal = null;
    }
}



/**
 * Generate CSS styles for feedback system
 * @returns {string} - CSS string for feedback styling
 */
function generateFeedbackStyles() {
    return `
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
        
        /* Feedback state animations */
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
    `;
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.FeedbackSystem = {
        FeedbackTracker,
        createFeedbackButtons,
        createFeedbackConfirmation,
        createFeedbackPrompt,
        submitFeedback,
        processFeedbackSubmission,
        changeFeedback,
        showFeedbackReasonModal,
        createErrorContextSection,
        createFeedbackReasonForm,
        submitFeedbackWithReason,
        closeFeedbackReasonModal,
        generateFeedbackStyles
    };
}