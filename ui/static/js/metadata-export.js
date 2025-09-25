/**
 * Metadata Export Functions
 * Handles YAML/JSON export with proper formatting
 * Integrates with existing file handling patterns
 */

/**
 * Export metadata in specified format
 * @param {string} format - 'yaml' or 'json'
 */
function handleMetadataExport(format = 'yaml') {
    const metadataSection = document.getElementById('metadata-section');
    if (!metadataSection) {
        showExportError('No metadata available to export');
        return;
    }
    
    try {
        // Extract current metadata from DOM
        const currentMetadata = extractCurrentMetadata();
        
        let exportContent;
        let filename;
        let mimeType;
        
        switch (format.toLowerCase()) {
            case 'yaml':
                exportContent = convertToYAML(currentMetadata);
                filename = generateFilename('yaml');
                mimeType = 'text/yaml';
                break;
            case 'json':
                exportContent = JSON.stringify(currentMetadata, null, 2);
                filename = generateFilename('json');
                mimeType = 'application/json';
                break;
            case 'frontmatter':
                exportContent = convertToFrontmatter(currentMetadata);
                filename = generateFilename('md');
                mimeType = 'text/markdown';
                break;
            default:
                showExportError(`Unsupported export format: ${format}`);
                return;
        }
        
        // Download file
        downloadFile(exportContent, filename, mimeType);
        
        // Show success notification
        showExportSuccess(`Metadata exported as ${format.toUpperCase()}!`);
        
        // Record export activity
        recordExportActivity(format, filename);
        
    } catch (error) {
        console.error('Export failed:', error);
        showExportError(`Export failed: ${error.message}`);
    }
}

/**
 * Extract current metadata from the DOM
 */
function extractCurrentMetadata() {
    // Try to get metadata from global variable first (if set by editor)
    if (window.currentEditableMetadata) {
        return formatMetadataForExport(window.currentEditableMetadata);
    }
    
    // Otherwise extract from the display
    const metadata = {
        title: extractFieldValue('title') || 'Untitled Document',
        description: extractFieldValue('description') || '',
        keywords: extractKeywordsFromChips(),
        categories: extractCategoriesFromLabels(),
        audience: extractFieldValue('audience') || 'General',
        content_type: extractContentType(),
        generated_at: new Date().toISOString(),
        generator: 'Content Editorial Assistant - Metadata Assistant v2.0'
    };
    
    // Remove empty fields
    Object.keys(metadata).forEach(key => {
        if (!metadata[key] || (Array.isArray(metadata[key]) && metadata[key].length === 0)) {
            delete metadata[key];
        }
    });
    
    return metadata;
}

/**
 * Format metadata for export (clean up internal fields)
 */
function formatMetadataForExport(metadata) {
    return {
        title: metadata.title || 'Untitled Document',
        description: metadata.description || '',
        keywords: metadata.keywords || [],
        categories: metadata.taxonomy_tags || [],
        audience: metadata.audience || 'General',
        content_type: metadata.content_type || 'concept',
        intent: metadata.intent || 'informational',
        generated_at: new Date().toISOString(),
        generator: 'Content Editorial Assistant - Metadata Assistant v2.0'
    };
}

/**
 * Extract field value from description list
 */
function extractFieldValue(fieldName) {
    const fieldElement = document.querySelector(`#metadata-section [data-field="${fieldName}"]`);
    if (fieldElement) {
        return fieldElement.textContent.trim();
    }
    
    // Fallback: try to find by label text
    const labelElements = document.querySelectorAll('#metadata-section .pf-v5-c-description-list__term .pf-v5-c-description-list__text');
    for (const labelEl of labelElements) {
        if (labelEl.textContent.toLowerCase().includes(fieldName.toLowerCase())) {
            const descriptionEl = labelEl.closest('.pf-v5-c-description-list__group')?.querySelector('.pf-v5-c-description-list__description .pf-v5-c-description-list__text');
            if (descriptionEl) {
                return descriptionEl.textContent.trim();
            }
        }
    }
    
    return '';
}

/**
 * Extract keywords from chip elements
 */
function extractKeywordsFromChips() {
    const keywordChips = document.querySelectorAll('#metadata-section .pf-v5-c-chip .pf-v5-c-chip__text');
    const keywords = [];
    
    keywordChips.forEach(chip => {
        const text = chip.textContent.trim();
        // Skip overflow chips (e.g., "+2 more")
        if (text && !text.match(/^\+\d+\s+more$/)) {
            keywords.push(text);
        }
    });
    
    return keywords;
}

/**
 * Extract categories from label elements
 */
function extractCategoriesFromLabels() {
    const categoryLabels = document.querySelectorAll('#metadata-section .pf-v5-c-label:not(.pf-m-green):not(.pf-m-orange) .pf-v5-c-label__content');
    const categories = [];
    
    categoryLabels.forEach(label => {
        const text = label.textContent.trim();
        // Remove icon characters and get clean text
        const cleanText = text.replace(/^[^\w\s]*/, '').trim();
        if (cleanText) {
            categories.push(cleanText);
        }
    });
    
    return categories;
}

/**
 * Extract content type from the page or metadata
 */
function extractContentType() {
    // Try to get from page context or metadata section
    const contentTypeElement = document.querySelector('[data-content-type]');
    if (contentTypeElement) {
        return contentTypeElement.getAttribute('data-content-type');
    }
    
    // Try to extract from subtitle or other indicators
    const subtitle = document.querySelector('#metadata-section .pf-v5-c-card__subtitle');
    if (subtitle) {
        const match = subtitle.textContent.match(/(\w+)\s+content/i);
        if (match) {
            return match[1].toLowerCase();
        }
    }
    
    return 'concept'; // Default
}

/**
 * Convert metadata to YAML format
 */
function convertToYAML(metadata) {
    const yamlLines = ['---'];
    
    // Add fields in a logical order
    const fieldOrder = ['title', 'description', 'keywords', 'categories', 'audience', 'content_type', 'intent', 'generated_at', 'generator'];
    
    fieldOrder.forEach(field => {
        if (metadata.hasOwnProperty(field) && metadata[field] !== undefined) {
            const value = metadata[field];
            
            if (Array.isArray(value)) {
                if (value.length > 0) {
                    yamlLines.push(`${field}:`);
                    value.forEach(item => {
                        yamlLines.push(`  - "${escapeYAMLString(item)}"`);
                    });
                }
            } else if (typeof value === 'string') {
                yamlLines.push(`${field}: "${escapeYAMLString(value)}"`);
            } else {
                yamlLines.push(`${field}: ${value}`);
            }
        }
    });
    
    yamlLines.push('---');
    yamlLines.push('');
    yamlLines.push('<!-- Your content goes here -->');
    
    return yamlLines.join('\n');
}

/**
 * Convert metadata to frontmatter format (YAML + content placeholder)
 */
function convertToFrontmatter(metadata) {
    const yaml = convertToYAML(metadata);
    return yaml + '\n\n# ' + (metadata.title || 'Your Title Here') + '\n\nYour content goes here...\n';
}

/**
 * Escape special characters in YAML strings
 */
function escapeYAMLString(str) {
    if (!str) return '';
    return str.replace(/"/g, '\\"').replace(/\n/g, '\\n').replace(/\r/g, '\\r').replace(/\t/g, '\\t');
}

/**
 * Generate filename based on title and format
 */
function generateFilename(extension) {
    const metadataSection = document.getElementById('metadata-section');
    let baseFilename = 'metadata';
    
    // Try to use document title
    const titleField = extractFieldValue('title');
    if (titleField && titleField !== 'Untitled Document') {
        baseFilename = titleField
            .toLowerCase()
            .replace(/[^\w\s-]/g, '') // Remove special chars
            .replace(/\s+/g, '-') // Replace spaces with hyphens
            .substring(0, 50); // Limit length
    } else {
        // Use timestamp
        const now = new Date();
        baseFilename = `metadata-${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    }
    
    return `${baseFilename}.${extension}`;
}

/**
 * Download file using existing utility functions or fallback
 */
function downloadFile(content, filename, mimeType) {
    // Check if there's an existing download utility
    if (typeof createAndDownloadFile === 'function') {
        createAndDownloadFile(content, filename, mimeType);
        return;
    }
    
    // Fallback implementation
    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    setTimeout(() => window.URL.revokeObjectURL(url), 100);
}

/**
 * Show export success notification
 */
function showExportSuccess(message) {
    if (typeof showNotification === 'function') {
        showNotification(message, 'success');
    } else {
        console.log('✅ ' + message);
        // Create a temporary success indicator
        createTemporaryNotification(message, 'success');
    }
}

/**
 * Show export error notification
 */
function showExportError(message) {
    if (typeof showNotification === 'function') {
        showNotification(message, 'danger');
    } else {
        console.error('❌ ' + message);
        createTemporaryNotification(message, 'error');
        alert('Export Error: ' + message);
    }
}

/**
 * Create temporary notification if no notification system exists
 */
function createTemporaryNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `pf-v5-c-alert pf-m-${type === 'error' ? 'danger' : type} pf-m-inline`;
    notification.style.position = 'fixed';
    notification.style.top = '20px';
    notification.style.right = '20px';
    notification.style.zIndex = '9999';
    notification.style.minWidth = '300px';
    
    notification.innerHTML = `
        <div class="pf-v5-c-alert__icon">
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-triangle'}"></i>
        </div>
        <h4 class="pf-v5-c-alert__title">Export ${type === 'success' ? 'Complete' : 'Error'}</h4>
        <div class="pf-v5-c-alert__description">${message}</div>
        <div class="pf-v5-c-alert__action">
            <button class="pf-v5-c-button pf-m-plain" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

/**
 * Record export activity for analytics
 */
function recordExportActivity(format, filename) {
    try {
        // Record in analytics if available
        if (typeof recordAnalyticsEvent === 'function') {
            recordAnalyticsEvent('metadata_export', {
                format: format,
                filename: filename,
                timestamp: new Date().toISOString()
            });
        }
        
        // Log for debugging
        console.log('📥 Metadata exported:', { format, filename });
    } catch (error) {
        console.warn('Failed to record export activity:', error);
    }
}

/**
 * Get available export formats
 */
function getAvailableExportFormats() {
    return [
        {
            id: 'yaml',
            name: 'YAML Frontmatter',
            description: 'YAML metadata block for static site generators',
            icon: 'fas fa-code',
            extension: '.yaml'
        },
        {
            id: 'json',
            name: 'JSON Metadata',
            description: 'Structured JSON for API integration',
            icon: 'fas fa-brackets-curly',
            extension: '.json'
        },
        {
            id: 'frontmatter',
            name: 'Markdown with Frontmatter',
            description: 'Complete Markdown file with YAML frontmatter',
            icon: 'fab fa-markdown',
            extension: '.md'
        }
    ];
}

/**
 * Show export format selector
 */
function showExportFormatSelector() {
    const formats = getAvailableExportFormats();
    
    // Create modal or dropdown with format options
    const modal = document.createElement('div');
    modal.className = 'pf-v5-c-backdrop';
    modal.innerHTML = `
        <div class="pf-v5-l-bullseye">
            <div class="pf-v5-c-modal-box pf-m-sm">
                <header class="pf-v5-c-modal-box__header">
                    <h1 class="pf-v5-c-modal-box__title">
                        <i class="fas fa-download pf-v5-u-mr-sm"></i>
                        Export Metadata
                    </h1>
                </header>
                <div class="pf-v5-c-modal-box__body">
                    <p>Choose the export format for your metadata:</p>
                    <div class="pf-v5-l-stack pf-m-gutter">
                        ${formats.map(format => `
                            <div class="pf-v5-l-stack__item">
                                <button class="pf-v5-c-button pf-m-tertiary pf-m-block" 
                                        onclick="exportMetadataFormat('${format.id}'); closeExportModal();">
                                    <i class="${format.icon} pf-v5-u-mr-sm"></i>
                                    <span class="pf-v5-u-mr-sm">${format.name}</span>
                                    <small class="pf-v5-u-color-200">(${format.extension})</small>
                                </button>
                                <small class="pf-v5-c-content">${format.description}</small>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <footer class="pf-v5-c-modal-box__footer">
                    <button class="pf-v5-c-button pf-m-secondary" onclick="closeExportModal()">
                        Cancel
                    </button>
                </footer>
            </div>
        </div>
    `;
    
    modal.id = 'export-format-modal';
    document.body.appendChild(modal);
}

/**
 * Export with specific format from modal
 */
function exportMetadataFormat(format) {
    handleMetadataExport(format);
}

/**
 * Close export format modal
 */
function closeExportModal() {
    const modal = document.getElementById('export-format-modal');
    if (modal) {
        modal.remove();
    }
}

// Export functions for global access
window.handleMetadataExport = handleMetadataExport;
window.exportMetadata = handleMetadataExport; // Alias for compatibility
window.showExportFormatSelector = showExportFormatSelector;
window.exportMetadataFormat = exportMetadataFormat;
window.closeExportModal = closeExportModal;
