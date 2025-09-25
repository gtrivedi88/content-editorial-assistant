/**
 * Metadata Feedback Integration
 * Connects with existing UserFeedback system, database models, and reliability tuner
 * Provides feedback collection for continuous learning
 */

/**
 * Record metadata-specific feedback using existing feedback system
 * Integrates with existing UserFeedback model and reliability tuner
 */
async function recordMetadataFeedback(feedbackType, component, originalValue, newValue, context = {}) {
    const feedbackData = {
        error_type: 'metadata_assistant',
        error_message: `Metadata ${component} ${feedbackType}`,
        feedback_type: feedbackType, // 'correct', 'incorrect', 'partially_correct'
        confidence_score: calculateFeedbackConfidence(feedbackType, context),
        user_reason: formatUserReason(feedbackType, component, originalValue, newValue),
        violation_id: generateMetadataViolationId(component),
        session_id: getCurrentSessionId()
    };
    
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(feedbackData)
        });
        
        const result = await response.json();
        if (result.success) {
            console.log('✅ Metadata feedback recorded:', result.feedback_id);
            
            // This feedback will be processed by existing reliability tuner
            // for continuous learning and model improvement
            
            // Update monitoring metrics using existing system
            updateValidationMetrics('metadata_feedback', 'success');
            
            return result.feedback_id;
        } else {
            console.error('❌ Failed to record metadata feedback:', result.error);
            return null;
        }
    } catch (error) {
        console.error('❌ Failed to record metadata feedback:', error);
        return null;
    }
}

/**
 * Record thumbs up/down feedback for generated metadata
 */
async function recordMetadataRating(rating, metadataComponent = null) {
    const feedbackType = rating === 'up' ? 'correct' : 'incorrect';
    const component = metadataComponent || 'overall';
    
    return await recordMetadataFeedback(
        feedbackType,
        component,
        'generated_metadata',
        rating === 'up' ? 'approved' : 'rejected',
        { rating: rating, component: component }
    );
}

/**
 * Record user correction feedback (when user edits metadata)
 */
async function recordMetadataCorrection(component, originalValue, correctedValue, reason = 'user_correction') {
    return await recordMetadataFeedback(
        'incorrect', // Original was incorrect, user provided correction
        component,
        originalValue,
        correctedValue,
        { correction_reason: reason }
    );
}

/**
 * Record keyword addition feedback
 */
async function recordKeywordAddition(addedKeyword, context = {}) {
    return await recordMetadataFeedback(
        'partially_correct', // Existing keywords were okay, but missing this one
        'keywords',
        'missing_keyword',
        addedKeyword,
        { action: 'keyword_added', ...context }
    );
}

/**
 * Record keyword removal feedback
 */
async function recordKeywordRemoval(removedKeyword, context = {}) {
    return await recordMetadataFeedback(
        'incorrect', // This keyword was incorrectly suggested
        'keywords',
        removedKeyword,
        'keyword_removed',
        { action: 'keyword_removed', ...context }
    );
}

/**
 * Record taxonomy classification feedback
 */
async function recordTaxonomyFeedback(action, taxonomyTag, context = {}) {
    const feedbackType = action === 'added' ? 'partially_correct' : 'incorrect';
    
    return await recordMetadataFeedback(
        feedbackType,
        'taxonomy',
        action === 'added' ? 'missing_category' : taxonomyTag,
        action === 'added' ? taxonomyTag : 'category_removed',
        { action: `taxonomy_${action}`, ...context }
    );
}

/**
 * Create feedback UI components for metadata sections
 */
function createMetadataFeedbackUI(sectionId, component) {
    const section = document.getElementById(sectionId);
    if (!section) return;
    
    // Check if feedback UI already exists
    if (section.querySelector('.metadata-feedback-ui')) return;
    
    const feedbackUI = document.createElement('div');
    feedbackUI.className = 'metadata-feedback-ui pf-v5-u-mt-sm';
    feedbackUI.innerHTML = `
        <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-align-items-center">
            <span class="pf-v5-c-content">
                <small>Is this ${component} helpful?</small>
            </span>
            <button class="pf-v5-c-button pf-m-plain pf-m-small" 
                    onclick="submitMetadataThumbsFeedback('${component}', 'up')"
                    title="Thumbs up - this ${component} is helpful">
                <i class="fas fa-thumbs-up"></i>
            </button>
            <button class="pf-v5-c-button pf-m-plain pf-m-small" 
                    onclick="submitMetadataThumbsFeedback('${component}', 'down')"
                    title="Thumbs down - this ${component} needs improvement">
                <i class="fas fa-thumbs-down"></i>
            </button>
        </div>
    `;
    
    // Add to the section
    const cardBody = section.querySelector('.pf-v5-c-card__body');
    if (cardBody) {
        cardBody.appendChild(feedbackUI);
    } else {
        section.appendChild(feedbackUI);
    }
}

/**
 * Initialize feedback UI for all metadata components
 */
function initializeMetadataFeedbackUI() {
    const metadataSection = document.getElementById('metadata-section');
    if (!metadataSection) return;
    
    // Add overall feedback to the main card footer
    addOverallMetadataFeedback();
    
    // Add specific component feedback
    setTimeout(() => {
        createMetadataFeedbackUI('metadata-section', 'generated metadata');
    }, 1000); // Delay to ensure DOM is ready
}

/**
 * Add overall feedback to metadata section footer
 */
function addOverallMetadataFeedback() {
    const metadataSection = document.getElementById('metadata-section');
    if (!metadataSection) return;
    
    const footer = metadataSection.querySelector('.pf-v5-c-card__footer');
    if (!footer) return;
    
    // Check if feedback already exists
    if (footer.querySelector('.overall-feedback-ui')) return;
    
    const feedbackUI = document.createElement('div');
    feedbackUI.className = 'overall-feedback-ui pf-v5-u-ml-auto';
    feedbackUI.innerHTML = `
        <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-align-items-center">
            <span class="pf-v5-c-content">
                <small class="pf-v5-u-color-200">Rate this metadata:</small>
            </span>
            <div class="pf-v5-c-button-group" role="group">
                <button class="pf-v5-c-button pf-m-tertiary pf-m-small" 
                        onclick="submitMetadataThumbsFeedback('overall', 'up')"
                        title="This metadata is helpful and accurate">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <button class="pf-v5-c-button pf-m-tertiary pf-m-small" 
                        onclick="submitMetadataThumbsFeedback('overall', 'down')"
                        title="This metadata needs improvement">
                    <i class="fas fa-thumbs-down"></i>
                </button>
            </div>
        </div>
    `;
    
    const flexContainer = footer.querySelector('.pf-v5-l-flex');
    if (flexContainer) {
        flexContainer.appendChild(feedbackUI);
    }
}

/**
 * Submit thumbs up/down feedback
 */
async function submitMetadataThumbsFeedback(component, rating) {
    const button = event.target.closest('button');
    if (!button) return;
    
    // Disable button during submission
    button.disabled = true;
    
    try {
        const feedbackId = await recordMetadataRating(rating, component);
        
        if (feedbackId) {
            // Show success feedback
            showFeedbackSuccess(button, rating);
            
            // Update button state
            updateFeedbackButtonState(button, rating, true);
            
            // Show thank you message
            showFeedbackThankYou(component, rating);
        } else {
            // Show error
            showFeedbackError(button);
        }
    } catch (error) {
        console.error('Failed to submit feedback:', error);
        showFeedbackError(button);
    }
    
    // Re-enable button after a delay
    setTimeout(() => {
        button.disabled = false;
    }, 2000);
}

/**
 * Show feedback success animation
 */
function showFeedbackSuccess(button, rating) {
    const icon = button.querySelector('i');
    const originalClass = icon.className;
    
    // Temporarily show checkmark
    icon.className = 'fas fa-check';
    button.classList.add('pf-m-primary');
    
    setTimeout(() => {
        icon.className = originalClass;
        button.classList.remove('pf-m-primary');
        button.classList.add(rating === 'up' ? 'pf-m-success' : 'pf-m-warning');
    }, 1000);
}

/**
 * Show feedback error
 */
function showFeedbackError(button) {
    const icon = button.querySelector('i');
    const originalClass = icon.className;
    
    // Temporarily show error
    icon.className = 'fas fa-exclamation-triangle';
    button.classList.add('pf-m-danger');
    
    setTimeout(() => {
        icon.className = originalClass;
        button.classList.remove('pf-m-danger');
    }, 2000);
}

/**
 * Update feedback button state
 */
function updateFeedbackButtonState(button, rating, submitted) {
    const buttonGroup = button.closest('.pf-v5-c-button-group');
    if (!buttonGroup) return;
    
    const allButtons = buttonGroup.querySelectorAll('button');
    allButtons.forEach(btn => {
        btn.classList.remove('pf-m-success', 'pf-m-warning', 'pf-m-primary');
    });
    
    if (submitted) {
        button.classList.add(rating === 'up' ? 'pf-m-success' : 'pf-m-warning');
    }
}

/**
 * Show thank you message
 */
function showFeedbackThankYou(component, rating) {
    const message = rating === 'up' ? 
        `Thank you! Your positive feedback helps improve our ${component} generation.` :
        `Thank you for your feedback! We'll use this to improve our ${component} generation.`;
    
    if (typeof showNotification === 'function') {
        showNotification(message, 'success');
    } else {
        console.log('👍 ' + message);
    }
}

/**
 * Format user reason for feedback
 */
function formatUserReason(feedbackType, component, originalValue, newValue) {
    const actions = {
        'correct': 'approved',
        'incorrect': 'rejected', 
        'partially_correct': 'modified'
    };
    
    const action = actions[feedbackType] || feedbackType;
    
    return `User ${action} ${component}: "${originalValue}" → "${newValue}"`;
}

/**
 * Calculate feedback confidence based on context
 */
function calculateFeedbackConfidence(feedbackType, context) {
    let baseConfidence = 0.8;
    
    // Adjust based on feedback type
    switch (feedbackType) {
        case 'correct':
            baseConfidence = 0.9;
            break;
        case 'incorrect':
            baseConfidence = 0.85;
            break;
        case 'partially_correct':
            baseConfidence = 0.75;
            break;
    }
    
    // Adjust based on context
    if (context.rating === 'up') {
        baseConfidence += 0.1;
    } else if (context.rating === 'down') {
        baseConfidence -= 0.1;
    }
    
    return Math.max(0.1, Math.min(1.0, baseConfidence));
}

/**
 * Generate unique violation ID for metadata feedback
 */
function generateMetadataViolationId(component) {
    const timestamp = Date.now();
    const random = Math.floor(Math.random() * 1000);
    return `metadata_${component}_${timestamp}_${random}`;
}

/**
 * Get current session ID
 */
function getCurrentSessionId() {
    return window.currentSessionId || 
           window.sessionId || 
           document.querySelector('[data-session-id]')?.getAttribute('data-session-id') ||
           'metadata_session_' + Date.now();
}

/**
 * Update validation metrics (integrate with existing system)
 */
function updateValidationMetrics(metric, status) {
    try {
        if (window.ValidationMetrics && window.ValidationMetrics.record_pipeline_execution) {
            window.ValidationMetrics.record_pipeline_execution(metric, status);
        }
    } catch (error) {
        console.warn('Could not update validation metrics:', error);
    }
}

/**
 * Collect detailed feedback via modal
 */
function showDetailedFeedbackModal(component, currentValue) {
    const modal = document.createElement('div');
    modal.className = 'pf-v5-c-backdrop';
    modal.innerHTML = `
        <div class="pf-v5-l-bullseye">
            <div class="pf-v5-c-modal-box pf-m-md">
                <header class="pf-v5-c-modal-box__header">
                    <h1 class="pf-v5-c-modal-box__title">
                        <i class="fas fa-comment pf-v5-u-mr-sm"></i>
                        Improve ${capitalizeFirst(component)}
                    </h1>
                </header>
                <div class="pf-v5-c-modal-box__body">
                    <div class="pf-v5-c-form">
                        <div class="pf-v5-c-form__group">
                            <div class="pf-v5-c-form__group-label">
                                <label class="pf-v5-c-form__label">
                                    <span class="pf-v5-c-form__label-text">Current ${component}:</span>
                                </label>
                            </div>
                            <div class="pf-v5-c-form__group-control">
                                <div class="pf-v5-c-form-control pf-m-readonly">
                                    ${escapeHtml(currentValue)}
                                </div>
                            </div>
                        </div>
                        
                        <div class="pf-v5-c-form__group">
                            <div class="pf-v5-c-form__group-label">
                                <label class="pf-v5-c-form__label" for="feedback-suggestion">
                                    <span class="pf-v5-c-form__label-text">Your suggestion:</span>
                                </label>
                            </div>
                            <div class="pf-v5-c-form__group-control">
                                <textarea class="pf-v5-c-form-control" id="feedback-suggestion" rows="3"
                                          placeholder="How would you improve this ${component}?"></textarea>
                            </div>
                        </div>
                        
                        <div class="pf-v5-c-form__group">
                            <div class="pf-v5-c-form__group-label">
                                <label class="pf-v5-c-form__label">
                                    <span class="pf-v5-c-form__label-text">Issue type:</span>
                                </label>
                            </div>
                            <div class="pf-v5-c-form__group-control">
                                <div class="pf-v5-c-radio">
                                    <input class="pf-v5-c-radio__input" type="radio" name="issue-type" value="inaccurate" id="issue-inaccurate" checked>
                                    <label class="pf-v5-c-radio__label" for="issue-inaccurate">Inaccurate</label>
                                </div>
                                <div class="pf-v5-c-radio">
                                    <input class="pf-v5-c-radio__input" type="radio" name="issue-type" value="incomplete" id="issue-incomplete">
                                    <label class="pf-v5-c-radio__label" for="issue-incomplete">Incomplete</label>
                                </div>
                                <div class="pf-v5-c-radio">
                                    <input class="pf-v5-c-radio__input" type="radio" name="issue-type" value="irrelevant" id="issue-irrelevant">
                                    <label class="pf-v5-c-radio__label" for="issue-irrelevant">Irrelevant</label>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                <footer class="pf-v5-c-modal-box__footer">
                    <button class="pf-v5-c-button pf-m-primary" onclick="submitDetailedFeedback('${component}')">
                        Submit Feedback
                    </button>
                    <button class="pf-v5-c-button pf-m-secondary" onclick="closeDetailedFeedbackModal()">
                        Cancel
                    </button>
                </footer>
            </div>
        </div>
    `;
    
    modal.id = 'detailed-feedback-modal';
    document.body.appendChild(modal);
}

/**
 * Submit detailed feedback from modal
 */
async function submitDetailedFeedback(component) {
    const suggestion = document.getElementById('feedback-suggestion')?.value;
    const issueType = document.querySelector('input[name="issue-type"]:checked')?.value;
    
    if (suggestion || issueType) {
        await recordMetadataFeedback(
            'incorrect',
            component,
            'detailed_feedback',
            suggestion || 'No specific suggestion',
            { issue_type: issueType, detailed_feedback: true }
        );
        
        showFeedbackThankYou(component, 'detailed');
    }
    
    closeDetailedFeedbackModal();
}

/**
 * Close detailed feedback modal
 */
function closeDetailedFeedbackModal() {
    const modal = document.getElementById('detailed-feedback-modal');
    if (modal) {
        modal.remove();
    }
}

/**
 * Initialize metadata feedback system
 */
function initializeMetadataFeedbackSystem() {
    // Wait for metadata section to be rendered
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.id === 'metadata-section') {
                    initializeMetadataFeedbackUI();
                }
            });
        });
    });
    
    observer.observe(document.body, { childList: true, subtree: true });
    
    // Also check if already exists
    if (document.getElementById('metadata-section')) {
        initializeMetadataFeedbackUI();
    }
}

/**
 * Utility function to capitalize first letter
 */
function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * Utility function to escape HTML
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeMetadataFeedbackSystem);
} else {
    initializeMetadataFeedbackSystem();
}

// Export functions for global access
window.recordMetadataFeedback = recordMetadataFeedback;
window.recordMetadataRating = recordMetadataRating;
window.recordMetadataCorrection = recordMetadataCorrection;
window.recordKeywordAddition = recordKeywordAddition;
window.recordKeywordRemoval = recordKeywordRemoval;
window.recordTaxonomyFeedback = recordTaxonomyFeedback;
window.submitMetadataThumbsFeedback = submitMetadataThumbsFeedback;
window.showDetailedFeedbackModal = showDetailedFeedbackModal;
window.submitDetailedFeedback = submitDetailedFeedback;
window.closeDetailedFeedbackModal = closeDetailedFeedbackModal;
