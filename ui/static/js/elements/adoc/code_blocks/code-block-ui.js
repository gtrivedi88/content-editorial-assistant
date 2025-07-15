/**
 * AsciiDoc Code Block Element UI Module
 * Handles rendering of listing and literal code blocks
 */

/**
 * Create a code block display
 * @param {Object} block - The code block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the code block
 */
function createCodeBlockElement(block, displayIndex) {
    const isListing = block.block_type === 'listing';
    const blockTypeDisplay = isListing ? 'Code Listing' : 'Literal Block';
    const icon = isListing ? 'fas fa-code' : 'fas fa-terminal';
    
    const issueCount = block.errors ? block.errors.length : 0;
    const status = block.should_skip_analysis ? 'grey' : issueCount > 0 ? 'red' : 'green';
    const statusText = block.should_skip_analysis ? 'Skipped' : issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="${icon} pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">${blockTypeDisplay}</span>
                    ${block.language ? `<span class="pf-v5-c-label pf-m-compact pf-v5-u-ml-sm">${block.language}</span>` : ''}
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">${statusText}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                ${block.should_skip_analysis ?
                    `<div class="pf-v5-c-empty-state pf-m-sm">
                        <div class="pf-v5-c-empty-state__content">
                             <i class="fas fa-ban pf-v5-c-empty-state__icon"></i>
                             <h3 class="pf-v5-c-title pf-m-md">Analysis Skipped</h3>
                             <div class="pf-v5-c-empty-state__body">Code blocks are not analyzed for style issues.</div>
                        </div>
                    </div>` :
                    `<div class="pf-v5-u-p-md" style="background-color: #f8f8f8; border: 1px solid #e0e0e0; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                        <pre style="margin: 0; white-space: pre-wrap; word-wrap: break-word; font-family: 'Courier New', monospace;"><code>${escapeHtml(block.content)}</code></pre>
                    </div>`
                }
            </div>
            ${!block.should_skip_analysis && issueCount > 0 ? `
            <div class="pf-v5-c-card__footer">
                <div class="pf-v5-l-stack pf-m-gutter">
                    ${(block.errors || []).map(error => createInlineError(error)).join('')}
                </div>
            </div>` : ''}
        </div>
    `;
}

/**
 * Check if this module can handle the given block type
 * @param {Object} block - Block to check
 * @returns {boolean} True if this module can handle the block
 */
function canHandleCodeBlock(block) {
    return block.block_type === 'listing' || block.block_type === 'literal';
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createCodeBlockElement,
        canHandleCodeBlock
    };
} 