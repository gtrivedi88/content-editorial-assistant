/**
 * Interactive Metadata Editor - Real-time editing with feedback
 * Integrates with existing UserFeedback system and database
 * Follows PatternFly design patterns for consistency
 */

/**
 * Global reference to current metadata for editing
 */
let currentEditableMetadata = null;
let metadataChangeCallbacks = [];

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
 * Create and initialize the interactive metadata editor
 * @param {HTMLElement} container - Container element to render editor in
 */
function createInteractiveMetadataEditor(container) {
    if (!container) {
        console.error('No container provided for interactive metadata editor');
        return;
    }

    // Get current metadata from the displayed section
    const metadataSection = document.getElementById('metadata-section');
    if (!metadataSection) {
        container.innerHTML = createEditorErrorState('No metadata available for editing');
        return;
    }

    // Extract current metadata from the display
    currentEditableMetadata = extractMetadataFromDisplay();
    
    // Create the editor interface
    container.innerHTML = createEditorInterface();
    
    // Initialize event listeners
    initializeEditorEventListeners();
    
    // Initialize with current metadata
    populateEditorFields();
}

/**
 * Extract current metadata from the displayed metadata section
 */
function extractMetadataFromDisplay() {
    // Use globally stored metadata if available
    if (window.currentMetadataForEditor) {
        return {
            title: window.currentMetadataForEditor.title || 'Untitled Document',
            description: cleanMarkupFromText(window.currentMetadataForEditor.description) || '',
            keywords: window.currentMetadataForEditor.keywords || [],
            taxonomy_tags: window.currentMetadataForEditor.taxonomy_tags || [],
            audience: window.currentMetadataForEditor.audience || 'General',
            intent: window.currentMetadataForEditor.intent || 'Informational'
        };
    }
    
    // Fallback to DOM extraction (legacy)
    return {
        title: document.querySelector('#metadata-section [data-field="title"]')?.textContent?.trim() || 'Untitled Document',
        description: document.querySelector('#metadata-section [data-field="description"]')?.textContent?.trim() || '',
        keywords: extractKeywordsFromDisplay(),
        taxonomy_tags: extractTaxonomyFromDisplay(),
        audience: document.querySelector('#metadata-section [data-field="audience"]')?.textContent?.trim() || 'General',
        intent: document.querySelector('#metadata-section [data-field="intent"]')?.textContent?.trim() || 'Informational'
    };
}

/**
 * Extract keywords from the current display
 */
function extractKeywordsFromDisplay() {
    const keywordChips = document.querySelectorAll('#metadata-section .pf-v5-c-chip .pf-v5-c-chip__text');
    return Array.from(keywordChips).map(chip => chip.textContent.trim()).filter(k => k && !k.startsWith('+'));
}

/**
 * Extract taxonomy tags from the current display
 */
function extractTaxonomyFromDisplay() {
    const taxonomyLabels = document.querySelectorAll('#metadata-section .pf-v5-c-label:not(.pf-m-green):not(.pf-m-orange) .pf-v5-c-label__content');
    return Array.from(taxonomyLabels).map(label => {
        // Extract text, removing the icon
        const text = label.textContent.trim();
        return text.replace(/^[^\w]*/, ''); // Remove icon characters
    }).filter(t => t);
}

/**
 * Create the main editor interface
 */
function createEditorInterface() {
    return `
        <div class="pf-v5-l-grid pf-m-gutter">
            <!-- Basic Information Editor -->
            <div class="pf-v5-l-grid__item pf-m-6-col-on-lg pf-m-12-col">
                <div class="pf-v5-c-card pf-m-flat">
                    <div class="pf-v5-c-card__header">
                        <h4 class="pf-v5-c-title pf-m-md">
                            <i class="fas fa-edit pf-v5-u-mr-sm"></i>
                            Basic Information
                        </h4>
                    </div>
                    <div class="pf-v5-c-card__body">
                        ${createBasicInfoEditor()}
                    </div>
                </div>
            </div>
            
            <!-- Classification Editor -->
            <div class="pf-v5-l-grid__item pf-m-6-col-on-lg pf-m-12-col">
                <div class="pf-v5-c-card pf-m-flat">
                    <div class="pf-v5-c-card__header">
                        <h4 class="pf-v5-c-title pf-m-md">
                            <i class="fas fa-tags pf-v5-u-mr-sm"></i>
                            Classification
                        </h4>
                    </div>
                    <div class="pf-v5-c-card__body">
                        ${createClassificationEditor()}
                    </div>
                </div>
            </div>
            
            <!-- AI Suggestions -->
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-c-card pf-m-flat">
                    <div class="pf-v5-c-card__header">
                        <h4 class="pf-v5-c-title pf-m-md">
                            <i class="fas fa-lightbulb pf-v5-u-mr-sm"></i>
                            AI Suggestions
                        </h4>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <div id="ai-suggestions-container">
                            ${createSuggestionsInterface()}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Editor Actions -->
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-l-flex pf-m-space-items-md pf-m-justify-content-space-between">
                    <div class="pf-v5-l-flex pf-m-space-items-sm">
                        <button class="pf-v5-c-button pf-m-primary" onclick="saveMetadataChanges()">
                            <i class="fas fa-save pf-v5-u-mr-sm"></i>
                            Save Changes
                        </button>
                        <button class="pf-v5-c-button pf-m-secondary" onclick="revertMetadataChanges()">
                            <i class="fas fa-undo pf-v5-u-mr-sm"></i>
                            Revert Changes
                        </button>
                        <button class="pf-v5-c-button pf-m-link" onclick="requestAISuggestions()">
                            <i class="fas fa-magic pf-v5-u-mr-sm"></i>
                            Get AI Suggestions
                        </button>
                    </div>
                    <div id="editor-status" class="pf-v5-c-content">
                        <small class="pf-v5-u-color-200">
                            Ready to edit
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create basic information editor fields
 */
function createBasicInfoEditor() {
    return `
        <div class="pf-v5-c-form">
            <div class="pf-v5-c-form__group">
                <div class="pf-v5-c-form__group-label">
                    <label class="pf-v5-c-form__label" for="edit-title">
                        <span class="pf-v5-c-form__label-text">Title</span>
                        <span class="pf-v5-c-form__label-required" aria-hidden="true">*</span>
                    </label>
                </div>
                <div class="pf-v5-c-form__group-control">
                    <input class="pf-v5-c-form-control" type="text" id="edit-title" 
                           placeholder="Enter document title..." 
                           onchange="updateMetadataField('title', this.value)"
                           maxlength="200" />
                    <div class="pf-v5-c-form__helper-text pf-v5-u-display-none" id="edit-title-help">
                        <div class="pf-v5-c-helper-text">
                            <div class="pf-v5-c-helper-text__item">
                                <span class="pf-v5-c-helper-text__item-text">Keep titles concise and descriptive</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="pf-v5-c-form__group">
                <div class="pf-v5-c-form__group-label">
                    <label class="pf-v5-c-form__label" for="edit-description">
                        <span class="pf-v5-c-form__label-text">Description</span>
                    </label>
                </div>
                <div class="pf-v5-c-form__group-control">
                    <textarea class="pf-v5-c-form-control description-textarea" id="edit-description" rows="4"
                              placeholder="Brief description of the document content..."
                              onchange="updateMetadataField('description', this.value)"
                              oninput="updateDescriptionCharCount()"
                              maxlength="1000"></textarea>
                    <div class="pf-v5-c-form__helper-text">
                        <div class="pf-v5-c-helper-text">
                            <div class="pf-v5-c-helper-text__item">
                                <span class="pf-v5-c-helper-text__item-text">
                                    <span id="description-char-count">0</span>/1000 characters
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="pf-v5-c-form__group">
                <div class="pf-v5-c-form__group-label">
                    <label class="pf-v5-c-form__label" for="edit-audience">
                        <span class="pf-v5-c-form__label-text">Target Audience</span>
                    </label>
                </div>
                <div class="pf-v5-c-form__group-control">
                    <select class="pf-v5-c-form-control" id="edit-audience" onchange="updateMetadataField('audience', this.value)">
                        <option value="General">General</option>
                        <option value="Beginner">Beginner</option>
                        <option value="Intermediate">Intermediate</option>
                        <option value="Advanced">Advanced</option>
                        <option value="Expert">Expert</option>
                        <option value="Developer">Developer</option>
                        <option value="Admin">Administrator</option>
                        <option value="End User">End User</option>
                    </select>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create classification editor fields  
 */
function createClassificationEditor() {
    return `
        <div class="pf-v5-c-form">
            <div class="pf-v5-c-form__group">
                <div class="pf-v5-c-form__group-label">
                    <label class="pf-v5-c-form__label">
                        <span class="pf-v5-c-form__label-text">Keywords</span>
                    </label>
                </div>
                <div class="pf-v5-c-form__group-control">
                    <div id="keywords-editor">
                        <div id="current-keywords" class="pf-v5-c-chip-group pf-v5-u-mb-sm">
                            <!-- Keywords will be populated here -->
                        </div>
                        <div class="pf-v5-l-flex pf-m-space-items-sm">
                            <input class="pf-v5-c-form-control" type="text" id="new-keyword-input" 
                                   placeholder="Add keyword..." 
                                   onkeypress="handleKeywordInput(event)" />
                            <button class="pf-v5-c-button pf-m-secondary" type="button" onclick="addKeyword()">
                                <i class="fas fa-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="pf-v5-c-form__group">
                <div class="pf-v5-c-form__group-label">
                    <label class="pf-v5-c-form__label">
                        <span class="pf-v5-c-form__label-text">Content Categories</span>
                    </label>
                </div>
                <div class="pf-v5-c-form__group-control">
                    <div id="taxonomy-editor">
                        <div class="pf-v5-c-select pf-m-typeahead">
                            <div class="pf-v5-c-select__toggle">
                                <div class="pf-v5-c-select__toggle-wrapper">
                                    <input class="pf-v5-c-form-control pf-v5-c-select__toggle-typeahead" type="text" 
                                           id="taxonomy-input" placeholder="Select or type category..."
                                           onkeypress="handleTaxonomyInput(event)" />
                                </div>
                                <button class="pf-v5-c-button pf-m-plain pf-v5-c-select__toggle-button" type="button" 
                                        onclick="toggleTaxonomyDropdown()">
                                    <i class="fas fa-caret-down"></i>
                                </button>
                            </div>
                            <div class="pf-v5-c-select__menu" id="taxonomy-dropdown" style="display: none;">
                                ${createTaxonomyOptions()}
                            </div>
                        </div>
                        <div id="current-taxonomy" class="pf-v5-l-flex pf-m-space-items-xs pf-v5-u-mt-sm">
                            <!-- Taxonomy tags will be populated here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create taxonomy dropdown options
 */
function createTaxonomyOptions() {
    const taxonomyOptions = [
        'Troubleshooting',
        'Installation',
        'API_Documentation',
        'Security',
        'Best_Practices',
        'Configuration',
        'Tutorial',
        'Reference',
        'Concept',
        'Procedure'
    ];
    
    return taxonomyOptions.map(option => 
        `<button class="pf-v5-c-select__menu-item" type="button" onclick="selectTaxonomy('${option}')">
            ${option.replace('_', ' ')}
        </button>`
    ).join('');
}

/**
 * Create AI suggestions interface
 */
function createSuggestionsInterface() {
    return `
        <div id="suggestions-content">
            <div class="pf-v5-c-empty-state">
                <div class="pf-v5-c-empty-state__content">
                    <i class="fas fa-magic pf-v5-c-empty-state__icon" aria-hidden="true"></i>
                    <h4 class="pf-v5-c-title pf-m-lg">AI Suggestions</h4>
                    <div class="pf-v5-c-empty-state__body">
                        Click "Get AI Suggestions" to receive intelligent recommendations for improving your metadata.
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create error state for editor
 */
function createEditorErrorState(message) {
    return `
        <div class="pf-v5-c-empty-state">
            <div class="pf-v5-c-empty-state__content">
                <i class="fas fa-exclamation-triangle pf-v5-c-empty-state__icon" aria-hidden="true"></i>
                <h4 class="pf-v5-c-title pf-m-lg">Editor Unavailable</h4>
                <div class="pf-v5-c-empty-state__body">
                    ${message}
                </div>
            </div>
        </div>
    `;
}

/**
 * Initialize event listeners for the editor
 */
function initializeEditorEventListeners() {
    // Character count for description
    const descriptionTextarea = document.getElementById('edit-description');
    if (descriptionTextarea) {
        descriptionTextarea.addEventListener('input', updateDescriptionCharCount);
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        const dropdown = document.getElementById('taxonomy-dropdown');
        const toggle = document.querySelector('.pf-v5-c-select__toggle');
        
        if (dropdown && !toggle.contains(event.target)) {
            dropdown.style.display = 'none';
        }
    });
}

/**
 * Populate editor fields with current metadata
 */
function populateEditorFields() {
    if (!currentEditableMetadata) return;
    
    // Populate basic fields
    const titleInput = document.getElementById('edit-title');
    const descriptionInput = document.getElementById('edit-description');
    const audienceSelect = document.getElementById('edit-audience');
    
    if (titleInput) titleInput.value = currentEditableMetadata.title || '';
    if (descriptionInput) {
        descriptionInput.value = currentEditableMetadata.description || '';
        updateDescriptionCharCount();
    }
    if (audienceSelect) audienceSelect.value = currentEditableMetadata.audience || 'General';
    
    // Populate keywords
    populateKeywords();
    
    // Populate taxonomy
    populateTaxonomy();
}

/**
 * Populate keywords in the editor
 */
function populateKeywords() {
    const keywordsContainer = document.getElementById('current-keywords');
    if (!keywordsContainer || !currentEditableMetadata.keywords) return;
    
    keywordsContainer.innerHTML = currentEditableMetadata.keywords.map(keyword => 
        `<div class="pf-v5-c-chip">
            <span class="pf-v5-c-chip__text">${escapeHtml(keyword)}</span>
            <button class="pf-v5-c-button pf-m-plain pf-v5-c-chip__actions" onclick="removeKeyword('${escapeHtml(keyword)}')">
                <i class="fas fa-times"></i>
            </button>
        </div>`
    ).join('');
}

/**
 * Populate taxonomy in the editor
 */
function populateTaxonomy() {
    const taxonomyContainer = document.getElementById('current-taxonomy');
    if (!taxonomyContainer || !currentEditableMetadata.taxonomy_tags) return;
    
    taxonomyContainer.innerHTML = currentEditableMetadata.taxonomy_tags.map(tag => 
        `<span class="pf-v5-c-label pf-m-blue">
            <span class="pf-v5-c-label__content">
                <i class="fas fa-folder pf-v5-c-label__icon"></i>
                ${escapeHtml(tag)}
            </span>
            <button class="pf-v5-c-button pf-m-plain pf-v5-c-label__actions" onclick="removeTaxonomy('${escapeHtml(tag)}')">
                <i class="fas fa-times"></i>
            </button>
        </span>`
    ).join('');
}

/**
 * Update metadata field value
 */
function updateMetadataField(field, value) {
    if (!currentEditableMetadata) return;
    
    const oldValue = currentEditableMetadata[field];
    currentEditableMetadata[field] = value;
    
    // Record the change for feedback
    recordMetadataChange(field, oldValue, value);
    
    // Update status
    updateEditorStatus('Unsaved changes');
    
    // Trigger any registered callbacks
    metadataChangeCallbacks.forEach(callback => callback(field, value, oldValue));
}

/**
 * Update description character count
 */
function updateDescriptionCharCount() {
    const textarea = document.getElementById('edit-description');
    const counter = document.getElementById('description-char-count');
    
    if (textarea && counter) {
        counter.textContent = textarea.value.length;
    }
}

/**
 * Handle keyword input (Enter key)
 */
function handleKeywordInput(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        addKeyword();
    }
}

/**
 * Add a new keyword
 */
function addKeyword() {
    const input = document.getElementById('new-keyword-input');
    const keyword = input.value.trim();
    
    if (!keyword) return;
    
    // Check for duplicates
    if (currentEditableMetadata.keywords.includes(keyword)) {
        showEditorNotification('Keyword already exists', 'warning');
        input.value = '';
        return;
    }
    
    // Check keyword limit
    if (currentEditableMetadata.keywords.length >= 10) {
        showEditorNotification('Maximum 10 keywords allowed', 'warning');
        input.value = '';
        return;
    }
    
    // Add keyword
    currentEditableMetadata.keywords.push(keyword);
    input.value = '';
    
    // Update display
    populateKeywords();
    
    // Record change
    recordMetadataChange('keywords', 'added', keyword);
    updateEditorStatus('Unsaved changes');
}

/**
 * Remove a keyword
 */
function removeKeyword(keyword) {
    const index = currentEditableMetadata.keywords.indexOf(keyword);
    if (index > -1) {
        currentEditableMetadata.keywords.splice(index, 1);
        populateKeywords();
        recordMetadataChange('keywords', 'removed', keyword);
        updateEditorStatus('Unsaved changes');
    }
}

/**
 * Handle taxonomy input
 */
function handleTaxonomyInput(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        const input = event.target;
        selectTaxonomy(input.value);
    }
}

/**
 * Toggle taxonomy dropdown
 */
function toggleTaxonomyDropdown() {
    const dropdown = document.getElementById('taxonomy-dropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Select a taxonomy
 */
function selectTaxonomy(taxonomy) {
    if (!taxonomy.trim()) return;
    
    // Check for duplicates
    if (currentEditableMetadata.taxonomy_tags.includes(taxonomy)) {
        showEditorNotification('Category already selected', 'warning');
        return;
    }
    
    // Add taxonomy
    currentEditableMetadata.taxonomy_tags.push(taxonomy);
    
    // Update display
    populateTaxonomy();
    
    // Clear input and hide dropdown
    const input = document.getElementById('taxonomy-input');
    const dropdown = document.getElementById('taxonomy-dropdown');
    if (input) input.value = '';
    if (dropdown) dropdown.style.display = 'none';
    
    // Record change
    recordMetadataChange('taxonomy_tags', 'added', taxonomy);
    updateEditorStatus('Unsaved changes');
}

/**
 * Remove a taxonomy
 */
function removeTaxonomy(taxonomy) {
    const index = currentEditableMetadata.taxonomy_tags.indexOf(taxonomy);
    if (index > -1) {
        currentEditableMetadata.taxonomy_tags.splice(index, 1);
        populateTaxonomy();
        recordMetadataChange('taxonomy_tags', 'removed', taxonomy);
        updateEditorStatus('Unsaved changes');
    }
}

/**
 * Save metadata changes
 */
function saveMetadataChanges() {
    if (!currentEditableMetadata) return;
    
    updateEditorStatus('Saving changes...');
    
    // Update the main display with new metadata
    updateMetadataDisplay();
    
    // Record feedback for learning
    recordMetadataFeedback('metadata_updated', currentEditableMetadata);
    
    updateEditorStatus('Changes saved');
    
    // Show success notification
    showEditorNotification('Metadata changes saved successfully!', 'success');
}

/**
 * Revert metadata changes
 */
function revertMetadataChanges() {
    // Extract fresh metadata from display
    currentEditableMetadata = extractMetadataFromDisplay();
    
    // Repopulate fields
    populateEditorFields();
    
    updateEditorStatus('Changes reverted');
    showEditorNotification('Changes reverted to original values', 'info');
}

/**
 * Request AI suggestions
 */
function requestAISuggestions() {
    const suggestionsContainer = document.getElementById('suggestions-content');
    if (!suggestionsContainer) return;
    
    // Show loading state
    suggestionsContainer.innerHTML = `
        <div class="pf-v5-c-spinner pf-m-lg" role="progressbar">
            <span class="pf-v5-c-spinner__clipper"></span>
            <span class="pf-v5-c-spinner__lead-ball"></span>
            <span class="pf-v5-c-spinner__tail-ball"></span>
        </div>
        <p class="pf-v5-u-mt-md">Getting AI suggestions...</p>
    `;
    
    // Simulate AI suggestion request (placeholder for future implementation)
    setTimeout(() => {
        suggestionsContainer.innerHTML = createAISuggestionsResults();
    }, 2000);
}

/**
 * Create AI suggestions results (placeholder)
 */
function createAISuggestionsResults() {
    return `
        <div class="pf-v5-l-stack pf-m-gutter">
            <div class="pf-v5-l-stack__item">
                <h5 class="pf-v5-c-title pf-m-md">Suggested Keywords</h5>
                <div class="pf-v5-c-chip-group">
                    <div class="pf-v5-c-chip">
                        <span class="pf-v5-c-chip__text">documentation</span>
                        <button class="pf-v5-c-button pf-m-plain pf-v5-c-chip__actions" onclick="applySuggestion('keyword', 'documentation')">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                    <div class="pf-v5-c-chip">
                        <span class="pf-v5-c-chip__text">guide</span>
                        <button class="pf-v5-c-button pf-m-plain pf-v5-c-chip__actions" onclick="applySuggestion('keyword', 'guide')">
                            <i class="fas fa-plus"></i>
                        </button>
                    </div>
                </div>
            </div>
            <div class="pf-v5-l-stack__item">
                <h5 class="pf-v5-c-title pf-m-md">Suggested Categories</h5>
                <div class="pf-v5-l-flex pf-m-space-items-xs">
                    <span class="pf-v5-c-label pf-m-outline">
                        <span class="pf-v5-c-label__content">
                            Tutorial
                        </span>
                        <button class="pf-v5-c-button pf-m-plain pf-v5-c-label__actions" onclick="applySuggestion('taxonomy', 'Tutorial')">
                            <i class="fas fa-plus"></i>
                        </button>
                    </span>
                </div>
            </div>
        </div>
    `;
}

/**
 * Apply an AI suggestion
 */
function applySuggestion(type, value) {
    if (type === 'keyword') {
        currentEditableMetadata.keywords.push(value);
        populateKeywords();
    } else if (type === 'taxonomy') {
        currentEditableMetadata.taxonomy_tags.push(value);
        populateTaxonomy();
    }
    
    updateEditorStatus('Unsaved changes');
    showEditorNotification(`Added suggested ${type}: ${value}`, 'success');
}

/**
 * Update the main metadata display with edited values
 */
function updateMetadataDisplay() {
    // This would update the main metadata display
    // For now, we'll just log the changes
    console.log('Updating metadata display with:', currentEditableMetadata);
}

/**
 * Update editor status
 */
function updateEditorStatus(message) {
    const statusElement = document.getElementById('editor-status');
    if (statusElement) {
        statusElement.innerHTML = `<small class="pf-v5-u-color-200">${message}</small>`;
    }
}

/**
 * Show editor notification
 */
function showEditorNotification(message, type = 'info') {
    // Use existing notification system if available
    if (typeof showNotification === 'function') {
        showNotification(message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

/**
 * Record metadata change for feedback learning
 */
function recordMetadataChange(field, oldValue, newValue) {
    // This would integrate with the existing feedback system
    console.log('Metadata change recorded:', { field, oldValue, newValue });
}

/**
 * Record metadata feedback using existing UserFeedback system
 */
async function recordMetadataFeedback(action, metadata) {
    try {
        const response = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                error_type: 'metadata_assistant',
                error_message: `Metadata ${action}`,
                feedback_type: 'correct', // User actively improved metadata
                confidence_score: 0.9,
                user_reason: `User edited metadata: ${JSON.stringify(metadata)}`,
                violation_id: `metadata_edit_${Date.now()}`,
                session_id: window.currentSessionId || 'metadata_session'
            })
        });
        
        if (response.ok) {
            console.log('Metadata feedback recorded successfully');
        }
    } catch (error) {
        console.warn('Failed to record metadata feedback:', error);
    }
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

/**
 * Update description character count
 */
function updateDescriptionCharCount() {
    const textarea = document.getElementById('edit-description');
    const charCount = document.getElementById('description-char-count');
    
    if (textarea && charCount) {
        charCount.textContent = textarea.value.length;
    }
}

// Export functions for global access
window.createInteractiveMetadataEditor = createInteractiveMetadataEditor;
window.updateMetadataField = updateMetadataField;
window.addKeyword = addKeyword;
window.removeKeyword = removeKeyword;
window.selectTaxonomy = selectTaxonomy;
window.removeTaxonomy = removeTaxonomy;
window.toggleTaxonomyDropdown = toggleTaxonomyDropdown;
window.handleKeywordInput = handleKeywordInput;
window.handleTaxonomyInput = handleTaxonomyInput;
window.saveMetadataChanges = saveMetadataChanges;
window.revertMetadataChanges = revertMetadataChanges;
window.requestAISuggestions = requestAISuggestions;
window.updateDescriptionCharCount = updateDescriptionCharCount;
window.applySuggestion = applySuggestion;
