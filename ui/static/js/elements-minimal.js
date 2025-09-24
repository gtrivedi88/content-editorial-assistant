/**
 * AsciiDoc Elements
 * Contains only essential list and table functionality
 */

/**
 * Decode HTML entities to regular characters
 */
function decodeHtmlEntities(text) {
    if (typeof text !== 'string') return text;
    
    // Check if style-helpers.js is loaded and has this function
    if (typeof window.decodeHtmlEntities === 'function' && window.decodeHtmlEntities !== decodeHtmlEntities) {
        return window.decodeHtmlEntities(text);
    }
    
    // Create a temporary element to decode HTML entities
    const tempElement = document.createElement('div');
    tempElement.innerHTML = text;
    let decoded = tempElement.textContent || tempElement.innerText || '';
    
    // Fallback manual decoding for common problematic entities
    const entityMap = {
        '&#8217;': "'",  // Right single quotation mark (curly apostrophe)
        '&#8216;': "'",  // Left single quotation mark
        '&#8220;': '"',  // Left double quotation mark
        '&#8221;': '"',  // Right double quotation mark
        '&#8211;': '–',  // En dash
        '&#8212;': '—',  // Em dash
        '&#8230;': '…',  // Horizontal ellipsis
        '&rsquo;': "'",  // Right single quotation mark
        '&lsquo;': "'",  // Left single quotation mark
        '&rdquo;': '"',  // Right double quotation mark
        '&ldquo;': '"',  // Left double quotation mark
        '&ndash;': '–',  // En dash
        '&mdash;': '—',  // Em dash
        '&hellip;': '…' // Horizontal ellipsis
    };
    
    // Apply manual decoding as fallback
    Object.keys(entityMap).forEach(entity => {
        const char = entityMap[entity];
        decoded = decoded.replace(new RegExp(entity, 'g'), char);
    });
    
    return decoded;
}

/**
 * Safe HTML renderer for table cells - allows common formatting tags
 * This function allows <code> tags and other safe formatting to be rendered properly
 */
function renderSafeTableCellHtml(text) {
    if (!text) return '';
    
    // Check if style-helpers.js is loaded and has this function
    if (typeof window.renderSafeTableCellHtml === 'function' && window.renderSafeTableCellHtml !== renderSafeTableCellHtml) {
        return window.renderSafeTableCellHtml(text);
    }
    
    // First decode HTML entities to get clean text (fixes &#8217; etc.)
    text = decodeHtmlEntities(text);
    
    // Then escape all HTML to be safe
    let escaped = escapeHtml(text);
    
    // Finally selectively un-escape safe formatting tags
    const safeTagsMap = {
        '&lt;code&gt;': '<code style="background: rgba(14, 184, 166, 0.1); color: #0d9488; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">',
        '&lt;/code&gt;': '</code>',
        '&lt;strong&gt;': '<strong>',
        '&lt;/strong&gt;': '</strong>',
        '&lt;em&gt;': '<em>',
        '&lt;/em&gt;': '</em>',
        '&lt;b&gt;': '<strong>',
        '&lt;/b&gt;': '</strong>',
        '&lt;i&gt;': '<em>',
        '&lt;/i&gt;': '</em>'
    };
    
    // Replace escaped safe tags with their HTML equivalents
    Object.keys(safeTagsMap).forEach(escapedTag => {
        const htmlTag = safeTagsMap[escapedTag];
        escaped = escaped.replace(new RegExp(escapedTag, 'gi'), htmlTag);
    });
    
    return escaped;
}

/**
 * Create a list block display with clean bullets/numbers
 */
function createListBlockElement(block, displayIndex) {
    const isOrdered = block.block_type === 'olist';
    let totalIssues = block.errors ? block.errors.length : 0;
    
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
            let content = renderSafeTableCellHtml(item.content);
            
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
                    // **NEW**: Render nested description lists
                    else if (child.block_type === 'dlist') {
                        nestedContent += createDescriptionListBlockElement(child, -1); // -1 index to signify nested
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
 * **NEW**: Create a description list block display.
 * This function renders a definition list (<dl>) with terms (<dt>) and descriptions (<dd>).
 */
function createDescriptionListBlockElement(block, displayIndex) {
    let totalIssues = block.errors ? block.errors.length : 0;

    // Recursively count issues in all children (term/description items)
    const countNestedIssues = (children) => {
        if (!children) return;
        children.forEach(item => {
            if (item.errors) totalIssues += item.errors.length;
            // Description items can have nested lists themselves
            if (item.children) countNestedIssues(item.children);
        });
    };
    
    if (block.children) {
        countNestedIssues(block.children);
    }
    
    const status = totalIssues > 0 ? 'red' : 'green';
    const statusText = totalIssues > 0 ? `${totalIssues} Issue(s)` : 'Clean';

    // This function generates the <dt> and <dd> pairs.
    const generateListItems = (items) => {
        if (!items || items.length === 0) return '';
        return items.map(item => {
            // The item itself is a 'description_list_item' block
            const term = renderSafeTableCellHtml(item.term || '');
            const description = renderSafeTableCellHtml(item.description || '');

            // Separate errors for the term and the description
            const termErrors = (item.errors || []).filter(e => e.structural_context && e.structural_context.is_dlist_term);
            const descErrors = (item.errors || []).filter(e => e.structural_context && e.structural_context.is_dlist_description);

            return `
                <dt>
                    ${term}
                    ${termErrors.length > 0 ? `
                        <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-mt-sm">
                            ${termErrors.map(error => createInlineError(error)).join('')}
                        </div>
                    ` : ''}
                </dt>
                <dd>
                    ${description}
                    ${descErrors.length > 0 ? `
                        <div class="pf-v5-l-stack pf-m-gutter pf-v5-u-mt-sm">
                            ${descErrors.map(error => createInlineError(error)).join('')}
                        </div>
                    ` : ''}
                </dd>
            `;
        }).join('');
    };
    
    // Errors that apply to the list structure as a whole (e.g., parallelism)
    const listStructureErrors = block.errors || [];

    // If displayIndex is -1, it's a nested list, so render without the main card wrapper.
    if (displayIndex === -1) {
        return `
            <dl class="pf-v5-c-description-list">
                ${generateListItems(block.children)}
            </dl>
        `;
    }

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                     <i class="fas fa-book pf-v5-u-mr-sm"></i>
                     <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                     <span class="pf-v5-u-ml-sm">${getBlockTypeDisplayName(block.block_type, {})}</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">${statusText}</span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-content">
                    <dl class="pf-v5-c-description-list">
                        ${generateListItems(block.children)}
                    </dl>
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
    
    const tableCells = [];
    for (let i = displayIndex + 1; i < allBlocks.length; i++) {
        if (allBlocks[i].block_type === 'table_cell') {
            tableCells.push(allBlocks[i]);
        } else {
            break; 
        }
    }

    let totalIssues = block.errors ? block.errors.length : 0;
    tableCells.forEach(cell => {
        if (cell.errors) totalIssues += cell.errors.length;
    });
    
    const status = totalIssues > 0 ? 'red' : 'green';
    const statusText = totalIssues > 0 ? `${totalIssues} Issue(s)` : 'Clean';
    
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
                                            <span class="pf-v5-u-font-size-sm">In table cell: "${renderSafeTableCellHtml(cell.content)}"</span>
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
    if (block.raw_content && block.raw_content.includes('|===')) {
        return parseAsciiDocTable(block.raw_content);
    }
    
    if (block.children && block.children.length > 0) {
        return parseStructuredTable(block.children);
    }
    
    if (block.content) {
        return parseSimpleTable(block.content);
    }
    
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
            ">${renderSafeTableCellHtml(cell)}</th>`;
        }
        html += '</tr>';
        html += '</thead>';
        
        rows = rows.slice(1);
    }
    
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
            ">${renderSafeTableCellHtml(cell)}</td>`;
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
    // **FIX**: Route different list types to their specific rendering functions.
    if (block.block_type === 'olist' || block.block_type === 'ulist') {
        return createListBlockElement(block, displayIndex);
    }
    if (block.block_type === 'dlist') {
        return createDescriptionListBlockElement(block, displayIndex);
    }
    
    if (block.block_type === 'table') {
        return createTableBlockElement(block, displayIndex, allBlocks);
    }
    
    if (block.block_type === 'section') {
        return createSectionBlockElement(block, displayIndex);
    }
    
    // Skip sub-elements that are rendered by their parents.
    if (['list_item', 'description_list_item', 'table_row', 'table_cell'].includes(block.block_type)) {
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
    
    // Enhanced status calculation with priority levels
    const priority = getBlockPriority(block.errors);
    const status = block.should_skip_analysis ? 'grey' : priority === 'red' ? 'red' : priority === 'yellow' ? 'orange' : 'green';
    const statusText = block.should_skip_analysis ? 'Skipped' : issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';
    const priorityIcon = getPriorityIcon(priority);
    
    // Generate error summary and rewrite button
    const errorSummary = issueCount > 0 ? summarizeBlockErrors(block.errors) : '';
    const rewriteButton = generateBlockRewriteButton(block, displayIndex, priority);

    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top block-priority-${priority}" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="${icon} pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">${blockTitle}</span>
                    ${priorityIcon}
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
                        ${renderSafeTableCellHtml(block.content)}
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
                    <div class="pf-v5-u-mt-md">
                        ${rewriteButton}
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
    
    const countChildIssues = (children) => {
        if (!children) return;
        children.forEach(child => {
            if (child.errors) totalIssues += child.errors.length;
            if (child.children) countChildIssues(child.children);
        });
    };
    countChildIssues(block.children);

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

// Block-Level Rewriting Helper Functions

/**
 * Determine block priority based on error types
 */
function getBlockPriority(errors) {
    if (!errors || errors.length === 0) return 'green';
    
    // Map error types to priority levels
    const priorities = errors.map(error => getErrorPriority(error.type));
    
    if (priorities.includes('urgent')) return 'red';
    if (priorities.includes('high') || priorities.includes('medium')) return 'yellow';
    return 'green';
}

/**
 * Get error priority level for a specific error type
 */
function getErrorPriority(errorType) {
    // Handle wildcard patterns
    if (errorType.startsWith('word_usage_')) return 'medium';
    if (errorType.startsWith('punctuation_')) return 'low';
    if (errorType.startsWith('technical_')) return 'medium';
    if (errorType.startsWith('references_')) return 'low';
    
    // Explicit mapping based on assembly line configuration
    const priorityMap = {
        // URGENT (Red priority)
        'legal_claims': 'urgent',
        'legal_company_names': 'urgent',
        'legal_personal_information': 'urgent',
        'inclusive_language': 'urgent',
        'second_person': 'urgent',
        
        // HIGH (Yellow priority)
        'passive_voice': 'high',
        'sentence_length': 'high',
        'subjunctive_mood': 'high',
        'verbs': 'high',
        'headings': 'high',
        
        // MEDIUM (Yellow priority)
        'contractions': 'medium',
        'spelling': 'medium',
        'terminology': 'medium',
        'anthropomorphism': 'medium',
        'capitalization': 'medium',
        'prefixes': 'medium',
        'plurals': 'medium',
        'abbreviations': 'medium',
        
        // LOW (Green priority)
        'tone': 'low',
        'citations': 'low',
        'ambiguity': 'low',
        'currency': 'low'
    };
    
    return priorityMap[errorType] || 'medium';
}

/**
 * Get priority icon for visual indicators
 */
function getPriorityIcon(priority) {
    switch (priority) {
        case 'red':
            return '<i class="fas fa-exclamation-triangle pf-v5-u-ml-sm" style="color: #dc3545;" title="Critical issues"></i>';
        case 'yellow':
            return '<i class="fas fa-exclamation-circle pf-v5-u-ml-sm" style="color: #ffc107;" title="High/Medium priority issues"></i>';
        case 'green':
            return '<i class="fas fa-check-circle pf-v5-u-ml-sm" style="color: #28a745;" title="Clean or low priority"></i>';
        default:
            return '';
    }
}

/**
 * Create a summary of block errors for quick overview
 */
function summarizeBlockErrors(errors) {
    if (!errors || errors.length === 0) return '';
    
    const errorCounts = {};
    errors.forEach(error => {
        const category = categorizeError(error.type);
        errorCounts[category] = (errorCounts[category] || 0) + 1;
    });
    
    const summaryParts = Object.entries(errorCounts).map(([category, count]) => 
        `${count} ${category}${count > 1 ? ' issues' : ' issue'}`
    );
    
    return summaryParts.join(', ');
}

/**
 * Categorize error types for summary display
 */
function categorizeError(errorType) {
    if (errorType.includes('legal') || errorType === 'second_person' || errorType === 'inclusive_language') {
        return 'legal/critical';
    }
    if (errorType === 'passive_voice' || errorType === 'sentence_length' || errorType === 'verbs') {
        return 'structural';
    }
    if (errorType.startsWith('word_usage_') || errorType === 'contractions' || errorType === 'spelling') {
        return 'grammar';
    }
    if (errorType.startsWith('punctuation_') || errorType === 'tone') {
        return 'style';
    }
    return 'other';
}

/**
 * Generate contextual rewrite button for blocks with errors
 */
function generateBlockRewriteButton(block, displayIndex, priority) {
    // Don't show button for blocks without errors or skipped blocks
    if (!block.errors || block.errors.length === 0 || block.should_skip_analysis) {
        return '';
    }
    
    const errorCount = block.errors.length;
    const buttonText = priority === 'red' 
        ? `🚨 Fix ${errorCount} Critical Issue${errorCount > 1 ? 's' : ''}`
        : `🤖 Improve ${errorCount} Issue${errorCount > 1 ? 's' : ''}`;
    
    const buttonClass = priority === 'red' ? 'pf-m-danger' : 'pf-m-primary';
    
    return `
        <div class="pf-v5-u-mt-md">
            <button class="pf-v5-c-button ${buttonClass} block-rewrite-button" 
                    onclick="rewriteBlock('block-${displayIndex}', '${block.block_type}')" 
                    data-block-id="block-${displayIndex}"
                    data-block-type="${block.block_type}">
                ${buttonText}
            </button>
        </div>
    `;
}

/**
 * Estimate processing time based on error count and complexity
 */
function estimateBlockProcessingTime(errors) {
    if (!errors || errors.length === 0) return 0;
    
    // Base time + additional time per error
    const baseTime = 15;
    const timePerError = 3;
    const totalTime = baseTime + (errors.length * timePerError);
    
    return Math.min(totalTime, 30); // Cap at 30 seconds
}
