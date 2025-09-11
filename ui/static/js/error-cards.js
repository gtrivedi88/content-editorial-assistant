/**
 * Error Cards Module
 * Handles error card generation, layout, interactive elements, and expandable sections
 */

/**
 * Create enhanced error card for error summaries with confidence indicators
 * @param {Object} error - Error object containing type, message, suggestions, etc.
 * @param {number} index - Index of the error for unique identification
 * @returns {string} - HTML string for error card
 */
function createErrorCard(error, index) {
    // Get styling information
    const typeStyle = window.ErrorStyling ? 
        window.ErrorStyling.getErrorTypeStyle(error.type) : 
        { color: 'var(--app-danger-color)', icon: 'fas fa-exclamation-circle' };
    
    const suggestions = Array.isArray(error.suggestions) ? error.suggestions : [];
    
    // Get confidence information
    const confidenceScore = window.ConfidenceSystem ? 
        window.ConfidenceSystem.extractConfidenceScore(error) : 
        (error.confidence_score || 0.5);
    
    const confidenceLevel = window.ConfidenceSystem ? 
        window.ConfidenceSystem.getConfidenceLevel(confidenceScore) : 
        (confidenceScore >= 0.7 ? 'HIGH' : confidenceScore >= 0.5 ? 'MEDIUM' : 'LOW');
    
    // Apply confidence-based styling
    let cardOpacity = '';
    if (confidenceLevel === 'LOW') {
        cardOpacity = 'opacity: 0.85;';
    }
    
    // Create confidence badge
    const confidenceBadge = window.ConfidenceSystem ? 
        window.ConfidenceSystem.createConfidenceBadge(confidenceScore) : 
        `<span class="pf-v5-c-label pf-m-compact">${Math.round(confidenceScore * 100)}%</span>`;
    
    return `
        <div class="pf-v5-c-card pf-m-compact app-card enhanced-error-card" 
             style="border-left: 4px ${confidenceLevel === 'LOW' ? 'dashed' : 'solid'} ${typeStyle.color}; ${cardOpacity}"
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
                        ${confidenceBadge}
                    </div>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <p class="pf-v5-u-mb-sm">${error.message}</p>
                
                ${error.text_segment ? createTextSegmentSection(error.text_segment) : ''}
                ${createConfidenceAnalysisSection(error, index)}
                ${createConsolidationSection(error)}
                ${createFixOptionsSection(error, index, suggestions)}
                ${createErrorMetadataSection(error)}
                ${createCardFeedbackSection(error)}
            </div>
        </div>
    `;
}

/**
 * Create text segment display section
 * @param {string} textSegment - The text segment to display
 * @returns {string} - HTML string for text segment section
 */
function createTextSegmentSection(textSegment) {
    return `
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
                    <code class="pf-v5-c-code-block__code">${escapeHtml(textSegment)}</code>
                </pre>
            </div>
        </div>
    `;
}

/**
 * Create confidence analysis expandable section
 * @param {Object} error - Error object
 * @param {number} index - Error index for unique identification
 * @returns {string} - HTML string for confidence analysis section
 */
function createConfidenceAnalysisSection(error, index) {
    // Always show confidence analysis section since createConfidenceTooltip handles all error types
    
    const confidenceTooltip = window.ConfidenceSystem ? 
        window.ConfidenceSystem.createConfidenceTooltip(error) : 
        '<div>Confidence details not available</div>';
    
    return `
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
                    ${confidenceTooltip}
                </div>
            </div>
        </div>
    `;
}

/**
 * Create consolidation information section
 * @param {Object} error - Error object
 * @returns {string} - HTML string for consolidation section
 */
function createConsolidationSection(error) {
    if (!error.consolidated_from || error.consolidated_from.length <= 1) {
        return '';
    }
    
    return `
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
    `;
}

/**
 * Create fix options or suggestions section
 * @param {Object} error - Error object
 * @param {number} index - Error index for unique identification
 * @param {Array} suggestions - Array of suggestions
 * @returns {string} - HTML string for fix options section
 */
function createFixOptionsSection(error, index, suggestions) {
    if (error.fix_options && error.fix_options.length > 1) {
        return createAdvancedFixOptions(error.fix_options, index);
    } else if (suggestions.length > 0) {
        return createSimpleSuggestions(suggestions);
    }
    return '';
}

/**
 * Create advanced fix options with expandable sections
 * @param {Array} fixOptions - Array of fix option objects
 * @param {number} index - Error index for unique identification
 * @returns {string} - HTML string for advanced fix options
 */
function createAdvancedFixOptions(fixOptions, index) {
    return `
        <div class="pf-v5-u-mt-md">
            <h4 class="pf-v5-c-title pf-m-sm pf-v5-u-mb-sm">
                <i class="fas fa-tools pf-v5-u-mr-xs"></i>
                Fix Options
            </h4>
            ${fixOptions.map((option, optionIndex) => `
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
    `;
}

/**
 * Create simple suggestions list
 * @param {Array} suggestions - Array of suggestion strings
 * @returns {string} - HTML string for suggestions
 */
function createSimpleSuggestions(suggestions) {
    return `
        <div class="pf-v5-u-mt-md">
            <h4 class="pf-v5-c-title pf-m-sm pf-v5-u-mb-sm">
                <i class="fas fa-lightbulb pf-v5-u-mr-xs"></i>
                Suggestions
            </h4>
            <ul class="pf-v5-c-list">
                ${suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
            </ul>
        </div>
    `;
}

/**
 * Create error metadata section with line numbers and sentence indices
 * @param {Object} error - Error object
 * @returns {string} - HTML string for metadata section
 */
function createErrorMetadataSection(error) {
    return `
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
    `;
}

/**
 * Create feedback section for error cards
 * @param {Object} error - Error object
 * @returns {string} - HTML string for feedback section
 */
function createCardFeedbackSection(error) {
    const feedbackButtons = window.FeedbackSystem ? 
        window.FeedbackSystem.createFeedbackButtons(error, 'card') : 
        '';
    
    return `
        <div class="pf-v5-u-mt-md pf-v5-u-pt-sm" style="border-top: 1px solid var(--pf-v5-global--BorderColor--300);">
            ${feedbackButtons}
        </div>
    `;
}

/**
 * Toggle fix option expandable section
 * @param {number} errorIndex - Index of the error
 * @param {number} optionIndex - Index of the fix option
 */
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

/**
 * Toggle confidence analysis section
 * @param {number} errorIndex - Index of the error
 */
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

/**
 * Generate CSS styles for error cards
 * @returns {string} - CSS string for error card styling
 */
function generateErrorCardStyles() {
    return `
        .enhanced-error-card {
            margin-bottom: 1.5rem;
            transition: box-shadow 0.2s ease;
        }
        
        .enhanced-error-card:hover {
            box-shadow: var(--pf-v5-global--BoxShadow--md);
        }
        
        .enhanced-error-card .pf-v5-c-card__header {
            padding-bottom: 0.5rem;
        }
        
        .enhanced-error-card .pf-v5-c-card__title h3 {
            margin: 0;
            display: flex;
            align-items: center;
        }
        
        .enhanced-error-card .confidence-indicators {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .enhanced-error-card .pf-v5-c-expandable-section__toggle {
            width: 100%;
            text-align: left;
            background: none;
            border: none;
            padding: 0.5rem;
            border-radius: var(--pf-v5-global--BorderRadius--sm);
            transition: background-color 0.2s ease;
        }
        
        .enhanced-error-card .pf-v5-c-expandable-section__toggle:hover {
            background-color: var(--pf-v5-global--palette--black-150);
        }
        
        .enhanced-error-card .pf-v5-c-expandable-section__toggle-icon i {
            transition: transform 0.2s ease;
        }
        
        .enhanced-error-card .pf-m-expanded .pf-v5-c-expandable-section__toggle-icon i {
            transform: rotate(90deg);
        }
        
        .error-card-metadata {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
        }
    `;
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.ErrorCards = {
        createErrorCard,
        createTextSegmentSection,
        createConfidenceAnalysisSection,
        createConsolidationSection,
        createFixOptionsSection,
        createAdvancedFixOptions,
        createSimpleSuggestions,
        createErrorMetadataSection,
        createCardFeedbackSection,
        toggleFixOption,
        toggleConfidenceSection,
        generateErrorCardStyles
    };
}