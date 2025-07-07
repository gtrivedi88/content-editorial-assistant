// Analysis display functions

// Display structural blocks (ideal UI)
function displayStructuralBlocks(blocks) {
    if (!blocks || blocks.length === 0) {
        return null;
    }
    
    return `
        <div class="mb-4">
            <div class="d-flex align-items-center mb-4" style="
                padding: 20px;
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            ">
                <div class="me-3 d-flex align-items-center justify-content-center" style="
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 12px;
                ">
                    <i class="fas fa-sitemap" style="color: white; font-size: 16px;"></i>
                </div>
                <div>
                    <h6 class="mb-1 fw-bold" style="color: #1e293b; font-size: 16px; letter-spacing: 0.5px;">Document Structure Analysis</h6>
                    <small style="color: #64748b; font-size: 13px;">Content organized by structural elements with context-aware style checking</small>
                </div>
                <div class="ms-auto">
                    <div class="badge" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 6px 12px;
                        border-radius: 8px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    ">
                        ${blocks.length} BLOCKS
                    </div>
                </div>
            </div>
            <div class="structural-blocks">
                ${(() => {
                    let displayIndex = 0;
                    return blocks.map(block => {
                        const html = createStructuralBlock(block, displayIndex);
                        if (html !== '') {
                            displayIndex++;
                        }
                        return html;
                    }).filter(html => html !== '').join('');
                })()}
            </div>
        </div>
    `;
}

// Display flat content (fallback)
function displayFlatContent(content, errors) {
    return `
        <div class="mb-3">
            <h6>Original Content:</h6>
            <div class="border rounded p-3 bg-light">
                ${highlightErrors(content, errors)}
            </div>
        </div>
        
        ${errors.length > 0 ? `
        <div class="mb-3">
            <h6>Detected Issues (${errors.length}):</h6>
            <div class="analysis-container">
                ${errors.map(error => createErrorCard(error)).join('')}
            </div>
        </div>
        ` : '<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>No issues detected!</div>'}
    `;
}

// Get a human-readable display name for a block type
function getBlockTypeDisplayName(blockType, context) {
    const level = context.level || 0;
    const admonitionType = context.admonition_type;
    
    const displayNames = {
        'heading': `HEADING (Level ${level})`,
        'paragraph': 'PARAGRAPH',
        'ordered_list': 'ORDERED LIST',
        'unordered_list': 'UNORDERED LIST',
        'list_item': 'LIST ITEM',
        'list_title': 'LIST TITLE',
        'admonition': `ADMONITION (${admonitionType ? admonitionType.toUpperCase() : 'NOTE'})`,
        'sidebar': 'SIDEBAR',
        'example': 'EXAMPLE',
        'quote': 'QUOTE',
        'verse': 'VERSE',
        'listing': 'CODE BLOCK',
        'literal': 'LITERAL BLOCK',
        'attribute_entry': 'ATTRIBUTE',
        'comment': 'COMMENT',
        'table': 'TABLE',
        'image': 'IMAGE',
        'audio': 'AUDIO',
        'video': 'VIDEO'
    };
    
    return displayNames[blockType] || blockType.toUpperCase().replace(/_/g, ' ');
}

// Create a list block with proper formatting (bullets, numbers, etc.)
function createListBlock(block, displayIndex) {
    const isOrdered = block.block_type === 'ordered_list';
    const style = {
        gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
        bgColor: '#f0fdfa',
        borderColor: '#ccfbf1',
        textColor: '#134e4a',
        accentColor: '#0d9488'
    };
    
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    // Count total issues including both list-level and item-level errors
    let totalIssues = 0;
    
    // Add block-level errors (like parallelism)
    if (block.errors) totalIssues += block.errors.length;
    
    // Add individual item errors
    const countIssues = (items) => {
        items.forEach(item => {
            if (item.errors) totalIssues += item.errors.length;
            if (item.children) countIssues(item.children);
        });
    };
    if (block.children) countIssues(block.children);
     
     // Generate list items HTML with proper formatting
     const generateListItems = (items, level = 0, parentIsOrdered = isOrdered) => {
         if (!items || items.length === 0) return '';
         
         return items.map((item, index) => {
            const marker = parentIsOrdered ? `${index + 1}.` : '•';
            const indentStyle = level > 0 ? `margin-left: ${level * 20}px;` : '';
            
            let itemHtml = `
                <div class="list-item" style="${indentStyle} margin-bottom: 8px;">
                    <div class="d-flex align-items-start">
                        <div class="list-marker me-3" style="
                            min-width: 24px;
                            font-weight: 600;
                            color: ${style.accentColor};
                            font-size: 14px;
                            line-height: 1.6;
                        ">
                            ${marker}
                        </div>
                        <div class="list-content flex-grow-1">
                            <div class="item-text" style="
                                color: #1f2937;
                                font-size: 14px;
                                line-height: 1.6;
                                margin-bottom: ${item.errors && item.errors.length > 0 ? '8px' : '0'};
                            ">
                                ${escapeHtml(item.content)}
                            </div>
                            ${item.errors && item.errors.length > 0 ? `
                                <div class="item-errors">
                                    ${item.errors.map(error => createInlineError(error)).join('')}
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            
            // Handle nested lists
            if (item.children && item.children.length > 0) {
                // Check if children are list items or nested lists
                const nestedLists = item.children.filter(child => 
                    child.block_type === 'unordered_list' || child.block_type === 'ordered_list'
                );
                
                if (nestedLists.length > 0) {
                    nestedLists.forEach(nestedList => {
                        const nestedIsOrdered = nestedList.block_type === 'ordered_list';
                        itemHtml += `
                            <div class="nested-list" style="margin-left: 20px; margin-top: 8px;">
                                ${generateListItems(nestedList.children, level + 1, nestedIsOrdered)}
                            </div>
                        `;
                    });
                }
            }
            
            return itemHtml;
        }).join('');
    };
    
    return `
        <div class="structural-block mb-4" style="
            border-radius: 16px;
            overflow: hidden;
            background: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid ${style.borderColor};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        ">
            <!-- List header -->
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
                        <i class="fas fa-list-${isOrdered ? 'ol' : 'ul'}" style="font-size: 18px;"></i>
                    </div>
                                         <div>
                         <h6 class="mb-0 fw-bold" style="font-size: 14px; letter-spacing: 0.5px;">
                             BLOCK ${displayIndex + 1}: ${blockTitle}
                         </h6>
                         <small class="opacity-90" style="font-size: 12px;">
                             ${totalIssues} ${totalIssues === 1 ? 'issue' : 'issues'} found
                         </small>
                     </div>
                </div>
                <div class="d-flex align-items-center">
                    <div class="badge" style="
                        background: ${totalIssues > 0 ? 'rgba(239, 68, 68, 0.9)' : 'rgba(34, 197, 94, 0.9)'};
                        color: white;
                        padding: 6px 12px;
                        border-radius: 20px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    ">
                        ${totalIssues > 0 ? `${totalIssues} ${totalIssues === 1 ? 'ISSUE' : 'ISSUES'}` : 'CLEAN'}
                    </div>
                </div>
            </div>
            
            <!-- List content -->
            <div class="block-content p-4" style="background: ${style.bgColor};">
                <div class="list-container" style="
                    background: white;
                    border: 1px solid ${style.borderColor};
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                ">
                    ${generateListItems(block.children)}
                </div>
                
                ${block.errors && block.errors.length > 0 ? `
                <div class="block-level-errors mt-3" style="
                    background: white;
                    border: 1px solid ${style.borderColor};
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                ">
                    <div class="d-flex align-items-center mb-3">
                        <div class="me-3 d-flex align-items-center justify-content-center" style="
                            width: 32px;
                            height: 32px;
                            background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                            border-radius: 8px;
                        ">
                            <i class="fas fa-list-ul" style="color: #dc2626; font-size: 14px;"></i>
                        </div>
                        <div>
                            <h6 class="mb-0 fw-bold" style="color: #dc2626; font-size: 14px;">
                                List-Level Issues (${block.errors.length})
                            </h6>
                            <small style="color: #6b7280;">Issues affecting the entire list structure</small>
                        </div>
                    </div>
                    <div class="error-list">
                        ${block.errors.map(error => createInlineError(error)).join('')}
                    </div>
                </div>
                ` : ''}
                
                ${totalIssues === 0 ? `
                <div class="d-flex align-items-center justify-content-center py-3 mt-3" style="
                    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                    border: 1px solid #bbf7d0;
                    border-radius: 12px;
                    color: #166534;
                ">
                    <i class="fas fa-check-circle me-3" style="color: #22c55e; font-size: 20px;"></i>
                    <div>
                        <div class="fw-medium">No issues found in this block</div>
                        <small style="opacity: 0.8;">This content follows style guidelines perfectly</small>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create a list title block with special styling
function createListTitleBlock(block, displayIndex) {
    const style = {
        gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
        bgColor: '#faf5ff',
        borderColor: '#e9d5ff',
        textColor: '#1e293b',
        accentColor: '#8b5cf6'
    };
    
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    const issueCount = block.errors ? block.errors.length : 0;
    
    return `
        <div class="structural-block mb-4" style="
            border-radius: 16px;
            overflow: hidden;
            background: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid ${style.borderColor};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        ">
            <!-- List title header -->
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
                        <i class="fas fa-list-ul" style="font-size: 18px;"></i>
                    </div>
                    <div>
                        <h6 class="mb-0 fw-bold" style="font-size: 14px; letter-spacing: 0.5px;">
                            BLOCK ${displayIndex + 1}: ${blockTitle}
                        </h6>
                        <small class="opacity-90" style="font-size: 12px;">
                            ${issueCount} ${issueCount === 1 ? 'issue' : 'issues'} found
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
            
            <!-- List title content -->
            <div class="block-content p-4" style="background: ${style.bgColor};">
                <div class="title-display" style="
                    background: white;
                    border: 1px solid ${style.borderColor};
                    border-radius: 12px;
                    padding: 20px;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                    text-align: center;
                ">
                    <div class="title-content" style="
                        font-size: 16px;
                        font-weight: 600;
                        color: ${style.textColor};
                        margin-bottom: 12px;
                    ">
                        ${escapeHtml(block.content)}
                    </div>
                    
                    ${block.errors && block.errors.length > 0 ? `
                        <div class="title-errors mt-3">
                            ${block.errors.map(error => createInlineError(error)).join('')}
                        </div>
                    ` : ''}
                </div>
                
                ${issueCount === 0 ? `
                <div class="d-flex align-items-center justify-content-center py-3 mt-3" style="
                    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                    border: 1px solid #bbf7d0;
                    border-radius: 12px;
                    color: #166534;
                ">
                    <i class="fas fa-check-circle me-3" style="color: #22c55e; font-size: 20px;"></i>
                    <div>
                        <div class="fw-medium">No issues found in this block</div>
                        <small style="opacity: 0.8;">This content follows style guidelines perfectly</small>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create a table block with proper HTML table rendering
function createTableBlock(block, displayIndex) {
    const style = {
        gradient: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
        bgColor: '#f0fdfa',
        borderColor: '#ccfbf1',
        textColor: '#134e4a',
        accentColor: '#14b8a6'
    };
    
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    // Count issues in table content and cells
    let totalIssues = 0;
    if (block.errors) totalIssues += block.errors.length;
    
    // Count issues in table rows and cells
    const countTableIssues = (children) => {
        if (!children) return;
        children.forEach(child => {
            if (child.errors) totalIssues += child.errors.length;
            if (child.children) countTableIssues(child.children);
        });
    };
    countTableIssues(block.children);
    
    // Calculate actual table dimensions from structure
    const rows = block.children ? block.children.filter(child => child.block_type === 'table_row') : [];
    const rowCount = rows.length;
    let colCount = 0;
    
    // Get column count from first row
    if (rows.length > 0) {
        const firstRowCells = rows[0].children ? rows[0].children.filter(child => child.block_type === 'table_cell') : [];
        colCount = firstRowCells.length;
    }
    
    // Extract table attributes for display
    const tableAttrs = block.attributes || {};
    const colsInfo = tableAttrs.cols;
    
    // Generate HTML table from structured data
    const generateHTMLTable = (tableBlock) => {
        if (!tableBlock.children || tableBlock.children.length === 0) {
            return `<div class="alert alert-info">No table data available</div>`;
        }
        
        const rows = tableBlock.children.filter(child => child.block_type === 'table_row');
        if (rows.length === 0) {
            return `<div class="alert alert-info">No table rows found</div>`;
        }
        
        let tableHTML = `
            <table class="table table-striped table-hover" style="
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                border: 1px solid ${style.borderColor};
                border-radius: 12px;
                overflow: hidden;
                background: white;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            ">
        `;
        
        // Process each row
        rows.forEach((row, rowIndex) => {
            // First row is typically header in AsciiDoc tables
            const isHeaderRow = rowIndex === 0 || (row.attributes && row.attributes.row_type === 'header');
            const cells = row.children ? row.children.filter(child => child.block_type === 'table_cell') : [];
            
            const originalBgColor = isHeaderRow ? 
                `linear-gradient(135deg, ${style.accentColor}15, ${style.accentColor}10)` : 
                (rowIndex % 2 === 0 ? 'white' : '#f9fafb');
            
            tableHTML += `<tr style="
                background: ${originalBgColor};
                transition: all 0.2s ease;
            " onmouseover="this.style.backgroundColor='${style.accentColor}10'" onmouseout="this.style.background='${originalBgColor}'">`;
            
            // Process each cell
            cells.forEach((cell, cellIndex) => {
                const cellType = isHeaderRow ? 'th' : 'td';
                const cellAttrs = cell.attributes || {};
                const colspan = cellAttrs.colspan || 1;
                const rowspan = cellAttrs.rowspan || 1;
                
                const cellStyle = `
                    padding: 12px 16px;
                    border-bottom: 1px solid ${style.borderColor};
                    ${cellIndex === 0 ? `border-left: 3px solid ${style.accentColor};` : ''}
                    font-weight: ${isHeaderRow ? '600' : '400'};
                    color: ${isHeaderRow ? style.textColor : '#1f2937'};
                    font-size: 14px;
                    line-height: 1.5;
                    vertical-align: top;
                    position: relative;
                `;
                
                // Add error indicators if cell has issues
                const cellErrors = cell.errors || [];
                const errorIndicator = cellErrors.length > 0 ? `
                    <div class="position-absolute top-0 end-0 me-2 mt-1">
                        <span class="badge bg-danger rounded-circle" style="width: 8px; height: 8px; padding: 0;" 
                              title="${cellErrors.length} issue${cellErrors.length > 1 ? 's' : ''} in this cell"></span>
                    </div>
                ` : '';
                
                tableHTML += `<${cellType} 
                    ${colspan > 1 ? `colspan="${colspan}"` : ''}
                    ${rowspan > 1 ? `rowspan="${rowspan}"` : ''}
                    style="${cellStyle}"
                >
                    ${errorIndicator}
                    ${renderSafeTableCellHtml(cell.content || '')}
                </${cellType}>`;
            });
            
            tableHTML += `</tr>`;
        });
        
        tableHTML += `</table>`;
        return tableHTML;
    };
    
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
                            ${rowCount} rows × ${colCount} columns • ${totalIssues} ${totalIssues === 1 ? 'issue' : 'issues'} found
                        </small>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <div class="badge" style="
                        background: ${totalIssues > 0 ? 'rgba(239, 68, 68, 0.9)' : 'rgba(34, 197, 94, 0.9)'};
                        color: white;
                        padding: 6px 12px;
                        border-radius: 20px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    ">
                        ${totalIssues > 0 ? `${totalIssues} ${totalIssues === 1 ? 'ISSUE' : 'ISSUES'}` : 'CLEAN'}
                    </div>
                </div>
            </div>
            
            <!-- Table content -->
            <div class="block-content p-4" style="background: ${style.bgColor};">
                ${block.title ? `
                    <div class="table-title mb-3 text-center" style="
                        font-size: 16px;
                        font-weight: 600;
                        color: ${style.textColor};
                        padding: 12px 0;
                        border-bottom: 2px solid ${style.borderColor};
                    ">
                        ${escapeHtml(block.title)}
                    </div>
                ` : ''}
                
                <!-- Rendered HTML Table -->
                <div class="table-responsive" style="border-radius: 12px; overflow: hidden;">
                    ${generateHTMLTable(block)}
                </div>
                
                <!-- Table-level errors -->
                ${block.errors && block.errors.length > 0 ? `
                    <div class="block-errors mt-3" style="
                        background: white;
                        border: 1px solid ${style.borderColor};
                        border-radius: 12px;
                        padding: 20px;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                    ">
                        <div class="d-flex align-items-center mb-3">
                            <div class="me-3 d-flex align-items-center justify-content-center" style="
                                width: 32px;
                                height: 32px;
                                background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                                border-radius: 8px;
                            ">
                                <i class="fas fa-table" style="color: #dc2626; font-size: 14px;"></i>
                            </div>
                            <div>
                                <h6 class="mb-0 fw-bold" style="color: #dc2626; font-size: 14px;">
                                    Table-Level Issues (${block.errors.length})
                                </h6>
                                <small style="color: #6b7280;">Issues affecting the entire table structure</small>
                            </div>
                        </div>
                        <div class="error-list">
                            ${block.errors.map(error => createInlineError(error)).join('')}
                        </div>
                    </div>
                ` : ''}
                
                <!-- Cell-level errors summary -->
                ${(() => {
                    const cellErrors = [];
                    const collectCellErrors = (children) => {
                        if (!children) return;
                        children.forEach(child => {
                            if (child.block_type === 'table_cell' && child.errors && child.errors.length > 0) {
                                cellErrors.push({
                                    rowIndex: child.attributes?.row_index || 0,
                                    cellIndex: child.attributes?.cell_index || 0,
                                    content: child.content || '',
                                    errors: child.errors
                                });
                            }
                            if (child.children) collectCellErrors(child.children);
                        });
                    };
                    collectCellErrors(block.children);
                    
                    if (cellErrors.length > 0) {
                        return `
                            <div class="cell-errors mt-3" style="
                                background: white;
                                border: 1px solid ${style.borderColor};
                                border-radius: 12px;
                                padding: 20px;
                                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                            ">
                                <div class="d-flex align-items-center mb-3">
                                    <div class="me-3 d-flex align-items-center justify-content-center" style="
                                        width: 32px;
                                        height: 32px;
                                        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                                        border-radius: 8px;
                                    ">
                                        <i class="fas fa-th" style="color: #d97706; font-size: 14px;"></i>
                                    </div>
                                    <div>
                                        <h6 class="mb-0 fw-bold" style="color: #d97706; font-size: 14px;">
                                            Cell-Level Issues (${cellErrors.length})
                                        </h6>
                                        <small style="color: #6b7280;">Issues found in individual table cells</small>
                                    </div>
                                </div>
                                <div class="error-list">
                                    ${cellErrors.map(cellError => `
                                        <div class="cell-error mb-2" style="
                                            background: #fef3c7;
                                            border: 1px solid #fde68a;
                                            border-radius: 8px;
                                            padding: 12px;
                                        ">
                                            <div class="fw-medium mb-1" style="color: #92400e;">
                                                Row ${cellError.rowIndex + 1}, Column ${cellError.cellIndex + 1}
                                            </div>
                                            <div class="small mb-2" style="color: #6b7280;">
                                                "${cellError.content.length > 50 ? cellError.content.substring(0, 50) + '...' : cellError.content}"
                                            </div>
                                            ${cellError.errors.map(error => createInlineError(error)).join('')}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `;
                    }
                    return '';
                })()}
                
                ${totalIssues === 0 ? `
                    <div class="d-flex align-items-center justify-content-center py-3 mt-3" style="
                        background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                        border: 1px solid #bbf7d0;
                        border-radius: 12px;
                        color: #166534;
                    ">
                        <i class="fas fa-check-circle me-3" style="color: #22c55e; font-size: 20px;"></i>
                        <div>
                            <div class="fw-medium">Table is perfectly formatted</div>
                            <small style="opacity: 0.8;">No style issues found in this table</small>
                        </div>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create a structural block display with world-class design
function createStructuralBlock(block, displayIndex) {
    // Handle list blocks specially - group list items under their parent
    if (block.block_type === 'unordered_list' || block.block_type === 'ordered_list') {
        return createListBlock(block, displayIndex);
    }
    
    // Skip individual list items - they'll be handled by their parent list
    if (block.block_type === 'list_item') {
        return '';
    }
    
    // Handle list titles specially
    if (block.block_type === 'list_title') {
        return createListTitleBlock(block, displayIndex);
    }
    
    // Handle table blocks specially - render as actual HTML table
    if (block.block_type === 'table') {
        return createTableBlock(block, displayIndex);
    }
    
    // Skip table rows and cells - they'll be handled by their parent table
    if (block.block_type === 'table_row' || block.block_type === 'table_cell') {
        return '';
    }
    
    // World-class color palette - professional and accessible
    const blockTypeStyles = {
        'heading': {
            gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            bgColor: '#f8fafc',
            borderColor: '#e2e8f0',
            textColor: '#1e293b',
            accentColor: '#667eea'
        },
        'paragraph': {
            gradient: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
            bgColor: '#f0f9ff',
            borderColor: '#e0f2fe',
            textColor: '#0f172a',
            accentColor: '#0ea5e9'
        },
        'ordered_list': {
            gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            bgColor: '#f0fdfa',
            borderColor: '#ccfbf1',
            textColor: '#134e4a',
            accentColor: '#0d9488'
        },
        'unordered_list': {
            gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            bgColor: '#f0fdfa',
            borderColor: '#ccfbf1',
            textColor: '#134e4a',
            accentColor: '#0d9488'
        },
        'list_item': {
            gradient: 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
            bgColor: '#f0fdfa',
            borderColor: '#ccfbf1',
            textColor: '#134e4a',
            accentColor: '#0d9488'
        },
        'list_title': {
            gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            bgColor: '#faf5ff',
            borderColor: '#e9d5ff',
            textColor: '#1e293b',
            accentColor: '#8b5cf6'
        },
        'admonition': {
            gradient: 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
            bgColor: '#eff6ff',
            borderColor: '#dbeafe',
            textColor: '#1e293b',
            accentColor: '#3b82f6'
        },
        'listing': {
            gradient: 'linear-gradient(135deg, #374151 0%, #1f2937 100%)',
            bgColor: '#f9fafb',
            borderColor: '#e5e7eb',
            textColor: '#111827',
            accentColor: '#374151'
        },
        'literal': {
            gradient: 'linear-gradient(135deg, #374151 0%, #1f2937 100%)',
            bgColor: '#f9fafb',
            borderColor: '#e5e7eb',
            textColor: '#111827',
            accentColor: '#374151'
        },
        'quote': {
            gradient: 'linear-gradient(135deg, #059669 0%, #047857 100%)',
            bgColor: '#f0fdfa',
            borderColor: '#ccfbf1',
            textColor: '#0f172a',
            accentColor: '#059669'
        },
        'sidebar': {
            gradient: 'linear-gradient(135deg, #dc2626 0%, #b91c1c 100%)',
            bgColor: '#fef2f2',
            borderColor: '#fecaca',
            textColor: '#1f2937',
            accentColor: '#dc2626'
        },
        'example': {
            gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            bgColor: '#f5f3ff',
            borderColor: '#e9d5ff',
            textColor: '#1e293b',
            accentColor: '#8b5cf6'
        },
        'verse': {
            gradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
            bgColor: '#fffbeb',
            borderColor: '#fed7aa',
            textColor: '#1e293b',
            accentColor: '#f59e0b'
        },
        'attribute_entry': {
            gradient: 'linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%)',
            bgColor: '#f9fafb',
            borderColor: '#e5e7eb',
            textColor: '#6b7280',
            accentColor: '#9ca3af'
        },
        'comment': {
            gradient: 'linear-gradient(135deg, #d1d5db 0%, #9ca3af 100%)',
            bgColor: '#f9fafb',
            borderColor: '#e5e7eb',
            textColor: '#6b7280',
            accentColor: '#9ca3af'
        },
        'table': {
            gradient: 'linear-gradient(135deg, #14b8a6 0%, #0d9488 100%)',
            bgColor: '#f0fdfa',
            borderColor: '#ccfbf1',
            textColor: '#134e4a',
            accentColor: '#14b8a6'
        },
        'image': {
            gradient: 'linear-gradient(135deg, #f472b6 0%, #ec4899 100%)',
            bgColor: '#fdf2f8',
            borderColor: '#fbcfe8',
            textColor: '#1e293b',
            accentColor: '#f472b6'
        },
        'audio': {
            gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
            bgColor: '#f5f3ff',
            borderColor: '#e9d5ff',
            textColor: '#1e293b',
            accentColor: '#8b5cf6'
        },
        'video': {
            gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            bgColor: '#fef2f2',
            borderColor: '#fecaca',
            textColor: '#1e293b',
            accentColor: '#ef4444'
        }
    };
    
    const blockTypeIcons = {
        'heading': 'fas fa-heading',
        'paragraph': 'fas fa-paragraph',
        'ordered_list': 'fas fa-list-ol',
        'unordered_list': 'fas fa-list-ul',
        'list_item': 'fas fa-list',
        'list_title': 'fas fa-heading',
        'admonition': 'fas fa-info-circle',
        'listing': 'fas fa-code',
        'literal': 'fas fa-terminal',
        'quote': 'fas fa-quote-left',
        'sidebar': 'fas fa-columns',
        'example': 'fas fa-lightbulb',
        'verse': 'fas fa-feather',
        'attribute_entry': 'fas fa-cog',
        'comment': 'fas fa-comment',
        'table': 'fas fa-table',
        'image': 'fas fa-image',
        'audio': 'fas fa-music',
        'video': 'fas fa-video'
    };
    
    const style = blockTypeStyles[block.block_type] || blockTypeStyles['paragraph'];
    const icon = blockTypeIcons[block.block_type] || 'fas fa-file-alt';
    
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    const issueCount = block.errors ? block.errors.length : 0;
    
    return `
        <div class="structural-block mb-4" style="
            border-radius: 16px;
            overflow: hidden;
            background: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid ${style.borderColor};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        ">
            <!-- World-class header design -->
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
                        <i class="${icon}" style="font-size: 18px;"></i>
                    </div>
                    <div>
                        <h6 class="mb-0 fw-bold" style="font-size: 14px; letter-spacing: 0.5px;">
                            BLOCK ${displayIndex + 1}: ${blockTitle}
                        </h6>
                        <small class="opacity-90" style="font-size: 12px;">
                            ${block.should_skip_analysis ? 'Analysis skipped for this block type' : 
                              `${issueCount} ${issueCount === 1 ? 'issue' : 'issues'} found`}
                        </small>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    ${!block.should_skip_analysis ? `
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
                    ` : `
                        <div class="badge" style="
                            background: rgba(156, 163, 175, 0.9);
                            color: white;
                            padding: 6px 12px;
                            border-radius: 20px;
                            font-size: 11px;
                            font-weight: 600;
                            letter-spacing: 0.5px;
                        ">
                            SKIPPED
                        </div>
                    `}
                </div>
            </div>
            
            <!-- Premium content area -->
            <div class="block-content p-4" style="background: ${style.bgColor};">
                ${block.should_skip_analysis ? 
                                         `<div class="d-flex align-items-center justify-content-center py-4" style="
                         color: #374151;
                         font-style: italic;
                     ">
                         <i class="fas fa-info-circle me-3" style="font-size: 24px; color: ${style.accentColor};"></i>
                         <div>
                             <div class="fw-medium">Analysis skipped for this block type</div>
                             <small style="color: #6b7280;">Code blocks and attributes are not analyzed for style issues</small>
                         </div>
                     </div>` : 
                                         `<div class="block-text mb-3" style="
                         background: white;
                         border: 1px solid ${style.borderColor};
                         border-radius: 12px;
                         padding: 20px;
                         font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Roboto Mono', monospace;
                         font-size: 14px;
                         line-height: 1.6;
                         color: #1f2937;
                         white-space: pre-wrap;
                         word-wrap: break-word;
                         box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                     ">
${escapeHtml(block.content)}
                     </div>`
                }
                
                ${!block.should_skip_analysis && block.errors && block.errors.length > 0 ? `
                <div class="block-errors">
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
                
                ${!block.should_skip_analysis && (!block.errors || block.errors.length === 0) ? `
                <div class="d-flex align-items-center justify-content-center py-3" style="
                    background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
                    border: 1px solid #bbf7d0;
                    border-radius: 12px;
                    color: #166534;
                ">
                    <i class="fas fa-check-circle me-3" style="color: #22c55e; font-size: 20px;"></i>
                    <div>
                        <div class="fw-medium">No issues found in this block</div>
                        <small style="opacity: 0.8;">This content follows style guidelines perfectly</small>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

// Create inline error display with premium design
function createInlineError(error) {
    const errorTypes = {
        'STYLE': { color: '#dc2626', bg: '#fef2f2', icon: 'fas fa-exclamation-circle' },
        'GRAMMAR': { color: '#b45309', bg: '#fefbeb', icon: 'fas fa-spell-check' },
        'STRUCTURE': { color: '#1e40af', bg: '#eff6ff', icon: 'fas fa-sitemap' },
        'PUNCTUATION': { color: '#6b21a8', bg: '#faf5ff', icon: 'fas fa-quote-right' },
        'CAPITALIZATION': { color: '#059669', bg: '#ecfdf5', icon: 'fas fa-font' },
        'TERMINOLOGY': { color: '#c2410c', bg: '#fff7ed', icon: 'fas fa-book' },
        'PASSIVE_VOICE': { color: '#b45309', bg: '#fefbeb', icon: 'fas fa-exchange-alt' },
        'READABILITY': { color: '#0e7490', bg: '#ecfeff', icon: 'fas fa-eye' },
        'ADMONITIONS': { color: '#1e40af', bg: '#eff6ff', icon: 'fas fa-info-circle' },
        'HEADINGS': { color: '#7c2d12', bg: '#fef7ed', icon: 'fas fa-heading' },
        'LISTS': { color: '#059669', bg: '#ecfdf5', icon: 'fas fa-list' },
        'PROCEDURES': { color: '#0e7490', bg: '#ecfeff', icon: 'fas fa-tasks' }
    };
    
    const errorType = error.error_type || 'STYLE';
    const typeStyle = errorTypes[errorType] || errorTypes['STYLE'];
    
    return `
        <div class="error-item mb-3" style="
            background: white;
            border: 1px solid ${typeStyle.bg};
            border-left: 4px solid ${typeStyle.color};
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 16px rgba(0, 0, 0, 0.08)'" 
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0, 0, 0, 0.04)'">
            <div class="d-flex align-items-start">
                <div class="me-3 d-flex align-items-center justify-content-center" style="
                    width: 36px;
                    height: 36px;
                    background: ${typeStyle.bg};
                    border-radius: 10px;
                    flex-shrink: 0;
                ">
                    <i class="${typeStyle.icon}" style="color: ${typeStyle.color}; font-size: 16px;"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-2">
                        <span class="badge me-2" style="
                            background: ${typeStyle.color};
                            color: white;
                            padding: 4px 10px;
                            border-radius: 6px;
                            font-size: 10px;
                            font-weight: 600;
                            letter-spacing: 0.5px;
                        ">${errorType}</span>
                        <div class="fw-semibold" style="color: #374151; font-size: 14px;">
                            ${error.message || 'Style issue detected'}
                        </div>
                    </div>
                    ${error.suggestion ? `
                    <div class="d-flex align-items-start" style="
                        background: ${typeStyle.bg};
                        border-radius: 8px;
                        padding: 12px;
                        margin-top: 8px;
                    ">
                        <i class="fas fa-lightbulb me-2" style="
                            color: ${typeStyle.color};
                            margin-top: 2px;
                            font-size: 14px;
                        "></i>
                        <div style="color: #4b5563; font-size: 13px; line-height: 1.5;">
                            <strong style="color: ${typeStyle.color};">Suggestion:</strong> ${error.suggestion}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// Display analysis results
function displayAnalysisResults(analysis, content, structuralBlocks = null) {
    const resultsContainer = document.getElementById('analysis-results');
    if (!resultsContainer) return;
    
    let html = `
        <div class="row">
            <div class="col-md-8">
                <div class="card border-0" style="
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
                    background: white;
                ">
                    <div class="card-header border-0 d-flex justify-content-between align-items-center" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 24px;
                    ">
                        <div class="d-flex align-items-center">
                            <div class="me-3 d-flex align-items-center justify-content-center" style="
                                width: 48px;
                                height: 48px;
                                background: rgba(255, 255, 255, 0.15);
                                border-radius: 16px;
                                backdrop-filter: blur(10px);
                            ">
                                <i class="fas fa-file-alt" style="font-size: 20px;"></i>
                            </div>
                            <div>
                                <h5 class="mb-1 fw-bold" style="font-size: 18px; letter-spacing: 0.5px;">Content Analysis</h5>
                                <small class="opacity-90" style="font-size: 14px;">Structural document review and style assessment</small>
                            </div>
                        </div>
                        <div class="d-flex align-items-center">
                            <div class="text-end me-3">
                                <div class="small opacity-75" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Quality Score</div>
                                <div class="fw-bold" style="font-size: 24px;">${analysis.overall_score.toFixed(1)}%</div>
                            </div>
                            <div class="badge" style="
                                background: ${analysis.overall_score >= 80 ? 'rgba(34, 197, 94, 0.9)' : analysis.overall_score >= 60 ? 'rgba(245, 158, 11, 0.9)' : 'rgba(239, 68, 68, 0.9)'};
                                color: white;
                                padding: 8px 16px;
                                border-radius: 12px;
                                font-size: 12px;
                                font-weight: 600;
                                letter-spacing: 0.5px;
                            ">
                                ${analysis.overall_score >= 80 ? 'EXCELLENT' : analysis.overall_score >= 60 ? 'GOOD' : 'NEEDS WORK'}
                            </div>
                        </div>
                    </div>
                    <div class="card-body" style="padding: 32px;">
                        ${structuralBlocks ? (displayStructuralBlocks(structuralBlocks) || displayFlatContent(content, analysis.errors)) : displayFlatContent(content, analysis.errors)}
                        
                        ${analysis.errors.length > 0 ? `
                        <div class="text-center mt-4">
                            <button class="btn btn-primary btn-lg" onclick="rewriteContent()">
                                <i class="fas fa-magic me-2"></i>Rewrite with AI
                            </button>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                ${generateStatisticsCard(analysis)}
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
}

// Generate statistics card (full implementation)
function generateStatisticsCard(analysis) {
    return `
        <!-- Ultra-Modern Technical Writing Statistics Card -->
        <div class="card border-0 shadow-lg" style="border-radius: 24px; overflow: hidden; background: white;">
            <!-- Modern gradient header -->
            <div class="card-header border-0 pb-2" style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%); color: white; border-radius: 0;">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="mb-0 fw-bold">
                        <i class="fas fa-chart-line me-2"></i>Writing Analytics
                    </h5>
                    <button class="btn btn-sm btn-light btn-outline-light rounded-pill opacity-90" data-bs-toggle="modal" data-bs-target="#metricsHelpModal" style="border: 1px solid rgba(255,255,255,0.3);">
                        <i class="fas fa-question-circle"></i>
                    </button>
                </div>
            </div>
            <div class="card-body pt-3" style="color: #2d3748; background: white;">
                
                <!-- Grade Level Assessment - Hero Section -->
                <div class="text-center mb-4 p-4 rounded-4" style="background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%); border: 2px solid #e2e8f0;">
                    <div class="d-flex justify-content-center align-items-center mb-3">
                        <div class="me-4">
                            <h1 class="mb-1 fw-bold" style="color: ${analysis.technical_writing_metrics?.meets_target_grade ? '#059669' : '#d97706'}; font-size: 2.5rem;">
                                ${analysis.technical_writing_metrics?.estimated_grade_level?.toFixed(1) || 'N/A'}
                            </h1>
                            <small class="text-muted fw-medium">Grade Level</small>
                        </div>
                        <div class="text-start">
                            <div class="badge fs-6 mb-2" style="background: ${analysis.technical_writing_metrics?.meets_target_grade ? 'linear-gradient(135deg, #10b981, #059669)' : 'linear-gradient(135deg, #f59e0b, #d97706)'}; color: white; padding: 8px 16px;">
                                ${analysis.technical_writing_metrics?.grade_level_category || 'Unknown'}
                            </div>
                            <div class="small d-flex align-items-center">
                                ${analysis.technical_writing_metrics?.meets_target_grade ? 
                                    '<i class="fas fa-check-circle me-2" style="color: #059669;"></i><span style="color: #059669;">Perfect for technical docs</span>' : 
                                    '<i class="fas fa-exclamation-triangle me-2" style="color: #d97706;"></i><span style="color: #d97706;">Outside target (9-11th grade)</span>'
                                }
                            </div>
                        </div>
                    </div>
                    <div class="small text-muted p-3 rounded-3" style="background: white; border: 1px solid #e2e8f0;">
                        ${getGradeLevelInsight(analysis.technical_writing_metrics?.estimated_grade_level, analysis.technical_writing_metrics?.meets_target_grade)}
                    </div>
                </div>

                <!-- Document Overview - Clean Modern Cards -->
                <div class="row g-3 mb-4">
                    <div class="col-4">
                        <div class="text-center p-3 rounded-3" style="background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);">
                            <h3 class="mb-1 fw-bold">${analysis.statistics.word_count || 0}</h3>
                            <small class="fw-medium">Words</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center p-3 rounded-3" style="background: linear-gradient(135deg, #06b6d4, #0891b2); color: white; box-shadow: 0 4px 12px rgba(6, 182, 212, 0.25);">
                            <h3 class="mb-1 fw-bold">${analysis.statistics.sentence_count || 0}</h3>
                            <small class="fw-medium">Sentences</small>
                        </div>
                    </div>
                    <div class="col-4">
                        <div class="text-center p-3 rounded-3" style="background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: white; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.25);">
                            <h3 class="mb-1 fw-bold">${Math.ceil((analysis.statistics.word_count || 0) / 250)}</h3>
                            <small class="fw-medium">Pages</small>
                        </div>
                    </div>
                </div>

                <!-- Readability Scores - Light Modern Cards -->
                <div class="mb-4">
                    <h6 class="text-center mb-3 fw-semibold d-flex align-items-center justify-content-center" style="color: #374151;">
                        <i class="fas fa-tachometer-alt me-2" style="color: #6366f1;"></i>Readability Metrics
                    </h6>
                    <div class="row g-2">
                        ${generateModernReadabilityCard('Flesch Score', analysis.statistics.flesch_reading_ease, 'Higher = easier to read', 'fas fa-book-open', getFleschColor(analysis.statistics.flesch_reading_ease))}
                        ${generateModernReadabilityCard('Fog Index', analysis.statistics.gunning_fog_index, 'Education years needed', 'fas fa-graduation-cap', getFogColor(analysis.statistics.gunning_fog_index))}
                        ${generateModernReadabilityCard('SMOG Grade', analysis.statistics.smog_index, 'School grade level', 'fas fa-school', getGradeColor(analysis.statistics.smog_index))}
                        ${generateModernReadabilityCard('ARI Score', analysis.statistics.automated_readability_index, 'Age to understand', 'fas fa-user-graduate', getGradeColor(analysis.statistics.automated_readability_index))}
                    </div>
                </div>

                <!-- Writing Quality - Light Background Progress Bars -->
                <div class="mb-4">
                    <h6 class="text-center mb-3 fw-semibold d-flex align-items-center justify-content-center" style="color: #374151;">
                        <i class="fas fa-clipboard-check me-2" style="color: #059669;"></i>Writing Quality
                    </h6>
                    
                    <!-- Modern Passive Voice Indicator -->
                    <div class="mb-3 p-3 rounded-3" style="background: rgba(59, 130, 246, 0.05); border: 1px solid rgba(59, 130, 246, 0.1);">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-exchange-alt me-2" style="color: #3b82f6;"></i>
                                <span class="fw-medium" style="color: #1f2937;">Passive Voice</span>
                                <span class="badge bg-light text-dark ms-2 rounded-pill" data-bs-toggle="tooltip" title="Keep under 15% for active writing" style="font-size: 0.7rem;">?</span>
                            </div>
                            <span class="fw-bold" style="color: #1f2937;">${(analysis.statistics.passive_voice_percentage || 0).toFixed(1)}%</span>
                        </div>
                        <div class="progress mb-2" style="height: 8px; background: rgba(59, 130, 246, 0.1); border-radius: 10px;">
                            <div class="progress-bar" 
                                 style="width: ${Math.min(100, (analysis.statistics.passive_voice_percentage || 0) * 6.67)}%; border-radius: 10px; background: ${getModernPassiveVoiceGradient(analysis.statistics.passive_voice_percentage)};"></div>
                        </div>
                        <div class="small" style="color: #6b7280;">
                            ${getPassiveVoiceInsight(analysis.statistics.passive_voice_percentage)}
                        </div>
                    </div>

                    <!-- Modern Sentence Length Indicator -->
                    <div class="mb-3 p-3 rounded-3" style="background: rgba(6, 182, 212, 0.05); border: 1px solid rgba(6, 182, 212, 0.1);">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-text-width me-2" style="color: #06b6d4;"></i>
                                <span class="fw-medium" style="color: #1f2937;">Sentence Length</span>
                                <span class="badge bg-light text-dark ms-2 rounded-pill" data-bs-toggle="tooltip" title="Aim for 15-20 words per sentence" style="font-size: 0.7rem;">?</span>
                            </div>
                            <span class="fw-bold" style="color: #1f2937;">${(analysis.statistics.avg_sentence_length || 0).toFixed(1)} words</span>
                        </div>
                        <div class="progress mb-2" style="height: 8px; background: rgba(6, 182, 212, 0.1); border-radius: 10px;">
                            <div class="progress-bar" 
                                 style="width: ${Math.min(100, (analysis.statistics.avg_sentence_length || 0) * 2.5)}%; border-radius: 10px; background: ${getModernSentenceLengthGradient(analysis.statistics.avg_sentence_length)};"></div>
                        </div>
                        <div class="small" style="color: #6b7280;">
                            ${getSentenceLengthInsight(analysis.statistics.avg_sentence_length)}
                        </div>
                    </div>

                    <!-- Modern Word Complexity Indicator -->
                    <div class="mb-3 p-3 rounded-3" style="background: rgba(139, 92, 246, 0.05); border: 1px solid rgba(139, 92, 246, 0.1);">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-brain me-2" style="color: #8b5cf6;"></i>
                                <span class="fw-medium" style="color: #1f2937;">Complex Words</span>
                                <span class="badge bg-light text-dark ms-2 rounded-pill" data-bs-toggle="tooltip" title="Words with 3+ syllables" style="font-size: 0.7rem;">?</span>
                            </div>
                            <span class="fw-bold" style="color: #1f2937;">${(analysis.statistics.complex_words_percentage || 0).toFixed(1)}%</span>
                        </div>
                        <div class="progress mb-2" style="height: 8px; background: rgba(139, 92, 246, 0.1); border-radius: 10px;">
                            <div class="progress-bar" 
                                 style="width: ${Math.min(100, (analysis.statistics.complex_words_percentage || 0) * 3.33)}%; border-radius: 10px; background: ${getModernComplexWordsGradient(analysis.statistics.complex_words_percentage)};"></div>
                        </div>
                        <div class="small" style="color: #6b7280;">
                            ${getComplexWordsInsight(analysis.statistics.complex_words_percentage)}
                        </div>
                    </div>
                </div>

                <!-- Smart Recommendations - Clean Modern Design -->
                <div class="mt-4">
                    <h6 class="text-center mb-3 fw-semibold d-flex align-items-center justify-content-center" style="color: #374151;">
                        <i class="fas fa-lightbulb me-2" style="color: #f59e0b;"></i>Smart Recommendations
                    </h6>
                    <div class="smart-recommendations">
                        ${generateModernSmartRecommendations(analysis)}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// HTML escape utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Safe HTML renderer for table cells - allows common formatting tags
function renderSafeTableCellHtml(text) {
    if (!text) return '';
    
    // First escape all HTML to be safe
    let escaped = escapeHtml(text);
    
    // Then selectively un-escape safe formatting tags
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

// Helper functions for statistics card
function getGradeLevelInsight(gradeLevel, meetsTarget) {
    if (!gradeLevel) return 'Grade level could not be determined.';
    
    if (meetsTarget) {
        return 'Perfect! Your content is accessible to your target technical audience.';
    } else if (gradeLevel < 9) {
        return 'Content may be too simple for technical documentation.';
    } else {
        return 'Consider simplifying complex sentences for better accessibility.';
    }
}

function generateModernReadabilityCard(title, value, description, icon, color) {
    return `
        <div class="col-6 mb-2">
            <div class="text-center p-2 rounded-3" style="background: ${color}; color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <div class="d-flex align-items-center justify-content-center mb-1">
                    <i class="${icon} me-2" style="font-size: 0.9rem;"></i>
                    <span class="fw-bold" style="font-size: 1.1rem;">${(value || 0).toFixed(1)}</span>
                </div>
                <div class="small fw-medium">${title}</div>
                <div class="small opacity-75" style="font-size: 0.7rem;">${description}</div>
            </div>
        </div>
    `;
}

function getFleschColor(score) {
    if (score >= 70) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score >= 50) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getFogColor(score) {
    if (score <= 12) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score <= 16) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getGradeColor(score) {
    if (score <= 12) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score <= 16) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernPassiveVoiceGradient(percentage) {
    if (percentage <= 15) return 'linear-gradient(135deg, #10b981, #059669)';
    if (percentage <= 25) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernSentenceLengthGradient(length) {
    if (length >= 15 && length <= 20) return 'linear-gradient(135deg, #10b981, #059669)';
    if (length <= 25) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernComplexWordsGradient(percentage) {
    if (percentage <= 20) return 'linear-gradient(135deg, #10b981, #059669)';
    if (percentage <= 30) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getPassiveVoiceInsight(percentage) {
    if (percentage <= 15) return 'Excellent active voice usage!';
    if (percentage <= 25) return 'Consider reducing passive voice usage.';
    return 'Too much passive voice. Rewrite for active voice.';
}

function getSentenceLengthInsight(length) {
    if (length >= 15 && length <= 20) return 'Perfect sentence length for technical writing!';
    if (length < 15) return 'Sentences might be too short. Consider combining some.';
    return 'Sentences are too long. Break them down for clarity.';
}

function getComplexWordsInsight(percentage) {
    if (percentage <= 20) return 'Good balance of complex and simple words.';
    if (percentage <= 30) return 'Consider simplifying some complex terms.';
    return 'Too many complex words may hurt readability.';
}

function generateModernSmartRecommendations(analysis) {
    const recommendations = [];
    
    // Add recommendations based on analysis
    if (analysis.statistics.passive_voice_percentage > 25) {
        recommendations.push('🎯 Reduce passive voice usage for clearer, more direct writing');
    }
    
    if (analysis.statistics.avg_sentence_length > 25) {
        recommendations.push('📝 Break down long sentences for better readability');
    }
    
    if (analysis.statistics.complex_words_percentage > 30) {
        recommendations.push('💡 Simplify complex terms where possible');
    }
    
    if (analysis.statistics.flesch_reading_ease < 50) {
        recommendations.push('📚 Improve readability with shorter sentences and simpler words');
    }
    
    if (recommendations.length === 0) {
        recommendations.push('✨ Excellent writing! Your content meets technical writing standards.');
    }
    
    return recommendations.map(rec => `
        <div class="alert alert-light border-start border-primary border-3 py-2 px-3 mb-2">
            <small class="text-dark">${rec}</small>
        </div>
    `).join('');
}
