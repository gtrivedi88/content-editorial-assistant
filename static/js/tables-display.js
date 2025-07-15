/**
 * Tables Display Module - Enhanced PatternFly Table Rendering
 * Handles complex table display with proper formatting and style analysis using PatternFly components
 */

// Create a comprehensive table block with PatternFly table rendering
function createTableBlock(block, displayIndex) {
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    const issueCount = block.errors ? block.errors.length : 0;
    const status = issueCount > 0 ? 'red' : 'green';
    const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';
    
    // Extract table content and parse it into rows and cells
    const tableHtml = parseTableContent(block);
    
    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top app-card" id="block-${displayIndex}">
            <!-- Table header -->
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
                                ${block.title ? block.title : 'Data Table'} • ${issueCount} ${issueCount === 1 ? 'issue' : 'issues'} found
                            </p>
                        </div>
                    </div>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                        <span class="pf-v5-c-label__content">
                            <i class="fas fa-${issueCount > 0 ? 'exclamation-triangle' : 'check-circle'} pf-v5-c-label__icon"></i>
                            ${statusText}
                        </span>
                    </span>
                </div>
            </div>
            
            <!-- Table content -->
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
                
                <div class="pf-v5-c-card pf-m-plain pf-m-bordered" style="overflow: hidden;">
                    ${tableHtml}
                </div>
                
                ${block.errors && block.errors.length > 0 ? `
                <div class="pf-v5-u-mt-lg">
                    <div class="pf-v5-c-card pf-m-plain">
                        <div class="pf-v5-c-card__header">
                            <div class="pf-v5-c-card__header-main">
                                <h4 class="pf-v5-c-title pf-m-md">
                                    <i class="fas fa-exclamation-triangle pf-v5-u-mr-sm" style="color: var(--app-danger-color);"></i>
                                    ${(block.errors || []).length} Issue${(block.errors || []).length > 1 ? 's' : ''} Found
                                </h4>
                            </div>
                        </div>
                        <div class="pf-v5-c-card__body">
                            <div class="pf-v5-l-stack pf-m-gutter">
                                ${(block.errors || []).map(error => createInlineError(error)).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Parse table content and create PatternFly HTML table structure
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
    
    // Final fallback: show placeholder
    return `
        <div class="pf-v5-c-empty-state pf-m-lg">
            <div class="pf-v5-c-empty-state__content">
                <i class="fas fa-table pf-v5-c-empty-state__icon" style="color: var(--app-primary-color);"></i>
                <h2 class="pf-v5-c-title pf-m-lg">Table Parsing Error</h2>
                <div class="pf-v5-c-empty-state__body">
                    <p>Table content could not be parsed properly.</p>
                    <div class="pf-v5-c-code-block pf-v5-u-mt-md">
                        <div class="pf-v5-c-code-block__content">
                            <pre class="pf-v5-c-code-block__pre"><code class="pf-v5-c-code-block__code">${escapeHtml(block.content || 'No content')}</code></pre>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Parse AsciiDoc table format from raw content
function parseAsciiDocTable(rawContent) {
    try {
        // Extract table content between |=== markers
        const tableMatch = rawContent.match(/\|===\s*([\s\S]*?)\s*\|===/);
        if (!tableMatch) {
            return parseSimpleTable(rawContent);
        }
        
        const tableContent = tableMatch[1].trim();
        const lines = tableContent.split('\n').filter(line => line.trim() !== '');
        
        let rows = [];
        let currentRow = [];
        
        for (let line of lines) {
            line = line.trim();
            if (line.startsWith('|')) {
                // This is a table row
                if (currentRow.length > 0) {
                    rows.push(currentRow);
                    currentRow = [];
                }
                // Split by | and clean up
                const cells = line.split('|').slice(1).map(cell => cell.trim());
                currentRow = cells;
            } else if (line !== '') {
                // Continuation of previous cell
                if (currentRow.length > 0) {
                    currentRow[currentRow.length - 1] += ' ' + line;
                }
            }
        }
        
        // Add the last row
        if (currentRow.length > 0) {
            rows.push(currentRow);
        }
        
        if (rows.length === 0) {
            return parseSimpleTable(rawContent);
        }
        
        // Generate PatternFly HTML table
        return generatePatternFlyTable(rows, true); // Assume first row is header
        
    } catch (error) {
        console.error('Error parsing AsciiDoc table:', error);
        return parseSimpleTable(rawContent);
    }
}

// Parse structured table from children blocks (if parser provides table_row/table_cell)
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

// Parse simple table format (fallback)
function parseSimpleTable(content) {
    if (!content) {
        return `
            <div class="pf-v5-c-empty-state pf-m-sm">
                <div class="pf-v5-c-empty-state__content">
                    <i class="fas fa-table pf-v5-c-empty-state__icon" style="color: var(--pf-v5-global--Color--200);"></i>
                    <h3 class="pf-v5-c-title pf-m-md">No Table Content</h3>
                    <div class="pf-v5-c-empty-state__body">No table content available for display.</div>
                </div>
            </div>
        `;
    }
    
    // Try to detect table-like structure in plain text
    const lines = content.split('\n').filter(line => line.trim() !== '');
    
    // Look for lines that might be table rows (contain multiple words/values)
    const potentialRows = lines.filter(line => {
        const words = line.trim().split(/\s+/);
        return words.length >= 2; // At least 2 columns
    });
    
    if (potentialRows.length < 2) {
        // Not enough content for a table, show as formatted text
        return `
            <div class="pf-v5-c-code-block">
                <div class="pf-v5-c-code-block__header">
                    <div class="pf-v5-c-code-block__header-main">
                        <span class="pf-v5-c-code-block__title">Raw Content</span>
                    </div>
                </div>
                <div class="pf-v5-c-code-block__content">
                    <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; line-height: 1.6;"><code class="pf-v5-c-code-block__code">${escapeHtml(content)}</code></pre>
                </div>
            </div>
        `;
    }
    
    // Try to parse as space-separated table
    const rows = potentialRows.map(line => {
        return line.trim().split(/\s+/);
    });
    
    return generatePatternFlyTable(rows, true);
}

// Generate PatternFly HTML table from rows array
function generatePatternFlyTable(rows, hasHeader = false) {
    if (rows.length === 0) {
        return `
            <div class="pf-v5-c-empty-state pf-m-sm">
                <div class="pf-v5-c-empty-state__content">
                    <i class="fas fa-table pf-v5-c-empty-state__icon" style="color: var(--pf-v5-global--Color--200);"></i>
                    <h3 class="pf-v5-c-title pf-m-md">No Table Data</h3>
                    <div class="pf-v5-c-empty-state__body">No table data available for display.</div>
                </div>
            </div>
        `;
    }
    
    let html = '<table class="pf-v5-c-table pf-m-compact pf-m-grid-md" role="grid">';
    
    // Generate header if specified
    if (hasHeader && rows.length > 0) {
        html += '<thead>';
        html += '<tr role="row">';
        for (const cell of rows[0]) {
            html += `<th class="pf-v5-c-table__th" role="columnheader" scope="col">${renderSafeTableCellHtml(cell)}</th>`;
        }
        html += '</tr>';
        html += '</thead>';
        
        // Remove header row from data rows
        rows = rows.slice(1);
    }
    
    // Generate body rows
    html += '<tbody role="rowgroup">';
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        html += `<tr role="row">`;
        for (const cell of row) {
            html += `<td class="pf-v5-c-table__td" role="gridcell">${renderSafeTableCellHtml(cell)}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody>';
    
    html += '</table>';
    return html;
} 