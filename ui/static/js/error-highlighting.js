/**
 * Error Highlighting Module
 * Handles content highlighting, error summaries, content processing, and HTML safety utilities
 */

/**
 * HTML escape utility function for safety
 * @param {string} text - Text to escape
 * @returns {string} - HTML-escaped text
 */
function escapeHtml(text) {
    if (!text) return '';
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Create highlighted text for errors in content
 * @param {string} content - Original content to highlight
 * @param {Array} errors - Array of error objects with position and text_segment
 * @returns {string} - HTML string with highlighted errors
 */
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
        
        // Get color from ErrorStyling module if available
        const color = window.ErrorStyling ? 
            window.ErrorStyling.getHighlightColor(errorType) : 
            getDefaultHighlightColor(errorType);
        
        const highlightedSegment = `<mark style="background-color: ${color}20; border-bottom: 2px solid ${color}; padding: 2px 4px; border-radius: 3px;">${segment}</mark>`;
        
        highlightedContent = highlightedContent.replace(segment, highlightedSegment);
    });
    
    return highlightedContent;
}

/**
 * Default highlight color mapping when ErrorStyling module is not available
 * @param {string} errorType - Type of error
 * @returns {string} - CSS color value
 */
function getDefaultHighlightColor(errorType) {
    const colorMap = {
        'STYLE': '#dc3545',
        'GRAMMAR': '#fd7e14', 
        'STRUCTURE': '#0066cc',
        'PUNCTUATION': '#6b21a8',
        'CAPITALIZATION': '#28a745',
        'TERMINOLOGY': '#c2410c',
        'PASSIVE_VOICE': '#fd7e14',
        'READABILITY': '#0e7490'
    };
    
    return colorMap[errorType] || colorMap['STYLE'];
}

/**
 * Enhanced error summary display with grouping and expandable sections
 * @param {Array} errors - Array of error objects
 * @returns {string} - HTML string for error summary
 */
function createErrorSummary(errors) {
    if (!errors || errors.length === 0) {
        return createNoErrorsMessage();
    }
    
    // Group errors by type
    const errorsByType = groupErrorsByType(errors);
    const errorTypeOrder = [
        'STYLE', 'GRAMMAR', 'STRUCTURE', 'PUNCTUATION', 
        'TERMINOLOGY', 'PASSIVE_VOICE', 'READABILITY'
    ];
    
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
                        .map(type => createErrorTypeSection(type, errorsByType[type]))
                        .join('')}
                </div>
            </div>
        </div>
    `;
}

/**
 * Create "no errors" message
 * @returns {string} - HTML string for no errors state
 */
function createNoErrorsMessage() {
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

/**
 * Group errors by their type
 * @param {Array} errors - Array of error objects
 * @returns {Object} - Object with error types as keys and arrays of errors as values
 */
function groupErrorsByType(errors) {
    return errors.reduce((acc, error) => {
        const type = error.error_type || 'STYLE';
        if (!acc[type]) acc[type] = [];
        acc[type].push(error);
        return acc;
    }, {});
}

/**
 * Create an expandable section for a specific error type
 * @param {string} type - Error type
 * @param {Array} typeErrors - Array of errors for this type
 * @returns {string} - HTML string for error type section
 */
function createErrorTypeSection(type, typeErrors) {
    const isExpanded = typeErrors.length <= 3;
    
    return `
        <div class="pf-v5-l-stack__item">
            <div class="pf-v5-c-expandable-section" ${isExpanded ? 'aria-expanded="true"' : ''}>
                <button type="button" class="pf-v5-c-expandable-section__toggle" 
                        aria-expanded="${isExpanded}"
                        onclick="toggleErrorTypeSection(this)">
                    <span class="pf-v5-c-expandable-section__toggle-icon">
                        <i class="fas fa-angle-right" aria-hidden="true" 
                           style="transform: ${isExpanded ? 'rotate(90deg)' : 'rotate(0deg)'}"></i>
                    </span>
                    <span class="pf-v5-c-expandable-section__toggle-text">
                        ${formatRuleType(type)} Issues (${typeErrors.length})
                    </span>
                </button>
                <div class="pf-v5-c-expandable-section__content" ${!isExpanded ? 'style="display: none;"' : ''}>
                    <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-mt-md">
                        ${typeErrors.map((error, index) => `
                            <div class="pf-v5-l-stack__item">
                                ${window.ErrorCards ? window.ErrorCards.createErrorCard(error, index) : createBasicErrorCard(error)}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Toggle error type section (fallback if not handled by other modules)
 * @param {HTMLElement} button - The toggle button element
 */
function toggleErrorTypeSection(button) {
    const section = button.closest('.pf-v5-c-expandable-section');
    const content = section.querySelector('.pf-v5-c-expandable-section__content');
    const icon = section.querySelector('.pf-v5-c-expandable-section__toggle-icon i');
    const isExpanded = section.getAttribute('aria-expanded') === 'true';
    
    if (isExpanded) {
        // Collapse
        content.style.display = 'none';
        section.setAttribute('aria-expanded', 'false');
        button.setAttribute('aria-expanded', 'false');
        icon.style.transform = 'rotate(0deg)';
    } else {
        // Expand
        content.style.display = 'block';
        section.setAttribute('aria-expanded', 'true');
        button.setAttribute('aria-expanded', 'true');
        icon.style.transform = 'rotate(90deg)';
    }
}

/**
 * Create a basic error card when ErrorCards module is not available
 * @param {Object} error - Error object
 * @returns {string} - HTML string for basic error card
 */
function createBasicErrorCard(error) {
    return `
        <div class="pf-v5-c-card pf-m-compact">
            <div class="pf-v5-c-card__body">
                <h4 class="pf-v5-c-title pf-m-md">${formatRuleType(error.type)}</h4>
                <p>${error.message}</p>
                ${error.text_segment ? `
                    <div class="pf-v5-c-code-block pf-m-plain">
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
 * Process content for safe display (remove or escape potentially harmful elements)
 * @param {string} content - Raw content to process
 * @returns {string} - Safely processed content
 */
function processContentForDisplay(content) {
    if (!content) return '';
    
    // Basic HTML sanitization - remove script tags and dangerous attributes
    let safeContent = content
        .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
        .replace(/on\w+="[^"]*"/gi, '')
        .replace(/javascript:/gi, '');
    
    return safeContent;
}

/**
 * Extract text content from potentially mixed HTML/text content
 * @param {string} content - Content that may contain HTML
 * @returns {string} - Plain text content
 */
function extractTextContent(content) {
    if (!content) return '';
    
    // Create a temporary element to extract text content
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = content;
    return tempDiv.textContent || tempDiv.innerText || '';
}

/**
 * Create preview text from content (truncated and cleaned)
 * @param {string} content - Original content
 * @param {number} maxLength - Maximum length of preview (default: 200)
 * @returns {string} - Preview text
 */
function createContentPreview(content, maxLength = 200) {
    if (!content) return '';
    
    const textContent = extractTextContent(content);
    
    if (textContent.length <= maxLength) {
        return textContent;
    }
    
    return textContent.substring(0, maxLength).trim() + '...';
}

/**
 * Generate CSS styles for highlighting and content display
 * @returns {string} - CSS string for highlighting styles
 */
function generateHighlightingStyles() {
    return `
        /* Error highlighting styles */
        mark {
            position: relative;
            transition: all 0.2s ease;
        }
        
        mark:hover {
            opacity: 0.8;
        }
        
        /* Error summary styles */
        .pf-v5-c-expandable-section__toggle {
            width: 100%;
            text-align: left;
            background: none;
            border: none;
            padding: 0.75rem;
            border-radius: var(--pf-v5-global--BorderRadius--sm);
            transition: background-color 0.2s ease;
        }
        
        .pf-v5-c-expandable-section__toggle:hover {
            background-color: var(--pf-v5-global--palette--black-150);
        }
        
        .pf-v5-c-expandable-section__toggle-icon i {
            transition: transform 0.2s ease;
            margin-right: 0.5rem;
        }
        
        .pf-v5-c-expandable-section__content {
            transition: all 0.3s ease;
        }
        
        /* Content processing styles */
        .processed-content {
            line-height: 1.6;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        .content-preview {
            font-style: italic;
            color: var(--pf-v5-global--Color--200);
            margin-top: 0.5rem;
        }
    `;
}

// Export functions for use in other modules
if (typeof window !== 'undefined') {
    window.ErrorHighlighting = {
        escapeHtml,
        highlightErrors,
        getDefaultHighlightColor,
        createErrorSummary,
        createNoErrorsMessage,
        groupErrorsByType,
        createErrorTypeSection,
        toggleErrorTypeSection,
        createBasicErrorCard,
        processContentForDisplay,
        extractTextContent,
        createContentPreview,
        generateHighlightingStyles
    };
}