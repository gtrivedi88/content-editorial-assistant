/**
 * AsciiDoc Procedure Element UI Module
 * Handles rendering of numbered procedure steps and workflows
 */

/**
 * Create a procedure block display
 * @param {Object} block - The procedure block data
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the procedure block
 */
function createProcedureBlockElement(block, displayIndex) {
    const issueCount = block.errors ? block.errors.length : 0;
    const status = issueCount > 0 ? 'red' : 'green';
    const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';
    const stepCount = block.children ? block.children.length : 0;

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="fas fa-list-ol pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">Procedure</span>
                    <span class="pf-v5-c-label pf-m-compact pf-v5-u-ml-sm">${stepCount} step${stepCount !== 1 ? 's' : ''}</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">${statusText}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                ${block.title ? `
                    <div class="pf-v5-u-p-md pf-v5-u-background-color-200 pf-v5-u-mb-md" style="border-radius: var(--pf-v5-global--BorderRadius--sm);">
                        <h4 class="pf-v5-c-title pf-m-md pf-v5-u-mb-0">
                            <i class="fas fa-clipboard-list pf-v5-u-mr-sm"></i>
                            ${escapeHtml(block.title)}
                        </h4>
                    </div>
                ` : ''}
                
                ${stepCount > 0 ? `
                    <ol class="pf-v5-c-list pf-m-plain" style="counter-reset: step-counter;">
                        ${generateProcedureSteps(block.children)}
                    </ol>
                ` : `
                    <div class="pf-v5-c-empty-state pf-m-sm">
                        <div class="pf-v5-c-empty-state__content">
                            <i class="fas fa-clipboard pf-v5-c-empty-state__icon"></i>
                            <h3 class="pf-v5-c-title pf-m-md">Empty Procedure</h3>
                            <div class="pf-v5-c-empty-state__body">This procedure contains no steps.</div>
                        </div>
                    </div>
                `}
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
 * Generate HTML for procedure steps
 * @param {Array} steps - Array of step objects
 * @returns {string} HTML string for procedure steps
 */
function generateProcedureSteps(steps) {
    if (!steps || steps.length === 0) return '';
    
    return steps.map((step, index) => {
        const stepNumber = index + 1;
        const hasErrors = step.errors && step.errors.length > 0;
        
        return `
            <li class="pf-v5-c-list__item pf-v5-u-mb-md" style="
                counter-increment: step-counter;
                position: relative;
                padding-left: 3rem;
                border-left: 3px solid var(--pf-v5-global--primary-color--100);
                margin-left: 1rem;
            ">
                <div class="procedure-step-number" style="
                    position: absolute;
                    left: -1.5rem;
                    top: 0;
                    width: 2rem;
                    height: 2rem;
                    background: var(--pf-v5-global--primary-color--100);
                    color: white;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: bold;
                    font-size: 0.875rem;
                ">
                    ${stepNumber}
                </div>
                <div class="procedure-step-content" style="min-height: 2rem; display: flex; align-items: flex-start;">
                    <div class="pf-v5-u-flex-grow-1">
                        <div style="white-space: pre-wrap; word-wrap: break-word;">
                            ${escapeHtml(step.content)}
                        </div>
                        ${hasErrors ? `
                            <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-mt-sm">
                                ${step.errors.map(error => createInlineError(error)).join('')}
                            </div>
                        ` : ''}
                    </div>
                </div>
            </li>
        `;
    }).join('');
}

/**
 * Check if this module can handle the given block type
 * @param {Object} block - Block to check
 * @returns {boolean} True if this module can handle the block
 */
function canHandleProcedure(block) {
    return block.block_type === 'procedure' || 
           (block.block_type === 'ordered_list' && block.is_procedure === true);
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createProcedureBlockElement,
        generateProcedureSteps,
        canHandleProcedure
    };
} 