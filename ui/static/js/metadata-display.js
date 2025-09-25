/**
 * Metadata Assistant Display Component (Module 3)
 * Integrates with existing PatternFly design system
 * Follows same patterns as modular-compliance-display.js
 */

/**
 * Main entry point - called from display-main.js
 * @param {Object} metadataData - Generated metadata from backend
 * @param {string} contentType - Document content type (concept, procedure, reference)
 */
function displayMetadataResults(metadataData, contentType = 'concept') {
    if (!metadataData || !metadataData.success) {
        return; // Don't display if metadata generation failed
    }

    // Store metadata globally for editor access
    window.currentMetadataForEditor = {
        ...metadataData.metadata,
        content_type: contentType,
        raw_metadata: metadataData // Store full response for reference
    };

    // Create metadata section using existing patterns
    const metadataSection = createMetadataSection(metadataData, contentType);
    const resultsContainer = document.getElementById('analysis-results');
    
    if (resultsContainer) {
        // Remove existing metadata section if present
        const existingMetadata = document.getElementById('metadata-section');
        if (existingMetadata) {
            existingMetadata.remove();
        }
        
        // Insert metadata section using same grid pattern as other modules
        const mainGrid = resultsContainer.querySelector('.pf-v5-l-grid');
        
        if (mainGrid) {
            // Add as new grid item - Module 3
            const metadataGridItem = document.createElement('div');
            metadataGridItem.className = 'pf-v5-l-grid__item pf-m-8-col-on-lg pf-m-12-col';
            metadataGridItem.appendChild(metadataSection);
            mainGrid.appendChild(metadataGridItem);
        } else {
            // Fallback: append to results container
            resultsContainer.appendChild(metadataSection);
        }
    }
}

/**
 * Create metadata section using existing PatternFly patterns
 * Consistent with createModularComplianceSection()
 */
function createMetadataSection(metadataData, contentType) {
    const section = document.createElement('div');
    section.id = 'metadata-section';
    section.className = 'pf-v5-c-card app-card pf-v5-u-mt-lg';
    
    const generatedMetadata = metadataData.metadata || {};
    const confidence = calculateOverallConfidence(generatedMetadata.generation_metadata?.confidence_scores || {});
    const processingTime = metadataData.processing_time || generatedMetadata.generation_metadata?.processing_time_seconds || 0;
    const degradedMode = metadataData.degraded_mode || false;
    
    section.innerHTML = `
        <div class="pf-v5-c-card__header">
            <div class="pf-v5-c-card__header-main">
                <h2 class="pf-v5-c-title pf-m-xl">
                    <i class="fas fa-tags pf-v5-u-mr-sm" style="color: var(--pf-v5-global--primary-color--100);"></i>
                    Generated Metadata
                </h2>
                <p class="pf-v5-c-card__subtitle">
                    AI-powered metadata extraction for ${capitalizeFirst(contentType)} content
                </p>
            </div>
            <div class="pf-v5-c-card__actions">
                <span class="pf-v5-c-label ${getConfidenceLabelClass(confidence)}">
                    <span class="pf-v5-c-label__content">
                        <i class="fas fa-magic pf-v5-c-label__icon"></i>
                        ${Math.round(confidence * 100)}% Confidence
                    </span>
                </span>
                ${degradedMode ? `
                    <span class="pf-v5-c-label pf-m-orange pf-v5-u-ml-sm">
                        <span class="pf-v5-c-label__content">
                            <i class="fas fa-exclamation-triangle pf-v5-c-label__icon"></i>
                            Fallback Mode
                        </span>
                    </span>
                ` : ''}
            </div>
        </div>
        
        <div class="pf-v5-c-card__body">
            <!-- Status Alert -->
            ${degradedMode ? `
                <div class="pf-v5-c-alert pf-m-warning pf-m-inline pf-v5-u-mb-lg">
                    <div class="pf-v5-c-alert__icon">
                        <i class="fas fa-exclamation-triangle"></i>
                    </div>
                    <h4 class="pf-v5-c-alert__title">Fallback mode active</h4>
                    <div class="pf-v5-c-alert__description">
                        Some advanced features were unavailable. Basic metadata generated using fallback methods.
                    </div>
                </div>
            ` : ''}
            
            <!-- Generated Metadata Grid -->
            <div class="pf-v5-l-grid pf-m-gutter pf-v5-u-mb-lg">
                ${createMetadataGrid(generatedMetadata, contentType)}
            </div>
            
            <!-- Interactive Editor Section (expandable) -->
            <div class="pf-v5-c-expandable-section pf-m-detached" id="metadata-editor-container">
                <button class="pf-v5-c-expandable-section__toggle" type="button" aria-expanded="false" onclick="toggleMetadataEditor(this)">
                    <span class="pf-v5-c-expandable-section__toggle-icon">
                        <i class="fas fa-angle-right"></i>
                    </span>
                    <span class="pf-v5-c-expandable-section__toggle-text">
                        Interactive Editor - Fine-tune metadata
                    </span>
                </button>
                <div class="pf-v5-c-expandable-section__content" id="interactive-editor-content" style="display: none;">
                    <!-- Interactive editor will be loaded here -->
                    <div class="pf-v5-u-p-md">
                        <p class="pf-v5-c-content">
                            <i class="fas fa-spinner fa-spin pf-v5-u-mr-sm"></i>
                            Loading interactive editor...
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="pf-v5-c-card__footer">
            <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-space-between">
                <div class="pf-v5-l-flex pf-m-space-items-sm">
                    <button class="pf-v5-c-button pf-m-secondary" onclick="exportMetadata('yaml')" title="Export as YAML">
                        <i class="fas fa-download pf-v5-u-mr-sm"></i>
                        Export YAML
                    </button>
                    <button class="pf-v5-c-button pf-m-secondary" onclick="exportMetadata('json')" title="Export as JSON">
                        <i class="fas fa-code pf-v5-u-mr-sm"></i> 
                        Export JSON
                    </button>
                    <button class="pf-v5-c-button pf-m-primary" onclick="refineMetadata()" title="AI-powered refinement">
                        <i class="fas fa-sparkles pf-v5-u-mr-sm"></i>
                        Refine Metadata
                    </button>
                </div>
                <div class="pf-v5-c-content">
                    <small class="pf-v5-u-color-200">
                        Generated in ${processingTime.toFixed(2)}s
                    </small>
                </div>
            </div>
        </div>
    `;
    
    return section;
}

/**
 * Create metadata display grid using PatternFly patterns
 */
function createMetadataGrid(metadata, contentType) {
    return `
        <div class="pf-v5-l-grid__item pf-m-6-col-on-lg pf-m-12-col">
            <div class="pf-v5-c-card pf-m-flat pf-m-plain">
                <div class="pf-v5-c-card__header pf-v5-u-pb-sm">
                    <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-color-100">
                        <i class="fas fa-info-circle pf-v5-u-mr-sm pf-v5-u-color-200"></i>
                        Basic Information
                    </h3>
                </div>
                <div class="pf-v5-c-card__body pf-v5-u-pt-sm">
                    <div class="pf-v5-c-description-list pf-m-horizontal-on-md">
                        ${createMetadataField('Title', metadata.title, { bold: true })}
                        ${createMetadataField('Description', metadata.description, { bold: true, multiline: true })}
                        ${createMetadataField('Content Type', contentType, { bold: true, capitalize: true })}
                        ${createMetadataField('Audience', metadata.audience, { bold: true })}
                        ${createMetadataField('Intent', metadata.intent, { bold: true })}
                    </div>
                </div>
            </div>
        </div>
        <div class="pf-v5-l-grid__item pf-m-6-col-on-lg pf-m-12-col">
            <div class="pf-v5-c-card pf-m-flat pf-m-plain">
                <div class="pf-v5-c-card__header pf-v5-u-pb-sm">
                    <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-color-100">
                        <i class="fas fa-tags pf-v5-u-mr-sm pf-v5-u-color-200"></i>
                        Classification
                    </h3>
                </div>
                <div class="pf-v5-c-card__body pf-v5-u-pt-sm">
                    <div class="pf-v5-c-description-list">
                        ${createKeywordsField(metadata.keywords)}
                        ${createTaxonomyField(metadata.taxonomy_tags)}
                        ${createAlgorithmsField(metadata.generation_metadata?.algorithms_used)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Clean markup from text content (removes AsciiDoc, Markdown, HTML, etc.)
 */
function cleanMarkupFromText(text) {
    if (!text) return '';
    
    let cleaned = text;
    
    // Remove AsciiDoc formatting
    cleaned = cleaned.replace(/^=+\s*(.*)$/gm, '$1'); // Headers
    cleaned = cleaned.replace(/^:.*?:/gm, ''); // Attributes like :toc:
    cleaned = cleaned.replace(/^\[.*?\]$/gm, ''); // Attribute blocks
    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1'); // Bold
    cleaned = cleaned.replace(/\*(.*?)\*/g, '$1'); // Italic
    cleaned = cleaned.replace(/`(.*?)`/g, '$1'); // Code
    
    // Remove Markdown formatting
    cleaned = cleaned.replace(/^#+\s*(.*)$/gm, '$1'); // Headers
    cleaned = cleaned.replace(/\*\*(.*?)\*\*/g, '$1'); // Bold
    cleaned = cleaned.replace(/\*(.*?)\*/g, '$1'); // Italic
    cleaned = cleaned.replace(/`(.*?)`/g, '$1'); // Code
    cleaned = cleaned.replace(/\[(.*?)\]\(.*?\)/g, '$1'); // Links
    
    // Remove HTML tags
    cleaned = cleaned.replace(/<[^>]*>/g, '');
    
    // Clean up excessive whitespace and newlines
    cleaned = cleaned.replace(/\n{3,}/g, '\n\n'); // Max 2 consecutive newlines
    cleaned = cleaned.replace(/^\s+|\s+$/g, ''); // Trim start/end
    cleaned = cleaned.replace(/\s+/g, ' '); // Collapse multiple spaces
    
    return cleaned;
}

/**
 * Create individual metadata field display with world-class formatting
 */
function createMetadataField(label, value, options = {}) {
    if (!value) return '';
    
    // Process value based on options
    let displayValue = value;
    
    // Clean markup from description fields
    if (options.multiline || label.toLowerCase().includes('description')) {
        displayValue = cleanMarkupFromText(displayValue);
    }
    
    if (options.capitalize) {
        displayValue = capitalizeFirst(displayValue);
    }
    if (options.truncate && displayValue.length > options.truncate) {
        displayValue = displayValue.substring(0, options.truncate) + '...';
    }
    
    // Style classes for different field types
    const termClasses = [
        'pf-v5-c-description-list__term',
        'pf-v5-u-mb-sm'
    ].filter(Boolean).join(' ');
    
    const textClasses = [
        'pf-v5-c-description-list__text',
        options.bold ? 'pf-v5-u-font-weight-bold' : ''
    ].filter(Boolean).join(' ');
    
    const descriptionClasses = [
        'pf-v5-c-description-list__description',
        options.multiline ? 'pf-v5-u-mb-md' : 'pf-v5-u-mb-sm'
    ].filter(Boolean).join(' ');
    
    // Format multiline content and handle expandable descriptions
    const formattedValue = options.multiline && displayValue.includes('\n') 
        ? displayValue.split('\n').map(line => escapeHtml(line.trim())).filter(line => line).join('<br>')
        : escapeHtml(displayValue);
    
    // Check if description is long and should be truncatable
    const shouldTruncate = options.multiline && displayValue.length > 150;
    const truncatedValue = shouldTruncate ? escapeHtml(displayValue.substring(0, 150)) + '...' : formattedValue;
    const uniqueId = shouldTruncate ? 'desc-' + Math.random().toString(36).substr(2, 9) : null;
    
    
    return `
        <div class="pf-v5-c-description-list__group pf-v5-u-mb-md">
            <dt class="${termClasses}">
                <span class="${textClasses}">
                    ${options.bold ? '<strong>' + label + '</strong>' : label}:
                </span>
            </dt>
            <dd class="${descriptionClasses}">
                <div class="pf-v5-c-description-list__text pf-v5-u-color-200 ${options.multiline ? 'pf-v5-u-line-height-md' : ''}" 
                     ${options.tooltip ? `title="${escapeHtml(value)}"` : ''}>
                    ${shouldTruncate ? `
                        <div id="${uniqueId}-truncated">${truncatedValue}</div>
                        <div id="${uniqueId}-full" style="display: none;">${formattedValue}</div>
                        <button type="button" class="pf-v5-c-button pf-m-link pf-m-inline description-expand-btn pf-v5-u-mt-xs" 
                                id="${uniqueId}-toggle" onclick="toggleDescription('${uniqueId}')">
                            <span class="expand-text">Show more</span>
                            <i class="fas fa-angle-down pf-v5-u-ml-xs expand-icon"></i>
                        </button>
                    ` : formattedValue}
                </div>
            </dd>
        </div>
    `;
}

/**
 * Create keywords display with enhanced chips styling and expandable functionality
 */
function createKeywordsField(keywords) {
    if (!keywords || keywords.length === 0) return '';
    
    const visibleKeywords = keywords.slice(0, 8);
    const hiddenKeywords = keywords.slice(8);
    const uniqueId = 'keywords-' + Math.random().toString(36).substr(2, 9);
    
    const visibleKeywordChips = visibleKeywords.map(keyword => 
        `<span class="pf-v5-c-chip pf-v5-u-mb-xs pf-v5-u-mr-xs">
            <span class="pf-v5-c-chip__text">${escapeHtml(keyword)}</span>
        </span>`
    ).join('');
    
    const hiddenKeywordChips = hiddenKeywords.map(keyword => 
        `<span class="pf-v5-c-chip pf-v5-u-mb-xs pf-v5-u-mr-xs">
            <span class="pf-v5-c-chip__text">${escapeHtml(keyword)}</span>
        </span>`
    ).join('');
    
    return `
        <div class="pf-v5-c-description-list__group pf-v5-u-mb-md">
            <dt class="pf-v5-c-description-list__term pf-v5-u-mb-sm">
                <span class="pf-v5-c-description-list__text pf-v5-u-font-weight-bold">
                    <strong>Keywords</strong>:
                </span>
            </dt>
            <dd class="pf-v5-c-description-list__description">
                <div class="pf-v5-c-chip-group pf-v5-u-display-flex pf-v5-u-flex-wrap">
                    ${visibleKeywordChips}
                    <div id="${uniqueId}-hidden" class="keyword-hidden-chips" style="display: none;">
                        ${hiddenKeywordChips}
                    </div>
                    ${hiddenKeywords.length > 0 ? `
                        <button id="${uniqueId}-toggle" class="pf-v5-c-chip pf-m-overflow pf-v5-u-mb-xs pf-v5-u-mr-xs keyword-expand-btn" 
                                onclick="toggleKeywords('${uniqueId}')" type="button">
                            <span class="pf-v5-c-chip__text">+${hiddenKeywords.length} more</span>
                        </button>
                    ` : ''}
                </div>
            </dd>
        </div>
    `;
}

/**
 * Create taxonomy tags display with enhanced colored labels
 */
function createTaxonomyField(taxonomyTags) {
    if (!taxonomyTags || taxonomyTags.length === 0) return '';
    
    const taxonomyLabels = taxonomyTags.map(tag => 
        `<span class="pf-v5-c-label pf-m-blue pf-v5-u-mb-xs pf-v5-u-mr-xs">
            <span class="pf-v5-c-label__content">
                <i class="fas fa-folder pf-v5-c-label__icon"></i>
                ${escapeHtml(tag)}
            </span>
        </span>`
    ).join('');
    
    return `
        <div class="pf-v5-c-description-list__group pf-v5-u-mb-md">
            <dt class="pf-v5-c-description-list__term pf-v5-u-mb-sm">
                <span class="pf-v5-c-description-list__text pf-v5-u-font-weight-bold">
                    <strong>Categories</strong>:
                </span>
            </dt>
            <dd class="pf-v5-c-description-list__description">
                <div class="pf-v5-l-flex pf-m-space-items-xs pf-v5-u-flex-wrap">
                    ${taxonomyLabels}
                </div>
            </dd>
        </div>
    `;
}

/**
 * Create algorithms used display with enhanced formatting
 */
function createAlgorithmsField(algorithms) {
    if (!algorithms) return '';
    
    const algorithmItems = Object.entries(algorithms).map(([component, algorithm]) => 
        `<div class="pf-v5-u-mb-xs">
            <strong class="pf-v5-u-color-100">${capitalizeFirst(component)}</strong>: 
            <span class="pf-v5-u-color-200">${algorithm.replace(/_/g, ' ')}</span>
        </div>`
    ).join('');
    
    return `
        <div class="pf-v5-c-description-list__group pf-v5-u-mb-md">
            <dt class="pf-v5-c-description-list__term pf-v5-u-mb-sm">
                <span class="pf-v5-c-description-list__text pf-v5-u-font-weight-bold">
                    <strong>Algorithms Used</strong>:
                </span>
            </dt>
            <dd class="pf-v5-c-description-list__description">
                <div class="pf-v5-c-description-list__text pf-v5-u-font-size-sm">
                    ${algorithmItems}
                </div>
            </dd>
        </div>
    `;
}

/**
 * Calculate overall confidence from individual confidence scores
 */
function calculateOverallConfidence(confidenceScores) {
    if (!confidenceScores || Object.keys(confidenceScores).length === 0) {
        return 0.5; // Default confidence
    }
    
    const scores = Object.values(confidenceScores);
    return scores.reduce((sum, score) => sum + score, 0) / scores.length;
}

/**
 * Get confidence label class based on confidence score
 */
function getConfidenceLabelClass(confidence) {
    if (confidence >= 0.8) return 'pf-m-green';
    if (confidence >= 0.6) return 'pf-m-blue';
    if (confidence >= 0.4) return 'pf-m-orange';
    return 'pf-m-red';
}

/**
 * Toggle metadata editor expandable section
 */
function toggleMetadataEditor(button) {
    const expandable = button.closest('.pf-v5-c-expandable-section');
    const content = expandable.querySelector('.pf-v5-c-expandable-section__content');
    const icon = button.querySelector('.pf-v5-c-expandable-section__toggle-icon i');
    
    if (content.style.display === 'none' || content.style.display === '') {
        // Expand
        content.style.display = 'block';
        button.setAttribute('aria-expanded', 'true');
        expandable.classList.add('pf-m-expanded');
        icon.className = 'fas fa-angle-down';
        
        // Initialize interactive editor on first open
        if (!content.dataset.initialized) {
            initializeInteractiveEditor();
            content.dataset.initialized = 'true';
        }
    } else {
        // Collapse
        content.style.display = 'none';
        button.setAttribute('aria-expanded', 'false');
        expandable.classList.remove('pf-m-expanded');
        icon.className = 'fas fa-angle-right';
    }
}

/**
 * Initialize interactive editor (placeholder for metadata-editor.js)
 */
function initializeInteractiveEditor() {
    const content = document.getElementById('interactive-editor-content');
    if (content && typeof createInteractiveMetadataEditor === 'function') {
        // Function will be available when metadata-editor.js is loaded
        createInteractiveMetadataEditor(content);
    } else {
        // Fallback message
        content.innerHTML = `
            <div class="pf-v5-c-empty-state pf-v5-u-p-lg">
                <div class="pf-v5-c-empty-state__content">
                    <i class="fas fa-tools pf-v5-c-empty-state__icon" aria-hidden="true"></i>
                    <h4 class="pf-v5-c-title pf-m-lg">Interactive Editor</h4>
                    <div class="pf-v5-c-empty-state__body">
                        Interactive metadata editing will be available once the editor component is loaded.
                    </div>
                </div>
            </div>
        `;
    }
}

/**
 * Export metadata functionality (placeholder for metadata-export.js)
 */
function exportMetadata(format) {
    if (typeof handleMetadataExport === 'function') {
        handleMetadataExport(format);
    } else {
        console.log(`Export ${format} functionality not yet loaded`);
        // Show a notification that export is not available yet
        if (typeof showNotification === 'function') {
            showNotification(`${format.toUpperCase()} export will be available once the export component is loaded.`, 'info');
        }
    }
}

/**
 * Refine metadata functionality (placeholder for future AI refinement)
 */
function refineMetadata() {
    console.log('Refine metadata functionality');
    
    // Show a placeholder notification
    if (typeof showNotification === 'function') {
        showNotification('AI-powered metadata refinement coming soon!', 'info');
    } else {
        alert('AI-powered metadata refinement feature will be available in a future update.');
    }
}

/**
 * Toggle keywords visibility - expand/collapse "+N more" functionality
 */
function toggleKeywords(uniqueId) {
    const hiddenChips = document.getElementById(uniqueId + '-hidden');
    const toggleBtn = document.getElementById(uniqueId + '-toggle');
    
    if (hiddenChips && toggleBtn) {
        const isHidden = hiddenChips.style.display === 'none';
        
        if (isHidden) {
            // Show hidden keywords
            hiddenChips.style.display = 'contents';
            toggleBtn.innerHTML = '<span class="pf-v5-c-chip__text">Show less</span>';
            toggleBtn.setAttribute('title', 'Hide additional keywords');
        } else {
            // Hide keywords
            hiddenChips.style.display = 'none';
            const hiddenCount = hiddenChips.children.length;
            toggleBtn.innerHTML = `<span class="pf-v5-c-chip__text">+${hiddenCount} more</span>`;
            toggleBtn.setAttribute('title', `Show ${hiddenCount} more keywords`);
        }
    }
}

/**
 * Toggle description visibility - expand/collapse long descriptions
 */
function toggleDescription(uniqueId) {
    const truncatedDiv = document.getElementById(uniqueId + '-truncated');
    const fullDiv = document.getElementById(uniqueId + '-full');
    const toggleBtn = document.getElementById(uniqueId + '-toggle');
    
    if (truncatedDiv && fullDiv && toggleBtn) {
        const isExpanded = fullDiv.style.display !== 'none';
        
        if (isExpanded) {
            // Collapse description
            truncatedDiv.style.display = 'block';
            fullDiv.style.display = 'none';
            toggleBtn.querySelector('.expand-text').textContent = 'Show more';
            toggleBtn.querySelector('.expand-icon').className = 'fas fa-angle-down pf-v5-u-ml-xs expand-icon';
        } else {
            // Expand description
            truncatedDiv.style.display = 'none';
            fullDiv.style.display = 'block';
            toggleBtn.querySelector('.expand-text').textContent = 'Show less';
            toggleBtn.querySelector('.expand-icon').className = 'fas fa-angle-up pf-v5-u-ml-xs expand-icon';
        }
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

// Export functions for global access - Module 3 integration
window.displayMetadataResults = displayMetadataResults;
window.toggleMetadataEditor = toggleMetadataEditor;
window.exportMetadata = exportMetadata;
window.refineMetadata = refineMetadata;
