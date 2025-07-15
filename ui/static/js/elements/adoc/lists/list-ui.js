/**
 * AsciiDoc List Element UI Module
 * Handles rendering of ordered and unordered lists
 */

/**
 * Create a list block display
 * @param {Object} block - The list block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the list block
 */
function createListBlockElement(block, displayIndex) {
    const isOrdered = block.block_type === 'ordered_list';
    let totalIssues = block.errors ? block.errors.length : 0;
    if (block.children) {
        block.children.forEach(item => {
            if (item.errors) totalIssues += item.errors.length;
        });
    }
    const status = totalIssues > 0 ? 'red' : 'green';
    const statusText = totalIssues > 0 ? `${totalIssues} Issue(s)` : 'Clean';

    const generateListItems = (items) => {
        if (!items || items.length === 0) return '';
        return items.map(item => `
            <li class="pf-v5-c-list__item">
                ${escapeHtml(item.content)}
                ${item.errors && item.errors.length > 0 ? `
                    <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-ml-lg pf-v5-u-mt-sm">
                        ${item.errors.map(error => createInlineError(error)).join('')}
                    </div>
                ` : ''}
            </li>
        `).join('');
    };

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                     <i class="fas fa-list-${isOrdered ? 'ol' : 'ul'} pf-v5-u-mr-sm"></i>
                     <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                     <span class="pf-v5-u-ml-sm">${getBlockTypeDisplayName(block.block_type, {})}</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">${statusText}</span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <${isOrdered ? 'ol' : 'ul'} class="pf-v5-c-list">
                    ${generateListItems(block.children)}
                </${isOrdered ? 'ol' : 'ul'}>
            </div>
            ${block.errors && block.errors.length > 0 ? `
            <div class="pf-v5-c-card__footer">
                <div class="pf-v5-c-content">
                    <h3 class="pf-v5-c-title pf-m-md">List Structure Issues:</h3>
                    <div class="pf-v5-l-stack pf-m-gutter">
                        ${block.errors.map(error => createInlineError(error)).join('')}
                    </div>
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
function canHandleList(block) {
    return block.block_type === 'ordered_list' || block.block_type === 'unordered_list';
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createListBlockElement,
        canHandleList
    };
} 