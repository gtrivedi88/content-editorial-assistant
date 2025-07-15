/**
 * Tables Display Module - Table Rendering and Display Functions
 * Handles complex table display with proper formatting and style analysis
 */

// Create a comprehensive table block with proper HTML table rendering
function createTableBlock(block, displayIndex) {
    const style = {
        gradient: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
        bgColor: '#f0fdf4',
        borderColor: '#bbf7d0',
        textColor: '#1e293b',
        accentColor: '#059669'
    };
    
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    const issueCount = block.errors ? block.errors.length : 0;
    
    // Extract table content and parse it into rows and cells
    const tableHtml = parseTableContent(block);
    
    return `
        <div class="structural-block mb-4" style="
            border-radius: 16px;
            overflow: hidden;
            background: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid ${style.borderColor};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        ">
            <!-- Table header -->
            <div class="block-header d-flex justify-content-between align-items-center p-3" style="
                background: ${style.gradient};
                color: white;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            ">
                <div class="d-flex align-items-center">
                    <div class="me-3 d-flex align-items-center justify-content-center" style="
                        width: 40px;
                        height: 40px;
                        background: rgba(255, 255, 255, 0.15);
                        border-radius: 12px;
                        backdrop-filter: blur(10px);
                    ">
                        <i class="fas fa-table" style="font-size: 18px;"></i>
                    </div>
                    <div>
                        <h6 class="mb-0 fw-bold" style="font-size: 14px; letter-spacing: 0.5px;">
                            BLOCK ${displayIndex + 1}: ${blockTitle}
                        </h6>
                        <small class="opacity-90" style="font-size: 12px;">
                            ${block.title ? block.title : 'Data Table'} • ${issueCount} ${issueCount === 1 ? 'issue' : 'issues'} found
                        </small>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <div class="badge" style="
                        background: ${issueCount > 0 ? 'rgba(239, 68, 68, 0.9)' : 'rgba(34, 197, 94, 0.9)'};
                        color: white;
                        padding: 6px 12px;
                        border-radius: 20px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    ">
                        ${issueCount > 0 ? `${issueCount} ${issueCount === 1 ? 'ISSUE' : 'ISSUES'}` : 'CLEAN'}
                    </div>
                </div>
            </div>
            
            <!-- Table content -->
            <div class="block-content p-4" style="background: ${style.bgColor};">
                ${block.title ? `
                    <div class="table-title mb-3" style="
                        text-align: center;
                        font-weight: 600;
                        color: ${style.textColor};
                        font-size: 16px;
                        padding: 12px;
                        background: white;
                        border: 1px solid ${style.borderColor};
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
                    ">
                        ${escapeHtml(block.title)}
                    </div>
                ` : ''}
                
                <div class="table-container" style="
                    background: white;
                    border: 1px solid ${style.borderColor};
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                ">
                    ${tableHtml}
                </div>
                
                ${block.errors && block.errors.length > 0 ? `
                <div class="block-errors mt-4">
                    <div class="d-flex align-items-center mb-3">
                        <div class="me-3 d-flex align-items-center justify-content-center" style="
                            width: 32px;
                            height: 32px;
                            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                            border-radius: 8px;
                        ">
                            <i class="fas fa-exclamation-triangle" style="color: #dc2626; font-size: 14px;"></i>
                        </div>
                        <div>
                            <h6 class="mb-0 fw-bold" style="color: #dc2626; font-size: 14px;">
                                ${block.errors.length} Issue${block.errors.length > 1 ? 's' : ''} Found
                            </h6>
                            <small style="color: #6b7280;">Review the following suggestions</small>
                        </div>
                    </div>
                    <div class="error-list">
                        ${block.errors.map(error => createInlineError(error)).join('')}
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Parse table content and create HTML table structure
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
        <div class="p-4 text-center text-muted">
            <i class="fas fa-table fa-2x mb-3"></i>
            <div>Table content could not be parsed</div>
            <small>Raw content: ${escapeHtml(block.content || 'No content')}</small>
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
        
        // Generate HTML table
        return generateHtmlTable(rows, true); // Assume first row is header
        
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
    
    return generateHtmlTable(rows, true);
}

// Parse simple table format (fallback)
function parseSimpleTable(content) {
    if (!content) {
        return '<div class="p-4 text-center text-muted">No table content available</div>';
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
            <div class="p-4" style="
                font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
                font-size: 14px;
                line-height: 1.6;
                color: #1f2937;
                white-space: pre-wrap;
                background: #f9fafb;
                border-radius: 8px;
            ">${escapeHtml(content)}</div>
        `;
    }
    
    // Try to parse as space-separated table
    const rows = potentialRows.map(line => {
        return line.trim().split(/\s+/);
    });
    
    return generateHtmlTable(rows, true);
}

// Generate HTML table from rows array
function generateHtmlTable(rows, hasHeader = false) {
    if (rows.length === 0) {
        return '<div class="p-4 text-center text-muted">No table data available</div>';
    }
    
    let html = '<table class="table table-hover" style="margin: 0; font-size: 14px;">';
    
    // Generate header if specified
    if (hasHeader && rows.length > 0) {
        html += '<thead style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);">';
        html += '<tr>';
        for (const cell of rows[0]) {
            html += `<th style="
                padding: 16px;
                font-weight: 600;
                color: #374151;
                border-bottom: 2px solid #e5e7eb;
                text-align: left;
            ">${renderSafeTableCellHtml(cell)}</th>`;
        }
        html += '</tr>';
        html += '</thead>';
        
        // Remove header row from data rows
        rows = rows.slice(1);
    }
    
    // Generate body rows
    html += '<tbody>';
    for (let i = 0; i < rows.length; i++) {
        const row = rows[i];
        html += `<tr style="border-bottom: 1px solid #f3f4f6; transition: background-color 0.2s;">`;
        for (const cell of row) {
            html += `<td style="
                padding: 16px;
                color: #374151;
                vertical-align: top;
                border-bottom: 1px solid #f3f4f6;
            ">${renderSafeTableCellHtml(cell)}</td>`;
        }
        html += '</tr>';
    }
    html += '</tbody>';
    
    html += '</table>';
    return html;
} 