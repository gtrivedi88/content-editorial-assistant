/**
 * Complex Block Creators Module - List and Table Creation Functions
 * Handles complex block types like lists, tables, and list titles
 */

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

// Create simplified table block (table creation is too complex for this limit)
// Full table implementation will be part of a separate tables-display.js module
function createTableBlock(block, displayIndex) {
    return `
        <div class="table-placeholder mb-4 p-4 border rounded" style="background: #f8f9fa;">
            <div class="text-center">
                <i class="fas fa-table fa-2x mb-3" style="color: #6c757d;"></i>
                <h6>Table Block ${displayIndex + 1}</h6>
                <p class="text-muted small">Complex table rendering moved to tables-display.js module</p>
                <div class="badge bg-info">Modularization in Progress</div>
            </div>
        </div>
    `;
} 