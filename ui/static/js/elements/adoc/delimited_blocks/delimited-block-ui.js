/**
 * AsciiDoc Delimited Block Element UI Module
 * Handles rendering of quote, sidebar, example, and verse blocks
 */

/**
 * Create a delimited block display
 * @param {Object} block - The delimited block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the delimited block
 */
function createDelimitedBlockElement(block, displayIndex) {
    const blockType = block.block_type;
    const issueCount = block.errors ? block.errors.length : 0;
    const status = issueCount > 0 ? 'red' : 'green';
    const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';

    // Block-specific configuration
    const blockConfig = {
        'quote': {
            icon: 'fas fa-quote-left',
            title: 'Quote Block',
            color: 'blue',
            style: 'border-left: 4px solid var(--pf-v5-global--primary-color--100); padding-left: 1rem; font-style: italic;'
        },
        'sidebar': {
            icon: 'fas fa-columns',
            title: 'Sidebar',
            color: 'purple',
            style: 'background-color: #f5f5f5; border: 1px solid #ddd; padding: 1rem; border-radius: var(--pf-v5-global--BorderRadius--sm);'
        },
        'example': {
            icon: 'fas fa-lightbulb',
            title: 'Example Block',
            color: 'green',
            style: 'background-color: #f0f8f0; border: 1px solid #d4e6d4; padding: 1rem; border-radius: var(--pf-v5-global--BorderRadius--sm);'
        },
        'verse': {
            icon: 'fas fa-feather',
            title: 'Verse Block',
            color: 'gold',
            style: 'font-family: serif; line-height: 1.6; white-space: pre-line; font-style: italic;'
        }
    };

    const config = blockConfig[blockType] || blockConfig['quote'];

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="${config.icon} pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">${config.title}</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">${statusText}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-u-p-md" style="${config.style}">
                    ${blockType === 'quote' ? `
                        <blockquote class="pf-v5-u-mb-0">
                            ${escapeHtml(block.content)}
                            ${block.attribution ? `<footer class="pf-v5-u-mt-sm pf-v5-u-font-size-sm">— ${escapeHtml(block.attribution)}</footer>` : ''}
                        </blockquote>
                    ` : `
                        <div style="white-space: pre-wrap; word-wrap: break-word;">
                            ${escapeHtml(block.content)}
                        </div>
                    `}
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
function canHandleDelimitedBlock(block) {
    return ['quote', 'sidebar', 'example', 'verse'].includes(block.block_type);
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createDelimitedBlockElement,
        canHandleDelimitedBlock
    };
} 