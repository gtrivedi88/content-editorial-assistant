/**
 * AsciiDoc Section Element UI Module
 * Handles rendering of document sections (containers for other blocks)
 */

/**
 * Create a section block display
 * @param {Object} block - The section block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the section block
 */
function createSectionBlockElement(block, displayIndex) {
    let totalIssues = block.errors ? block.errors.length : 0;
    const countChildIssues = (children) => {
        if (!children) return;
        children.forEach(child => {
            if (child.errors) totalIssues += child.errors.length;
            if (child.children) countChildIssues(child.children);
        });
    };
    countChildIssues(block.children);
    
    const status = totalIssues > 0 ? 'red' : 'green';
    const statusText = totalIssues > 0 ? `${totalIssues} Issue(s)` : 'Clean';
    const childCount = block.children ? block.children.length : 0;

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="fas fa-folder-open pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">Section</span>
                    <span class="pf-v5-c-label pf-m-compact pf-v5-u-ml-sm">${childCount} block${childCount !== 1 ? 's' : ''}</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">${statusText}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                ${block.content ? `
                    <div class="pf-v5-u-p-md pf-v5-u-background-color-200 pf-v5-u-mb-md" style="white-space: pre-wrap; word-wrap: break-word; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                        <strong>Section Title:</strong> ${escapeHtml(block.content)}
                    </div>
                ` : ''}
                
                ${childCount > 0 ? `
                    <div class="pf-v5-c-expandable-section" data-ouia-component-type="PF5/ExpandableSection">
                        <button class="pf-v5-c-expandable-section__toggle" type="button" aria-expanded="false">
                            <span class="pf-v5-c-expandable-section__toggle-icon">
                                <i class="fas fa-angle-right" aria-hidden="true"></i>
                            </span>
                            <span class="pf-v5-c-expandable-section__toggle-text">Show ${childCount} nested block${childCount !== 1 ? 's' : ''}</span>
                        </button>
                        <div class="pf-v5-c-expandable-section__content" hidden>
                            <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-ml-lg">
                                <!-- Child blocks would be rendered here -->
                                <p class="pf-v5-u-color-200">Nested blocks: ${childCount} total</p>
                            </div>
                        </div>
                    </div>
                ` : `
                    <div class="pf-v5-c-empty-state pf-m-sm">
                        <div class="pf-v5-c-empty-state__content">
                            <i class="fas fa-folder pf-v5-c-empty-state__icon"></i>
                            <h3 class="pf-v5-c-title pf-m-md">Empty Section</h3>
                            <div class="pf-v5-c-empty-state__body">This section contains no blocks.</div>
                        </div>
                    </div>
                `}
            </div>
            ${totalIssues > 0 ? `
            <div class="pf-v5-c-card__footer">
                <div class="pf-v5-l-stack pf-m-gutter">
                    ${(block.errors || []).map(error => createInlineError(error)).join('')}
                    ${totalIssues > (block.errors?.length || 0) ? `
                        <div class="pf-v5-c-alert pf-m-info pf-m-inline">
                            <div class="pf-v5-c-alert__icon">
                                <i class="fas fa-info-circle"></i>
                            </div>
                            <div class="pf-v5-c-alert__title">
                                Additional issues found in nested blocks
                            </div>
                        </div>
                    ` : ''}
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
function canHandleSection(block) {
    return block.block_type === 'section';
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createSectionBlockElement,
        canHandleSection
    };
} 