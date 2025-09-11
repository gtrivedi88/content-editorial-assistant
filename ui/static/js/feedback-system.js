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
        // Use stable components that don't change between analysis runs
        // Focus on the core error identity rather than positional information
        const components = [
            error.type || 'unknown',
            error.message || 'nomessage'
        ];
        
        // Add text segment if available, otherwise try other text identifiers
        let textIdentifier = 'notext';
        if (error.text_segment && error.text_segment.trim()) {
            textIdentifier = error.text_segment.trim().replace(/\s+/g, ' ').substring(0, 100);
        } else if (error.sentence && error.sentence.trim()) {
            // Use sentence if text_segment is not available
            textIdentifier = error.sentence.trim().replace(/\s+/g, ' ').substring(0, 100);
        } else if (error.suggestions && error.suggestions.length > 0) {
            // Use first suggestion as differentiator if no text available
            textIdentifier = error.suggestions[0].replace(/\s+/g, ' ').substring(0, 50);
        }
        
        components.push(textIdentifier);
        
        // Add additional differentiating factors for same-type errors
        if (error.subtype) {
            components.push(error.subtype);
        }
        
        if (error.ambiguity_type) {
            components.push(error.ambiguity_type);
        }
        
        if (error.rule_subtype) {
            components.push(error.rule_subtype);
        }
        
        // For word usage errors, extract the specific word being flagged
        if (error.type && error.type.includes('word_usage') && error.message) {
            const wordMatch = error.message.match(/'([^']+)'/);
            if (wordMatch) {
                components.push(`flagged_word:${wordMatch[1]}`);
            }
        }
        
        // Add error position if available (but only the first few digits to avoid minor variations)
        if (error.error_position && typeof error.error_position === 'number') {
            // Round to nearest 10 to avoid minor position differences
            const roundedPosition = Math.floor(error.error_position / 10) * 10;
            components.push(`pos:${roundedPosition}`);
        }
        
        // If we still have minimal differentiation, add a hash of all available properties
        if (textIdentifier === 'notext' && error.message === error.type) {
            // Create a more unique identifier from all error properties
            const allProps = JSON.stringify({
                suggestions: error.suggestions || [],
                severity: error.severity,
                confidence: error.confidence,
                confidence_score: error.confidence_score,
                // Include any other unique properties
                ...Object.keys(error).reduce((acc, key) => {
                    if (typeof error[key] === 'string' && error[key].length < 200) {
                        acc[key] = error[key];
                    }
                    return acc;
                }, {})
            });
            components.push(allProps.substring(0, 100));
        }

        // Create a more stable hash using enhanced components
        const rawId = components.join('|');

        // Use DJB2 hash algorithm for better distribution
        let hash = 5381;
        for (let i = 0; i < rawId.length; i++) {
            hash = ((hash << 5) + hash) + rawId.charCodeAt(i);
            hash = hash & hash; // Convert to 32-bit integer
        }
        
        // Convert to positive base36 string with more digits for better uniqueness
        const errorId = Math.abs(hash).toString(36).padStart(10, '0');

        return errorId;
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
        
        const feedbackData = {
            type: feedbackType, // 'helpful', 'not_helpful'
            reason: reason,
            timestamp: Date.now(),
            error_type: error.type,
            confidence_score: confidenceScore,
            // Store the complete error object for reconstruction
            original_error: {
                type: error.type,
                message: error.message,
                line_number: error.line_number,
                sentence_index: error.sentence_index,
                text_segment: error.text_segment,
                confidence_score: error.confidence_score
            }
        };

        this.feedback[errorId] = feedbackData;

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
        const feedback = this.feedback[errorId] || null;

        if (feedback) {

        }
        return feedback;
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
    const errorId = FeedbackTracker.generateErrorId(error);

    const existingFeedback = FeedbackTracker.getFeedback(error);

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

    // Prevent multiple submissions
    const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
    if (!feedbackSection) {
        console.error(`Feedback section not found for error ID: ${errorId}`);
        return;
    }

    // Check if already processing
    if (feedbackSection.dataset.processing === 'true') {

        return;
    }
    
    // Mark as processing
    feedbackSection.dataset.processing = 'true';
    
    // Disable feedback buttons - use multiple selectors to be more robust
    let buttons = Array.from(feedbackSection.querySelectorAll('.feedback-btn, .feedback-helpful, .feedback-not-helpful'));

    // Also try to find buttons in the immediate DOM area as fallback
    if (buttons.length === 0) {

        const allButtons = Array.from(feedbackSection.querySelectorAll('button'));

        allButtons.forEach(btn => {
            if (btn.textContent && (btn.textContent.includes('Helpful') || btn.textContent.includes('Not helpful'))) {
                buttons.push(btn);
            }
        });
    }
    
    buttons.forEach(btn => {
        btn.disabled = true;
        btn.style.opacity = '0.6';
    });

    try {
        // Use safe decoding with fallback
        let errorJson;
        let error;
        
        // Try confidence system first (if available)
        if (window.ConfidenceSystem && window.ConfidenceSystem.safeBase64Decode) {

            errorJson = window.ConfidenceSystem.safeBase64Decode(encodedError);
        } else {

            errorJson = decodeURIComponent(Array.prototype.map.call(atob(encodedError), c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2)).join(''));
        }

        error = JSON.parse(errorJson);

        // Validate the error object has required properties
        if (!error.type || !error.message) {
            throw new Error(`Invalid error object: missing type or message. Got: ${JSON.stringify(error)}`);
        }
        
        if (feedbackType === 'not_helpful') {

            // Show reason selection modal for negative feedback
            showFeedbackReasonModal(errorId, feedbackType, error);
        } else {

            // Direct submission for positive feedback
            processFeedbackSubmission(errorId, feedbackType, error, null);
        }
    } catch (e) {
        console.error('Failed to process feedback:', e);
        console.error('EncodedError that failed:', encodedError);
        
        // Re-enable buttons on error
        buttons.forEach(btn => {
            btn.disabled = false;
            btn.style.opacity = '1';
        });
        feedbackSection.dataset.processing = 'false';
        
        // Show user-friendly error message
        showFeedbackError(feedbackSection, 'Failed to submit feedback. Please try again.');
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

    try {
        // Record feedback

        const recordedErrorId = FeedbackTracker.recordFeedback(error, feedbackType, reason);

        // Verify feedback was recorded
        const storedFeedback = FeedbackTracker.getFeedback(error);

        // Update UI to show feedback confirmation
        const feedbackSections = document.querySelectorAll(`[data-error-id="${errorId}"]`);

        if (feedbackSections.length > 0) {
            // Update all sections with the same error ID
            feedbackSections.forEach((feedbackSection, index) => {

                updateFeedbackSection(feedbackSection, errorId, error, feedbackType, reason);
            });
            
            // Submit to backend if available (only once, not per section)
            submitFeedbackToBackend(errorId, feedbackType, error, reason);
        } else {
            console.error(`[DEBUG] No feedback sections found for errorId: ${errorId}`);
            
            // Try to find any feedback sections for debugging
            const allFeedbackSections = document.querySelectorAll('[data-error-id]');

        }
    } catch (e) {
        console.error('Error processing feedback submission:', e);
        console.error('Error object that failed:', error);
        
        const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
        if (feedbackSection) {
            feedbackSection.dataset.processing = 'false';
            showFeedbackError(feedbackSection, 'Failed to save feedback. Please try again.');
        }
    }
}

/**
 * Update a single feedback section
 * @param {Element} feedbackSection - The feedback section element
 * @param {string} errorId - Error ID
 * @param {Object} error - Error object
 * @param {string} feedbackType - Feedback type
 * @param {Object|null} reason - Reason object
 */
function updateFeedbackSection(feedbackSection, errorId, error, feedbackType, reason) {
    try {
        if (feedbackSection) {

            // Remove processing state
            feedbackSection.dataset.processing = 'false';
            
            // Update with confirmation - this should now show the Change button

            const newHtml = createFeedbackButtons(error);

            // Force a small delay to ensure DOM is ready
            setTimeout(() => {
                feedbackSection.innerHTML = newHtml;

                // Verify the update actually happened
                const hasChangeButton = feedbackSection.querySelector('.feedback-change-btn');

                // Add success animation
                feedbackSection.style.transition = 'all 0.3s ease';
                feedbackSection.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    feedbackSection.style.transform = 'scale(1)';
                }, 200);
            }, 50);
        }
    } catch (e) {
        console.error('Error updating feedback section:', e);
        feedbackSection.dataset.processing = 'false';
    }
}

/**
 * Change existing feedback
 * @param {string} errorId - Error ID
 */
function changeFeedback(errorId) {

    const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
    if (!feedbackSection) {
        console.error(`Feedback section not found for error ID: ${errorId}`);
        return;
    }

    // Get existing feedback data - use direct access first, then try to find by error object
    let existingFeedback = FeedbackTracker.feedback[errorId];

    if (!existingFeedback) {
        // Fallback: search through all stored feedback to find matching errorId

        // Find any feedback with matching errorId in the keys
        const feedbackKeys = Object.keys(FeedbackTracker.feedback);
        existingFeedback = feedbackKeys.includes(errorId) ? FeedbackTracker.feedback[errorId] : null;
        
        if (!existingFeedback) {
            console.error(`No existing feedback found for error ID: ${errorId}`);
            console.error(`Available feedback keys:`, feedbackKeys);
            return;
        }
    }

    // Disable change button to prevent multiple clicks
    const changeBtn = feedbackSection.querySelector('.feedback-change-btn');
    if (changeBtn) {
        changeBtn.disabled = true;
        changeBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Changing...';
    }
    
    try {
        // Remove existing feedback
        delete FeedbackTracker.feedback[errorId];
        FeedbackTracker.saveToSession();
        
        // Reconstruct error object from stored data
        const reconstructedError = existingFeedback.original_error || {
            type: existingFeedback.error_type,
            message: existingFeedback.original_error?.message || 'Error message not available',
            text_segment: existingFeedback.original_error?.text_segment || '',
            confidence_score: existingFeedback.confidence_score
        };
        
        // Show fresh feedback buttons with animation
        const newHtml = createFeedbackPrompt(errorId, reconstructedError);
        feedbackSection.innerHTML = newHtml;
        
        // Add fade-in animation
        feedbackSection.style.opacity = '0';
        requestAnimationFrame(() => {
            feedbackSection.style.transition = 'opacity 0.3s ease';
            feedbackSection.style.opacity = '1';
        });
        
    } catch (error) {
        console.error('Error changing feedback:', error);
        // Restore the change button if there was an error
        if (changeBtn) {
            changeBtn.disabled = false;
            changeBtn.innerHTML = '<i class="fas fa-edit"></i> Change';
        }
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
    
    // Handle Escape key to close modal
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            closeFeedbackReasonModal();
        }
    };
    document.addEventListener('keydown', handleEscape);
    
    // Store the escape handler for cleanup
    modal.escapeHandler = handleEscape;
    
    document.body.appendChild(modal);
    window.currentFeedbackModal = modal;
    
    // Store error ID for cleanup when modal is closed
    modal.setAttribute('data-error-id', errorId);
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
        if (!form) {
            console.error('Feedback reason form not found');
            return;
        }
        
        const selectedReason = form.querySelector('input[name="feedback-reason"]:checked');
        const comment = form.querySelector('#feedback-comment').value.trim();
        
        if (!selectedReason) {
            // Highlight the fieldset to show error
            const fieldset = form.querySelector('fieldset');
            if (fieldset) {
                fieldset.style.border = '2px solid var(--app-danger-color)';
                fieldset.style.borderRadius = '4px';
                setTimeout(() => {
                    fieldset.style.border = '';
                    fieldset.style.borderRadius = '';
                }, 3000);
            }
            return;
        }
        
        // Disable submit button to prevent double submission
        const submitBtn = form.closest('.feedback-reason-modal').querySelector('.pf-v5-c-button.pf-m-primary');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
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
        
        // Close modal first (this will also reset processing state)
        closeFeedbackReasonModal();
        
        // Process feedback
        processFeedbackSubmission(errorId, feedbackType, error, reason);
        
    } catch (e) {
        console.error('Failed to submit feedback with reason:', e);
        
        // Re-enable submit button if there was an error
        const submitBtn = document.querySelector('.feedback-reason-modal .pf-v5-c-button.pf-m-primary');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Submit Feedback';
        }
        
        // Show error in modal if it's still open
        const modal = document.querySelector('.feedback-reason-modal-backdrop');
        if (modal) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'pf-v5-c-alert pf-m-danger pf-m-inline';
            errorDiv.innerHTML = `
                <div class="pf-v5-c-alert__icon">
                    <i class="fas fa-exclamation-circle"></i>
                </div>
                <div class="pf-v5-c-alert__title">
                    Failed to submit feedback. Please try again.
                </div>
            `;
            
            const modalBody = modal.querySelector('.pf-v5-c-modal-box__body');
            if (modalBody) {
                modalBody.insertBefore(errorDiv, modalBody.firstChild);
            }
        }
    }
}

/**
 * Close feedback reason modal
 */
function closeFeedbackReasonModal() {
    if (window.currentFeedbackModal) {
        // Get the error ID from the modal to reset processing state
        const errorId = window.currentFeedbackModal.getAttribute('data-error-id');
        
        // Reset processing state for the feedback section
        if (errorId) {
            const feedbackSection = document.querySelector(`[data-error-id="${errorId}"]`);
            if (feedbackSection) {
                feedbackSection.dataset.processing = 'false';
                
                // Re-enable feedback buttons
                const buttons = feedbackSection.querySelectorAll('.feedback-btn');
                buttons.forEach(btn => {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                });
            }
        }
        
        // Clean up escape key listener
        if (window.currentFeedbackModal.escapeHandler) {
            document.removeEventListener('keydown', window.currentFeedbackModal.escapeHandler);
        }
        
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

/**
 * Submit feedback to backend API
 * @param {string} errorId - Error ID
 * @param {string} feedbackType - Feedback type
 * @param {Object} error - Error object
 * @param {Object|null} reason - Reason object
 */
function submitFeedbackToBackend(errorId, feedbackType, error, reason) {
    // Generate session ID if not available
    const sessionId = window.currentSessionId || generateSessionId();
    
    const feedbackData = {
        session_id: sessionId,
        error_id: errorId,
        error_type: error.type,
        error_message: error.message,
        feedback_type: feedbackType === 'helpful' ? 'correct' : 'incorrect',
        confidence_score: error.confidence_score || 0.5,
        user_reason: reason ? JSON.stringify(reason) : null
    };
    
    fetch('/api/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(feedbackData)
    }).catch(error => {
        console.warn('Failed to submit feedback to backend:', error);
        // Don't fail the UI operation for backend errors
    });
}

/**
 * Generate a session ID if one doesn't exist
 * @returns {string} - Session ID
 */
function generateSessionId() {
    if (!window.currentSessionId) {
        window.currentSessionId = 'sess_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    return window.currentSessionId;
}

/**
 * Show feedback error message
 * @param {Element} feedbackSection - Feedback section element
 * @param {string} message - Error message
 */
function showFeedbackError(feedbackSection, message) {
    const errorHtml = `
        <div class="pf-v5-c-alert pf-m-danger pf-m-inline" style="margin-top: 0.5rem;">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-exclamation-circle"></i>
            </div>
            <div class="pf-v5-c-alert__title">
                ${message}
            </div>
        </div>
    `;
    
    feedbackSection.insertAdjacentHTML('afterend', errorHtml);
    
    // Remove error message after 5 seconds
    setTimeout(() => {
        const errorAlert = feedbackSection.nextElementSibling;
        if (errorAlert && errorAlert.classList.contains('pf-v5-c-alert')) {
            errorAlert.remove();
        }
    }, 5000);
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
        generateFeedbackStyles,
        submitFeedbackToBackend,
        generateSessionId,
        showFeedbackError
    };
    
    // Initialize feedback system when the script loads
    console.log('[DEBUG] Initializing FeedbackTracker...');
    FeedbackTracker.init();
}