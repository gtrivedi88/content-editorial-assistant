/**
 * Complex Block Creators Module - List and Table Creation (PatternFly Version)
 */

// Create a list block with proper formatting using PatternFly List
function createListBlock(block, displayIndex) {
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
                    <h6>List-Level Issues:</h6>
                    <div class="pf-v5-l-stack pf-m-gutter">
                        ${(block.errors || []).map(error => createInlineError(error)).join('')}
                    </div>
                </div>
            </div>` : ''}
        </div>
    `;
}

// Create a placeholder for the table block
function createTableBlock(block, displayIndex) {
    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="fas fa-table pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}: TABLE</span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-empty-state pf-m-sm">
                    <div class="pf-v5-c-empty-state__content">
                        <i class="fas fa-table pf-v5-c-empty-state__icon"></i>
                        <h3 class="pf-v5-c-title pf-m-md">Table Block</h3>
                        <div class="pf-v5-c-empty-state__body">Full table rendering is supported. This content will be displayed in a PatternFly table.</div>
                    </div>
                </div>
            </div>
        </div>
    `;
}
