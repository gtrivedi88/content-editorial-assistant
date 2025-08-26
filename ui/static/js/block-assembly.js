/**
 * Block Assembly Line UI Module
 * Creates dynamic assembly line visualization for individual blocks based on their specific errors.
 * Integrates with PatternFly components for consistent styling.
 */

// Global state for block-level rewriting
window.blockRewriteState = {
    currentlyProcessingBlock: null,
    processedBlocks: new Set(),
    blockResults: new Map(), // blockId -> result object
    sessionId: null
};

/**
 * Create dynamic assembly line container based on block errors
 */
function createBlockAssemblyLineContainer(blockId, applicableStations) {
    if (!applicableStations || applicableStations.length === 0) {
        return createNoStationsMessage(blockId);
    }
    
    const stationDisplayNames = {
        'urgent': 'Critical/Legal Pass',
        'high': 'Structural Pass',
        'medium': 'Grammar Pass',
        'low': 'Style Pass'
    };
    
    const stationsHtml = applicableStations.map(station => {
        const displayName = stationDisplayNames[station] || 'Processing Pass';
        return createStationElement(station, displayName);
    }).join('');
    
    return `
        <div class="block-assembly-line pf-v5-u-mt-md" data-block-id="${blockId}">
            <div class="pf-v5-c-card pf-m-compact">
                <div class="pf-v5-c-card__header">
                    <div class="pf-v5-c-card__header-main">
                        <h3 class="pf-v5-c-title pf-m-md">
                            <i class="fas fa-industry pf-v5-u-mr-sm" style="color: #667eea;"></i>
                            AI Assembly Line
                        </h3>
                    </div>
                    <div class="pf-v5-c-card__actions">
                        <span class="assembly-line-status pf-v5-u-font-size-sm pf-v5-u-color-400">
                            Starting processing...
                        </span>
                    </div>
                </div>
                <div class="pf-v5-c-card__body">
                    <!-- Progress indicator -->
                    <div class="pf-v5-c-progress pf-v5-u-mb-md">
                        <div class="pf-v5-c-progress__description">
                            <span class="pf-v5-c-progress__measure">
                                <span class="progress-percent">0%</span>
                            </span>
                        </div>
                        <div class="pf-v5-c-progress__bar" style="width: 0%;"></div>
                    </div>
                    
                    <!-- Assembly line stations -->
                    <div class="assembly-line-stations pf-v5-l-stack pf-m-gutter">
                        ${stationsHtml}
                    </div>
                </div>
                <div class="pf-v5-c-card__footer">
                    <small class="pf-v5-u-color-400">
                        <i class="fas fa-info-circle pf-v5-u-mr-xs"></i>
                        Processing only the stations needed for this block's specific errors
                    </small>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create individual station element
 */
function createStationElement(station, displayName) {
    return `
        <div class="pf-v5-l-stack__item">
            <div class="dynamic-station station-waiting" data-station="${station}">
                <div class="pf-v5-l-flex pf-m-align-items-center">
                    <div class="pf-v5-l-flex__item">
                        <i class="station-status-icon fas fa-clock pf-v5-u-mr-sm"></i>
                    </div>
                    <div class="pf-v5-l-flex__item pf-m-flex-1">
                        <span class="pf-v5-u-font-weight-bold">${displayName}</span>
                        <div class="station-status-text pf-v5-u-font-size-sm pf-v5-u-color-400">
                            Waiting...
                        </div>
                    </div>
                    <div class="pf-v5-l-flex__item">
                        <span class="station-priority-badge pf-v5-c-label pf-m-outline pf-m-${getStationColor(station)}">
                            <span class="pf-v5-c-label__content">${getStationPriority(station)}</span>
                        </span>
                    </div>
                </div>
                <div class="station-preview pf-v5-u-mt-xs pf-v5-u-font-size-sm pf-v5-u-color-300" style="display: none;">
                    <!-- Preview text will be inserted here during processing -->
                </div>
            </div>
        </div>
    `;
}

/**
 * Get color class for station based on priority
 */
function getStationColor(station) {
    const colorMap = {
        'urgent': 'red',
        'high': 'orange', 
        'medium': 'gold',
        'low': 'blue'
    };
    return colorMap[station] || 'grey';
}

/**
 * Get priority label for station
 */
function getStationPriority(station) {
    const priorityMap = {
        'urgent': 'Critical',
        'high': 'High',
        'medium': 'Medium', 
        'low': 'Low'
    };
    return priorityMap[station] || 'Normal';
}

/**
 * Create message when no stations are needed
 */
function createNoStationsMessage(blockId) {
    return `
        <div class="block-assembly-line pf-v5-u-mt-md" data-block-id="${blockId}">
            <div class="pf-v5-c-empty-state pf-m-sm">
                <div class="pf-v5-c-empty-state__content">
                    <i class="fas fa-check-circle pf-v5-c-empty-state__icon" style="color: #28a745;"></i>
                    <h3 class="pf-v5-c-title pf-m-md">Block is clean</h3>
                    <div class="pf-v5-c-empty-state__body">
                        No assembly line processing needed for this block.
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create block results card
 */
function createBlockResultsCard(blockId, result) {
    const errorCount = result.errors_fixed || 0;
    const confidence = result.confidence || 0;
    const rewrittenText = result.rewritten_text || '';
    const processingTime = result.processing_time || 0;
    
    return `
        <div class="block-results-card pf-v5-u-mt-md" data-block-id="${blockId}">
            <div class="pf-v5-c-card pf-m-compact">
                <div class="pf-v5-c-card__header">
                    <div class="pf-v5-c-card__header-main">
                        <h3 class="pf-v5-c-title pf-m-md">
                            <i class="fas fa-magic pf-v5-u-mr-sm" style="color: #28a745;"></i>
                            Improved Text
                        </h3>
                    </div>
                    <div class="pf-v5-c-card__actions">
                        <div class="pf-v5-l-flex pf-m-space-items-sm">
                            <div class="pf-v5-l-flex__item">
                                <span class="pf-v5-c-label pf-m-green">
                                    <span class="pf-v5-c-label__content">
                                        <i class="fas fa-check-circle pf-v5-c-label__icon"></i>
                                        ${errorCount} Fixed
                                    </span>
                                </span>
                            </div>
                            <div class="pf-v5-l-flex__item">
                                <span class="pf-v5-c-label pf-m-outline pf-m-blue">
                                    <span class="pf-v5-c-label__content">
                                        ${Math.round(confidence * 100)}% Confidence
                                    </span>
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="pf-v5-c-card__body">
                    <div class="pf-v5-c-code-block">
                        <div class="pf-v5-c-code-block__header">
                            <div class="pf-v5-c-code-block__header-main">
                                <span class="pf-v5-c-code-block__title">Improved Content</span>
                            </div>
                            <div class="pf-v5-c-code-block__actions">
                                <button class="pf-v5-c-button pf-m-plain pf-m-small copy-block-button" 
                                        onclick="copyBlockText('${blockId}', '${escapeForAttribute(rewrittenText)}')"
                                        title="Copy improved text">
                                    <i class="fas fa-copy" aria-hidden="true"></i>
                                </button>
                            </div>
                        </div>
                        <div class="pf-v5-c-code-block__content">
                            <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; word-wrap: break-word;"><code class="pf-v5-c-code-block__code">${escapeHtml(rewrittenText)}</code></pre>
                        </div>
                    </div>
                </div>
                <div class="pf-v5-c-card__footer">
                    <div class="pf-v5-l-flex pf-m-justify-content-center">
                        <div class="pf-v5-l-flex__item">
                            <button class="copy-text-button pf-v5-c-button pf-m-primary pf-m-block" 
                                    onclick="copyBlockTextToClipboard('${blockId}', '${escapeForAttribute(rewrittenText)}')">
                                <i class="fas fa-copy pf-v5-u-mr-sm"></i>
                                Copy Improved Text
                            </button>
                        </div>
                    </div>
                    <div class="pf-v5-u-mt-sm pf-v5-u-text-align-center">
                        <small class="pf-v5-u-color-400">
                            <i class="fas fa-clock pf-v5-u-mr-xs"></i>
                            Processed in ${processingTime.toFixed(1)}s
                        </small>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create block error card
 */
function createBlockErrorCard(blockId, errorMessage) {
    return `
        <div class="block-error-card pf-v5-u-mt-md" data-block-id="${blockId}">
            <div class="pf-v5-c-alert pf-m-danger">
                <div class="pf-v5-c-alert__icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <h4 class="pf-v5-c-alert__title">Block Processing Failed</h4>
                <div class="pf-v5-c-alert__description">
                    ${escapeHtml(errorMessage)}
                </div>
                <div class="pf-v5-c-alert__action">
                    <button class="pf-v5-c-button pf-m-link pf-m-inline" 
                            onclick="retryBlockRewrite('${blockId}')">
                        Try Again
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Copy block text to clipboard with user feedback
 */
function copyBlockTextToClipboard(blockId, text) {
    // Decode the escaped text
    const decodedText = decodeAttribute(text);
    
    navigator.clipboard.writeText(decodedText).then(() => {
        // Show success feedback
        showCopySuccessMessage(blockId);
    }).catch(err => {
        console.error('Failed to copy text:', err);
        // Fallback: show text in a modal for manual copying
        showTextModal('Copy Improved Text', decodedText);
    });
}

/**
 * Show copy success message
 */
function showCopySuccessMessage(blockId) {
    const button = document.querySelector(`[data-block-id="${blockId}"] .copy-text-button`);
    if (!button) return;
    
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-check pf-v5-u-mr-sm"></i>Copied!';
    button.classList.remove('pf-m-primary');
    button.classList.add('pf-m-success');
    
    setTimeout(() => {
        button.innerHTML = originalText;
        button.classList.remove('pf-m-success');
        button.classList.add('pf-m-primary');
    }, 2000);
}

/**
 * Retry block rewrite
 */
function retryBlockRewrite(blockId) {
    // Remove error card
    const errorCard = document.querySelector(`[data-block-id="${blockId}"].block-error-card`);
    if (errorCard) {
        errorCard.remove();
    }
    
    // Get block type from button
    const blockElement = document.getElementById(blockId);
    const rewriteButton = blockElement ? blockElement.querySelector('.block-rewrite-button') : null;
    const blockType = rewriteButton ? rewriteButton.dataset.blockType : 'paragraph';
    
    // Retry the rewrite
    rewriteBlock(blockId, blockType);
}

/**
 * Utility function to escape text for HTML attributes
 */
function escapeForAttribute(text) {
    return text
        .replace(/\\/g, '\\\\')
        .replace(/'/g, "\\'")
        .replace(/"/g, '\\"')
        .replace(/\n/g, '\\n')
        .replace(/\r/g, '\\r')
        .replace(/\t/g, '\\t');
}

/**
 * Utility function to decode escaped attribute text
 */
function decodeAttribute(text) {
    return text
        .replace(/\\'/g, "'")
        .replace(/\\"/g, '"')
        .replace(/\\n/g, '\n')
        .replace(/\\r/g, '\r')
        .replace(/\\t/g, '\t')
        .replace(/\\\\/g, '\\');
}

/**
 * Store current structural blocks for later reference
 */
function storeCurrentStructuralBlocks(blocks) {
    window.currentStructuralBlocks = blocks;
}

/**
 * Get block data by ID (enhanced version)
 */
function getBlockDataById(blockId) {
    if (window.currentStructuralBlocks) {
        const blockIndex = parseInt(blockId.replace('block-', ''));
        return window.currentStructuralBlocks[blockIndex] || null;
    }
    return null;
}

/**
 * Show text in a modal for manual copying (fallback)
 */
function showTextModal(title, text) {
    // Create modal dynamically
    const modal = document.createElement('div');
    modal.className = 'pf-v5-c-backdrop';
    modal.innerHTML = `
        <div class="pf-v5-c-modal-box pf-m-lg">
            <div class="pf-v5-c-modal-box__header">
                <h1 class="pf-v5-c-modal-box__title">${title}</h1>
                <div class="pf-v5-c-modal-box__description">
                    Select all text below and copy manually
                </div>
            </div>
            <div class="pf-v5-c-modal-box__body">
                <textarea class="pf-v5-c-form-control" rows="10" readonly style="width: 100%;">${text}</textarea>
            </div>
            <div class="pf-v5-c-modal-box__footer">
                <button class="pf-v5-c-button pf-m-primary" onclick="this.closest('.pf-v5-c-backdrop').remove()">Close</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Auto-select text
    const textarea = modal.querySelector('textarea');
    textarea.select();
    
    // Remove modal when clicking backdrop
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
}

// Initialize global state when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Initialize block rewrite state
    window.blockRewriteState = {
        currentlyProcessingBlock: null,
        processedBlocks: new Set(),
        blockResults: new Map(),
        sessionId: window.sessionId || null
    };
    
    console.log('📦 Block Assembly Line module initialized');
});
