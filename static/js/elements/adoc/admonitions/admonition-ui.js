/**
 * AsciiDoc Admonition Element UI Module
 * Handles rendering of NOTE, TIP, WARNING, IMPORTANT, CAUTION blocks
 */

/**
 * Create an admonition block display
 * @param {Object} block - The admonition block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the admonition block
 */
function createAdmonitionBlock(block, displayIndex) {
    const admonitionType = block.admonition_type || 'NOTE';
    const issueCount = block.errors ? block.errors.length : 0;
    const status = issueCount > 0 ? 'red' : 'green';
    const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';

    // Admonition-specific styling
    const admonitionConfig = {
        'NOTE': { icon: 'fas fa-info-circle', color: 'blue', label: 'Note' },
        'TIP': { icon: 'fas fa-lightbulb', color: 'green', label: 'Tip' },
        'IMPORTANT': { icon: 'fas fa-exclamation-circle', color: 'orange', label: 'Important' },
        'WARNING': { icon: 'fas fa-exclamation-triangle', color: 'gold', label: 'Warning' },
        'CAUTION': { icon: 'fas fa-radiation', color: 'red', label: 'Caution' }
    };

    const config = admonitionConfig[admonitionType] || admonitionConfig['NOTE'];

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="${config.icon} pf-v5-u-mr-sm" style="color: var(--pf-v5-global--${config.color}--Color--100);"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">Admonition (${config.label})</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">${statusText}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-alert pf-m-${config.color} pf-m-inline" style="margin-bottom: 1rem;">
                    <div class="pf-v5-c-alert__icon">
                        <i class="${config.icon}"></i>
                    </div>
                    <div class="pf-v5-c-alert__title">
                        <h3 class="pf-v5-c-title pf-m-md">${config.label}</h3>
                    </div>
                </div>
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
function canHandleAdmonition(block) {
    return block.block_type === 'admonition';
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createAdmonitionBlock,
        canHandleAdmonition
    };
} 