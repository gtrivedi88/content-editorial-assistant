// Global variables
let currentAnalysis = null;
let currentContent = null;
let socket = null;
let sessionId = null;

// Initialize application when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeTooltips();
    initializeFileHandlers();
    initializeInteractivity();
});

// Initialize tooltips
function initializeTooltips() {
    // Check if Bootstrap is available (some pages may not have it)
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } else {
        // Fallback: Use PatternFly-style tooltips if Bootstrap is not available
        const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"], [title]');
        tooltipElements.forEach(function(element) {
            if (element.hasAttribute('title') && !element.hasAttribute('data-tooltip-initialized')) {
                element.setAttribute('data-tooltip-initialized', 'true');
                
                element.addEventListener('mouseenter', function() {
                    const tooltipText = this.getAttribute('title') || this.getAttribute('data-bs-title');
                    if (!tooltipText) return;
                    
                    const tooltip = document.createElement('div');
                    tooltip.className = 'pf-v5-c-tooltip';
                    tooltip.textContent = tooltipText;
                    tooltip.style.position = 'absolute';
                    tooltip.style.background = 'rgba(0,0,0,0.8)';
                    tooltip.style.color = 'white';
                    tooltip.style.padding = '0.5rem';
                    tooltip.style.borderRadius = '4px';
                    tooltip.style.fontSize = '0.875rem';
                    tooltip.style.zIndex = '9999';
                    tooltip.style.pointerEvents = 'none';
                    tooltip.style.maxWidth = '200px';
                    tooltip.style.wordWrap = 'break-word';
                    
                    document.body.appendChild(tooltip);
                    
                    const rect = this.getBoundingClientRect();
                    tooltip.style.left = rect.left + 'px';
                    tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
                    
                    this._tooltip = tooltip;
                });
                
                element.addEventListener('mouseleave', function() {
                    if (this._tooltip) {
                        this._tooltip.remove();
                        this._tooltip = null;
                    }
                });
            }
        });
    }
}

// Initialize file upload handlers
function initializeFileHandlers() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const textInput = document.getElementById('text-input');

    if (uploadArea && fileInput) {
        // Drag and drop functionality
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
                hideSampleSection();
            }
        });

        // File input change handler
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
                hideSampleSection();
            }
        });

        // Clear text input when file is selected
        fileInput.addEventListener('change', () => {
            if (textInput) textInput.value = '';
        });
    }

    if (textInput) {
        // Clear file input when text is entered
        textInput.addEventListener('input', () => {
            if (fileInput) fileInput.value = '';
        });

        // Auto-resize textarea
        textInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    }
}

// Initialize interactive elements
function initializeInteractivity() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Direct text analysis
function analyzeDirectText() {
    const textInput = document.getElementById('text-input');
    if (!textInput) return;

    const text = textInput.value.trim();
    if (!text) {
        alert('Please enter some text to analyze');
        return;
    }

    currentContent = text;
    analyzeContent(text);
    hideSampleSection();
}

// Sample text analysis
function analyzeSampleText() {
    const sampleText = `The implementation of the new system was facilitated by the team in order to optimize performance metrics. Due to the fact that the previous system was inefficient, a large number of users were experiencing difficulties. The decision was made by management to utilize advanced technologies for the purpose of enhancing user experience and improving overall system reliability.`;
    
    currentContent = sampleText;
    analyzeContent(sampleText);
    hideSampleSection();
}

// Hide sample section when analysis starts
function hideSampleSection() {
    const sampleSection = document.getElementById('sample-section');
    if (sampleSection) {
        sampleSection.style.display = 'none';
    }
}



// NEW BLOCK-LEVEL REWRITING FUNCTIONS

/**
 * Rewrite a single structural block
 */
function rewriteBlock(blockId, blockType) {
    console.log(`🤖 Starting block rewrite for ${blockId} (${blockType})`);
    
    const block = findBlockById(blockId);
    if (!block || !block.errors || block.errors.length === 0) {
        console.warn('Block not found or has no errors:', blockId);
        return;
    }
    
    // Update block state to processing
    updateBlockCardToProcessing(blockId);
    
    // Show dynamic assembly line based on block errors
    displayBlockAssemblyLine(blockId, block.errors);
    
    // Call new API endpoint
    fetch('/rewrite-block', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            block_content: block.content,
            block_errors: block.errors,
            block_type: blockType,
            block_id: blockId,
            session_id: sessionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayBlockResults(blockId, data);
        } else {
            showBlockError(blockId, data.error || 'Block rewrite failed');
        }
    })
    .catch(error => {
        console.error('Block rewrite error:', error);
        showBlockError(blockId, 'Failed to rewrite block');
    });
}

/**
 * Find block data by block ID
 */
function findBlockById(blockId) {
    // Extract block index from ID (e.g., "block-0" -> 0)
    const blockIndex = parseInt(blockId.replace('block-', ''));
    
    // Get block data from current analysis or stored data
    if (window.currentStructuralBlocks && window.currentStructuralBlocks[blockIndex]) {
        return window.currentStructuralBlocks[blockIndex];
    }
    
    // Fallback: extract from DOM
    const blockElement = document.getElementById(blockId);
    if (!blockElement) return null;
    
    // Extract block content and metadata from DOM
    const contentElement = blockElement.querySelector('.pf-v5-u-background-color-200');
    const content = contentElement ? contentElement.textContent.trim() : '';
    const blockType = blockElement.dataset.blockType || 'paragraph';
    
    // Extract error information from DOM (simplified version)
    const errorElements = blockElement.querySelectorAll('.error-item');
    const errors = Array.from(errorElements).map(el => ({
        type: el.dataset.errorType || 'unknown',
        flagged_text: el.dataset.flaggedText || ''
    }));
    
    return { content, block_type: blockType, errors };
}

/**
 * Display dynamic assembly line for a specific block
 */
function displayBlockAssemblyLine(blockId, blockErrors) {
    // Get applicable stations for this block's errors
    const applicableStations = getApplicableStationsFromErrors(blockErrors);
    
    // Create assembly line UI container
    const assemblyLineContainer = createBlockAssemblyLineContainer(blockId, applicableStations);
    
    // Insert after the block element
    const blockElement = document.getElementById(blockId);
    if (blockElement) {
        // Remove any existing assembly line
        const existingAssemblyLine = blockElement.nextElementSibling;
        if (existingAssemblyLine && existingAssemblyLine.classList.contains('block-assembly-line')) {
            existingAssemblyLine.remove();
        }
        
        // Insert new assembly line
        blockElement.insertAdjacentHTML('afterend', assemblyLineContainer);
    }
}

/**
 * Display results for a completed block rewrite
 */
function displayBlockResults(blockId, result) {
    console.log(`✅ Block rewrite completed for ${blockId}:`, result);
    
    // Remove assembly line UI
    removeBlockAssemblyLine(blockId);
    
    // Create results card
    const resultsCard = createBlockResultsCard(blockId, result);
    
    // Insert results after the block element
    const blockElement = document.getElementById(blockId);
    if (blockElement) {
        blockElement.insertAdjacentHTML('afterend', resultsCard);
        
        // Update block card to show completion
        updateBlockCardToComplete(blockId, result.errors_fixed || 0);
    }
}

/**
 * Show error for a block rewrite failure
 */
function showBlockError(blockId, errorMessage) {
    console.error(`❌ Block rewrite failed for ${blockId}:`, errorMessage);
    
    // Remove assembly line UI
    removeBlockAssemblyLine(blockId);
    
    // Show error message
    const errorCard = createBlockErrorCard(blockId, errorMessage);
    
    const blockElement = document.getElementById(blockId);
    if (blockElement) {
        blockElement.insertAdjacentHTML('afterend', errorCard);
        
        // Reset block card state
        updateBlockCardToError(blockId);
    }
}

/**
 * Update block card visual state to processing
 */
function updateBlockCardToProcessing(blockId) {
    const blockElement = document.getElementById(blockId);
    if (!blockElement) return;
    
    const button = blockElement.querySelector('.block-rewrite-button');
    if (button) {
        button.disabled = true;
        button.innerHTML = '🔄 Processing...';
        button.classList.add('pf-m-in-progress');
    }
    
    // Add processing indicator
    blockElement.classList.add('block-processing');
}

/**
 * Update block card visual state to completed
 */
function updateBlockCardToComplete(blockId, errorsFixed) {
    const blockElement = document.getElementById(blockId);
    if (!blockElement) return;
    
    const button = blockElement.querySelector('.block-rewrite-button');
    if (button) {
        button.innerHTML = `✅ Fixed ${errorsFixed} Issue${errorsFixed !== 1 ? 's' : ''}`;
        button.classList.remove('pf-m-in-progress');
        button.classList.add('pf-m-success');
        button.disabled = false;
    }
    
    // Update status indicator
    const statusLabel = blockElement.querySelector('.pf-v5-c-label');
    if (statusLabel) {
        statusLabel.className = 'pf-v5-c-label pf-m-outline pf-m-green';
        statusLabel.innerHTML = '<span class="pf-v5-c-label__content">Improved</span>';
    }
    
    blockElement.classList.remove('block-processing');
    blockElement.classList.add('block-completed');
}

/**
 * Update block card visual state to error
 */
function updateBlockCardToError(blockId) {
    const blockElement = document.getElementById(blockId);
    if (!blockElement) return;
    
    const button = blockElement.querySelector('.block-rewrite-button');
    if (button) {
        button.disabled = false;
        button.innerHTML = button.innerHTML.replace('🔄 Processing...', 'Retry');
        button.classList.remove('pf-m-in-progress');
    }
    
    blockElement.classList.remove('block-processing');
    blockElement.classList.add('block-error');
}

/**
 * Get applicable stations from error list
 */
function getApplicableStationsFromErrors(errors) {
    if (!errors || errors.length === 0) return [];
    
    const stationsNeeded = new Set();
    
    errors.forEach(error => {
        const priority = getErrorPriority(error.type);
        if (priority === 'urgent') stationsNeeded.add('urgent');
        else if (priority === 'high') stationsNeeded.add('high');
        else if (priority === 'medium') stationsNeeded.add('medium');
        else if (priority === 'low') stationsNeeded.add('low');
    });
    
    // Return in priority order
    const priorityOrder = ['urgent', 'high', 'medium', 'low'];
    return priorityOrder.filter(station => stationsNeeded.has(station));
}

/**
 * Remove assembly line UI for a block
 */
function removeBlockAssemblyLine(blockId) {
    const blockElement = document.getElementById(blockId);
    if (!blockElement) return;
    
    const assemblyLineElement = blockElement.nextElementSibling;
    if (assemblyLineElement && assemblyLineElement.classList.contains('block-assembly-line')) {
        assemblyLineElement.remove();
    }
}



// Refine content function (Pass 2)
function refineContent(firstPassResult) {
    // Use the global currentRewrittenContent if no parameter provided
    const contentToRefine = firstPassResult || window.currentRewrittenContent;
    
    if (!contentToRefine || !currentAnalysis) {
        alert('No first pass result available');
        return;
    }

    showLoading('rewrite-results', 'Refining with AI Pass 2...');

    fetch('/refine', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            first_pass_result: contentToRefine,
            original_errors: currentAnalysis.errors || [],
            session_id: sessionId 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayRefinementResults(data);
        } else {
            showError('rewrite-results', data.error || 'Refinement failed');
        }
    })
    .catch(error => {
        console.error('Refinement error:', error);
        showError('rewrite-results', 'Refinement failed: ' + error.message);
    });
} 