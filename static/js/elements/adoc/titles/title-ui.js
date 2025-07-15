/**
 * AsciiDoc Title/Heading Element UI Module
 * Handles rendering of document titles and section headings
 */

/**
 * Create a title/heading block display
 * @param {Object} block - The title block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the title block
 */
function createTitleBlock(block, displayIndex) {
    const level = block.level || 1;
    const levelText = level === 0 ? 'Document Title' : `Level ${level} Heading`;
    const icon = level === 0 ? 'fas fa-file-text' : 'fas fa-heading';
    
    const issueCount = block.errors ? block.errors.length : 0;
    const status = issueCount > 0 ? 'red' : 'green';
    const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="${icon} pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">${levelText}</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">${statusText}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-u-p-md pf-v5-u-background-color-200" style="white-space: pre-wrap; word-wrap: break-word; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                    ${level === 0 ? '= ' : '='.repeat(level + 1) + ' '}${escapeHtml(block.content)}
                </div>
            </div>
            ${issueCount > 0 ? `
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
function canHandleTitle(block) {
    return block.block_type === 'heading' || block.block_type === 'title';
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createTitleBlock,
        canHandleTitle
    };
} 