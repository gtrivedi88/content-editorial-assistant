/**
 * AsciiDoc Elements
 * Contains only essential list and table functionality
 */

/**
 * Create a list block display with clean bullets/numbers
 */
function createListBlockElement(block, displayIndex) {
    const isOrdered = block.block_type === 'olist';
    let totalIssues = block.errors ? block.errors.length : 0;
    
    // Recursively count issues in all nested children
    const countNestedIssues = (children) => {
        if (!children) return;
        children.forEach(item => {
            if (item.errors) totalIssues += item.errors.length;
            if (item.children) countNestedIssues(item.children);
        });
    };
    
    if (block.children) {
        countNestedIssues(block.children);
    }
    
    const status = totalIssues > 0 ? 'red' : 'green';
    const statusText = totalIssues > 0 ? `${totalIssues} Issue(s)` : 'Clean';

    const generateListItems = (items) => {
        if (!items || items.length === 0) return '';
        return items.map(item => {
            let content = escapeHtml(item.content);
            
            // Handle nested lists if this item has children
            let nestedContent = '';
            if (item.children && item.children.length > 0) {
                item.children.forEach(child => {
                    if (child.block_type === 'olist' || child.block_type === 'ulist') {
                        const isChildOrdered = child.block_type === 'olist';
                        nestedContent += `
                            <${isChildOrdered ? 'ol' : 'ul'}>
                                ${generateListItems(child.children)}
                            </${isChildOrdered ? 'ol' : 'ul'}>
                        `;
                    }
                });
            }
            
            return `
                <li>
                    ${content}
                    ${nestedContent}
                    ${item.errors && item.errors.length > 0 ? `
                        <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-ml-lg pf-v5-u-mt-sm">
                            ${item.errors.map(error => createInlineError(error)).join('')}
                        </div>
                    ` : ''}
                </li>
            `;
        }).join('');
    };

    // Separate list structure errors from item errors for better display
    const listStructureErrors = block.errors ? block.errors.filter(error => 
        error.type === 'lists' || error.error_type === 'lists' || 
        error.type === 'structure' || error.error_type === 'structure'
    ) : [];

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
                <div class="pf-v5-c-content">
                    <${isOrdered ? 'ol' : 'ul'}>
                        ${generateListItems(block.children)}
                    </${isOrdered ? 'ol' : 'ul'}>
                </div>
            </div>
            ${listStructureErrors.length > 0 ? `
            <div class="pf-v5-c-card__footer">
                <div class="pf-v5-c-content">
                    <h3 class="pf-v5-c-title pf-m-md">List Structure Issues:</h3>
                    <div class="pf-v5-l-stack pf-m-gutter">
                        ${listStructureErrors.map(error => createInlineError(error)).join('')}
                    </div>
                </div>
            </div>` : ''}
        </div>
    `;
}

/**
 * Create a table block display with proper HTML table structure
 */
function createTableBlockElement(block, displayIndex, allBlocks = []) {
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    // Find all table cell blocks that belong to this table
    // They will be the next blocks in sequence until we hit a non-table_cell block
    const tableCells = [];
    for (let i = displayIndex + 1; i < allBlocks.length; i++) {
        if (allBlocks[i].block_type === 'table_cell') {
            tableCells.push(allBlocks[i]);
        } else {
            break; // Stop when we hit a non-table_cell block
        }
    }

    
    // Calculate total issues including table cell errors
    let totalIssues = block.errors ? block.errors.length : 0;
    tableCells.forEach(cell => {
        if (cell.errors) totalIssues += cell.errors.length;
    });
    
    const status = totalIssues > 0 ? 'red' : 'green';
    const statusText = totalIssues > 0 ? `${totalIssues} Issue(s)` : 'Clean';
    
    // Extract table content and parse it into rows and cells
    const tableHtml = parseTableContent(block);
    
    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top app-card" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <div class="pf-v5-l-flex pf-m-align-items-center">
                        <div class="pf-v5-l-flex__item">
                            <div class="pf-v5-l-flex pf-m-align-items-center pf-m-justify-content-center" style="
                                width: 40px;
                                height: 40px;
                                background: linear-gradient(135deg, var(--app-success-color) 0%, rgba(62, 134, 53, 0.8) 100%);
                                border-radius: var(--pf-v5-global--BorderRadius--lg);
                                color: white;
                            ">
                                <i class="fas fa-table" style="font-size: 18px;"></i>
                            </div>
                        </div>
                        <div class="pf-v5-l-flex__item pf-v5-u-ml-md">
                            <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-xs">
                                BLOCK ${displayIndex + 1}: ${blockTitle}
                            </h3>
                            <p class="pf-v5-u-font-size-sm pf-v5-u-color-200 pf-v5-u-mb-0">
                                ${block.title ? block.title : 'Data Table'} • ${totalIssues} ${totalIssues === 1 ? 'issue' : 'issues'} found
                            </p>
                        </div>
                    </div>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">
                            <i class="fas fa-${totalIssues > 0 ? 'exclamation-triangle' : 'check-circle'} pf-v5-c-label__icon"></i>
                            ${statusText}
                        </span>
                    </span>
                </div>
            </div>
            
            <div class="pf-v5-c-card__body">
                ${block.title ? `
                    <div class="pf-v5-u-mb-lg">
                        <div class="pf-v5-c-card pf-m-plain" style="
                            background: linear-gradient(135deg, rgba(0, 102, 204, 0.03) 0%, rgba(0, 64, 128, 0.05) 100%);
                            border: 1px solid var(--pf-v5-global--BorderColor--100);
                        ">
                            <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                                <h4 class="pf-v5-c-title pf-m-lg">${escapeHtml(block.title)}</h4>
                            </div>
                        </div>
                    </div>
                ` : ''}
                
                <div class="pf-v5-c-card pf-m-plain" style="
                    background: var(--pf-v5-global--BackgroundColor--100);
                    border: 1px solid var(--pf-v5-global--BorderColor--100);
                    border-radius: var(--pf-v5-global--BorderRadius--sm);
                    overflow: hidden;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                ">
                    <div style="overflow-x: auto;">
                        ${tableHtml}
                    </div>
                </div>
                
                ${totalIssues > 0 ? `
                <div class="pf-v5-u-mt-lg">
                    <div class="pf-v5-c-card pf-m-plain">
                        <div class="pf-v5-c-card__header">
                            <div class="pf-v5-c-card__header-main">
                                <h4 class="pf-v5-c-title pf-m-md">
                                    <i class="fas fa-exclamation-triangle pf-v5-u-mr-sm" style="color: var(--app-danger-color);"></i>
                                    ${totalIssues} Issue${totalIssues > 1 ? 's' : ''} Found
                                </h4>
                            </div>
                        </div>
                        <div class="pf-v5-c-card__body">
                            <div class="pf-v5-l-stack pf-m-gutter">
                                ${(block.errors || []).map(error => createInlineError(error)).join('')}
                                ${tableCells.filter(cell => cell.errors && cell.errors.length > 0).map(cell => `
                                    <div class="pf-v5-c-alert pf-m-inline pf-m-info pf-v5-u-mb-sm">
                                        <div class="pf-v5-c-alert__icon">
                                            <i class="fas fa-table" aria-hidden="true"></i>
                                        </div>
                                        <div class="pf-v5-c-alert__title">
                                            <span class="pf-v5-u-font-size-sm">In table cell: "${escapeHtml(cell.content)}"</span>
                                        </div>
                                        <div class="pf-v5-c-alert__description">
                                            ${(cell.errors || []).map(error => `
                                                <div class="pf-v5-c-helper-text pf-m-error pf-v5-u-mb-sm">
                                                    <div class="pf-v5-c-helper-text__item pf-m-error">
                                                        <span class="pf-v5-c-helper-text__item-icon">
                                                            <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
                                                        </span>
                                                        <span class="pf-v5-c-helper-text__item-text">
                                                            <strong>${error.rule_id || 'Style'}:</strong> ${error.message || error.text || 'Style issue detected'}
                                                        </span>
                                                    </div>
                                                </div>
                                            `).join('')}
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

/**
 * Parse table content - simplified version that covers the main cases
 */
function parseTableContent(block) {
    // If the block has raw content that looks like AsciiDoc table format
    if (block.raw_content && block.raw_content.includes('|===')) {
        return parseAsciiDocTable(block.raw_content);
    }
    
    // If the block has children (table rows and cells from parser)
    if (block.children && block.children.length > 0) {
        return parseStructuredTable(block.children);
    }
    
    // Fallback: try to parse content as simple table
    if (block.content) {
        return parseSimpleTable(block.content);
    }
    
    // Final fallback
    return `
        <div class="pf-v5-c-empty-state pf-m-lg">
            <div class="pf-v5-c-empty-state__content">
                <i class="fas fa-table pf-v5-c-empty-state__icon"></i>
                <h2 class="pf-v5-c-title pf-m-lg">Table Content</h2>
                <div class="pf-v5-c-empty-state__body">
                    <div class="pf-v5-c-code-block">
                        <div class="pf-v5-c-code-block__content">
                            <pre class="pf-v5-c-code-block__pre"><code class="pf-v5-c-code-block__code">${escapeHtml(block.content || 'No content')}</code></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Parse AsciiDoc table format
 */
function parseAsciiDocTable(rawContent) {
    try {
        const tableMatch = rawContent.match(/\|===\s*([\s\S]*?)\s*\|===/);
        if (!tableMatch) return parseSimpleTable(rawContent);
        
        const tableContent = tableMatch[1].trim();
        const lines = tableContent.split('\n').filter(line => line.trim() !== '');
        
        let rows = [];
        let currentRow = [];
        
        for (let line of lines) {
            line = line.trim();
            if (line.startsWith('|')) {
                if (currentRow.length > 0) {
                    rows.push(currentRow);
                    currentRow = [];
                }
                const cells = line.split('|').slice(1).map(cell => cell.trim());
                currentRow = cells;
            } else if (line !== '') {
                if (currentRow.length > 0) {
                    currentRow[currentRow.length - 1] += ' ' + line;
                }
            }
        }
        
        if (currentRow.length > 0) {
            rows.push(currentRow);
        }
        
        return generatePatternFlyTable(rows, true);
    } catch (error) {
        console.error('Error parsing AsciiDoc table:', error);
        return parseSimpleTable(rawContent);
    }
}

/**
 * Parse structured table from children blocks
 */
function parseStructuredTable(children) {
    const rows = [];
    
    for (const child of children) {
        if (child.block_type === 'table_row' && child.children) {
            const cells = child.children
                .filter(cell => cell.block_type === 'table_cell')
                .map(cell => cell.content || '');
            if (cells.length > 0) {
                rows.push(cells);
            }
        }
    }
    
    return generatePatternFlyTable(rows, true);
}

/**
 * Parse simple table format (fallback)
 */
function parseSimpleTable(content) {
    if (!content) {
        return `<div class="pf-v5-c-empty-state pf-m-sm">
            <div class="pf-v5-c-empty-state__content">
                <i class="fas fa-table pf-v5-c-empty-state__icon"></i>
                <h3 class="pf-v5-c-title pf-m-md">No Table Content</h3>
                <div class="pf-v5-c-empty-state__body">No table content available.</div>
            </div>
        </div>`;
    }
    
    // Show as formatted text if not clearly a table
    return `
        <div class="pf-v5-c-code-block">
            <div class="pf-v5-c-code-block__header">
                <div class="pf-v5-c-code-block__header-main">
                    <span class="pf-v5-c-code-block__title">Table Content</span>
                </div>
            </div>
            <div class="pf-v5-c-code-block__content">
                <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap;"><code class="pf-v5-c-code-block__code">${escapeHtml(content)}</code></pre>
            </div>
        </div>
    `;
}

/**
 * Generate PatternFly HTML table from rows array
 */
function generatePatternFlyTable(rows, hasHeader = false) {
    if (rows.length === 0) {
        return `<div class="pf-v5-c-empty-state pf-m-sm">
            <div class="pf-v5-c-empty-state__content">
                <i class="fas fa-table pf-v5-c-empty-state__icon"></i>
                <h3 class="pf-v5-c-title pf-m-md">No Table Data</h3>
                <div class="pf-v5-c-empty-state__body">No table data available.</div>
            </div>
        </div>`;
    }
    
    let html = `<table class="pf-v5-c-table pf-m-compact pf-m-grid-md pf-m-striped" role="grid" style="
        border: 1px solid var(--pf-v5-global--BorderColor--100);
        border-radius: var(--pf-v5-global--BorderRadius--sm);
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    ">`;
    
    // Generate header if specified
    if (hasHeader && rows.length > 0) {
        html += '<thead>';
        html += '<tr role="row">';
        for (const cell of rows[0]) {
            html += `<th class="pf-v5-c-table__th" role="columnheader" scope="col" style="
                background: linear-gradient(135deg, var(--pf-v5-global--palette--blue-100) 0%, var(--pf-v5-global--palette--blue-200) 100%);
                font-weight: var(--pf-v5-global--FontWeight--bold);
                color: var(--pf-v5-global--palette--blue-700);
                border-bottom: 2px solid var(--pf-v5-global--palette--blue-300);
                padding: var(--pf-v5-global--spacer--md);
                text-align: left;
            ">${escapeHtml(cell)}</th>`;
        }
        html += '</tr>';
        html += '</thead>';
        
        rows = rows.slice(1);
    }
    
    // Generate body rows
    html += '<tbody role="rowgroup">';
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        const isEvenRow = i % 2 === 0;
        html += `<tr role="row" style="
            background-color: ${isEvenRow ? 'var(--pf-v5-global--BackgroundColor--100)' : 'var(--pf-v5-global--BackgroundColor--200)'};
            transition: background-color 0.2s ease;
        " onmouseover="this.style.backgroundColor='var(--pf-v5-global--palette--blue-50)'" 
           onmouseout="this.style.backgroundColor='${isEvenRow ? 'var(--pf-v5-global--BackgroundColor--100)' : 'var(--pf-v5-global--BackgroundColor--200)'}'"
        >`;
        for (const cell of row) {
            html += `<td class="pf-v5-c-table__td" role="gridcell" style="
                padding: var(--pf-v5-global--spacer--md);
                border-bottom: 1px solid var(--pf-v5-global--BorderColor--100);
                vertical-align: top;
                line-height: 1.5;
            ">${escapeHtml(cell)}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody>';
    
    html += '</table>';
    return html;
}

/**
 * Simplified block creation - replaces the complex modular system
 */
function createStructuralBlock(block, displayIndex, allBlocks = []) {
    // Handle lists and tables with specialized rendering
    if (block.block_type === 'olist' || block.block_type === 'ulist') {
        return createListBlockElement(block, displayIndex);
    }
    
    if (block.block_type === 'table') {
        return createTableBlockElement(block, displayIndex, allBlocks);
    }
    
    // Handle sections  
    if (block.block_type === 'section') {
        return createSectionBlockElement(block, displayIndex);
    }
    
    // Skip sub-elements that shouldn't be displayed separately
    if (['list_item', 'list_title', 'table_row', 'table_cell'].includes(block.block_type)) {
        return '';
    }
    
    // Default handling for other block types
    const blockTypeIcons = {
        'heading': 'fas fa-heading', 'paragraph': 'fas fa-paragraph', 'admonition': 'fas fa-info-circle',
        'listing': 'fas fa-code', 'literal': 'fas fa-terminal', 'quote': 'fas fa-quote-left', 'sidebar': 'fas fa-columns',
        'example': 'fas fa-lightbulb', 'verse': 'fas fa-feather', 'attribute_entry': 'fas fa-cog', 'comment': 'fas fa-comment',
        'image': 'fas fa-image', 'audio': 'fas fa-music', 'video': 'fas fa-video'
    };
    const icon = blockTypeIcons[block.block_type] || 'fas fa-file-alt';
    const blockTitle = getBlockTypeDisplayName(block.block_type, { level: block.level, admonition_type: block.admonition_type });
    const issueCount = block.errors ? block.errors.length : 0;
    const status = block.should_skip_analysis ? 'grey' : issueCount > 0 ? 'red' : 'green';
    const statusText = block.should_skip_analysis ? 'Skipped' : issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="${icon} pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">${blockTitle}</span>
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
                             <h3 class="pf-v5-c-title pf-m-md">Code blocks are intentionally not analyzed for style issues.</h3>
                             <div class="pf-v5-c-empty-state__body">Code blocks and attributes are not analyzed for style issues.</div>
                        </div>
                    </div>` :
                    `<div class="pf-v5-u-p-md pf-v5-u-background-color-200" style="white-space: pre-wrap; word-wrap: break-word; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                        ${escapeHtml(block.content)}
                    </div>`
                }
            </div>
            ${block.errors && block.errors.length > 0 ? `
            <div class="pf-v5-c-card__footer">
                <div class="pf-v5-c-content">
                    <h3 class="pf-v5-c-title pf-m-md">Issues:</h3>
                    <div class="pf-v5-l-stack pf-m-gutter">
                        ${block.errors.map(error => createInlineError(error)).join('')}
                    </div>
                </div>
            </div>` : ''}
        </div>
    `;
}

/**
 * Create a section block (which contains other cards)
 */
function createSectionBlockElement(block, displayIndex) {
    let totalIssues = block.errors ? block.errors.length : 0;
    
    // Count issues in all children recursively
    const countChildIssues = (children) => {
        if (!children) return;
        children.forEach(child => {
            if (child.errors) totalIssues += child.errors.length;
            if (child.children) countChildIssues(child.children);
        });
    };
    countChildIssues(block.children);

    // Generate HTML for child blocks
    let childDisplayIndex = 0;
    const childrenHtml = block.children ? block.children.map(child => {
        const html = createStructuralBlock(child, childDisplayIndex);
        if (html) childDisplayIndex++;
        return html;
    }).filter(html => html).join('') : '';

    const status = totalIssues > 0 ? 'red' : 'green';
    const statusText = totalIssues > 0 ? `${totalIssues} Issue(s)` : 'Clean';

    return `
        <div class="pf-v5-c-card pf-m-bordered pf-m-expandable">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="fas fa-layer-group pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">SECTION ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">${getBlockTypeDisplayName(block.block_type, { level: block.level })}</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">${statusText}</span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-l-stack pf-m-gutter">
                    ${childrenHtml}
                </div>
            </div>
        </div>
    `;
}