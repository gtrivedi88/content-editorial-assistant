/**
 * AsciiDoc Paragraph Element UI Module
 * Handles rendering of regular text paragraphs
 */

/**
 * Create a paragraph block display
 * @param {Object} block - The paragraph block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the paragraph block
 */
function createParagraphBlock(block, displayIndex) {
    const issueCount = block.errors ? block.errors.length : 0;
    const status = issueCount > 0 ? 'red' : 'green';
    const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="fas fa-paragraph pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">Paragraph</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">${statusText}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-u-p-md pf-v5-u-background-color-200" style="white-space: pre-wrap; word-wrap: break-word; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                    ${escapeHtml(block.content)}
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
function canHandleParagraph(block) {
    return block.block_type === 'paragraph';
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createParagraphBlock,
        canHandleParagraph
    };
} 