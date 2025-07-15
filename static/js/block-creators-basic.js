/**
 * Basic Block Creators Module - Basic Block Creation Functions
 * Handles structural block creation, sections, and generic block types
 */

// Create a structural block display with world-class design (main dispatcher)
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
    
    // Handle section blocks specially - display section + children
    if (block.block_type === 'section') {
        return createSectionBlock(block, displayIndex);
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
        'admonition': 'fas fa-info-circle',
        'listing': 'fas fa-code',
        'literal': 'fas fa-terminal',
        'quote': 'fas fa-quote-left',
        'sidebar': 'fas fa-columns',
        'example': 'fas fa-lightbulb',
        'verse': 'fas fa-feather',
        'attribute_entry': 'fas fa-cog',
        'comment': 'fas fa-comment',
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

// Create a section block with its children displayed recursively
function createSectionBlock(block, displayIndex) {
    const style = {
        gradient: 'linear-gradient(135deg, #4f46e5 0%, #3730a3 100%)',
        bgColor: '#f8fafc',
        borderColor: '#e2e8f0',
        textColor: '#1e293b',
        accentColor: '#4f46e5'
    };
    
    const blockTitle = getBlockTypeDisplayName(block.block_type, {
        level: block.level,
        admonition_type: block.admonition_type
    });
    
    // Count issues in section and all children
    let totalIssues = 0;
    if (block.errors) totalIssues += block.errors.length;
    
    const countChildIssues = (children) => {
        if (!children) return;
        children.forEach(child => {
            if (child.errors) totalIssues += child.errors.length;
            if (child.children) countChildIssues(child.children);
        });
    };
    countChildIssues(block.children);
    
    // Generate children HTML with updated display indices
    let childrenHtml = '';
    let childDisplayIndex = 0;
    
    if (block.children && block.children.length > 0) {
        childrenHtml = block.children.map(child => {
            const html = createStructuralBlock(child, childDisplayIndex);
            if (html !== '') {
                childDisplayIndex++;
            }
            return html;
        }).filter(html => html !== '').join('');
    }
    
    return `
        <div class="structural-section mb-4" style="
            border-radius: 16px;
            overflow: hidden;
            background: white;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            border: 1px solid ${style.borderColor};
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        ">
            <!-- Section header -->
            <div class="section-header d-flex justify-content-between align-items-center p-3" style="
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
                        <i class="fas fa-layer-group" style="font-size: 18px;"></i>
                    </div>
                    <div>
                        <h6 class="mb-0 fw-bold" style="font-size: 14px; letter-spacing: 0.5px;">
                            SECTION ${displayIndex + 1}: ${blockTitle}
                        </h6>
                        <small class="opacity-90" style="font-size: 12px;">
                            ${block.children ? block.children.length : 0} child blocks • ${totalIssues} ${totalIssues === 1 ? 'issue' : 'issues'} total
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
            
            <!-- Section content and children -->
            <div class="section-content p-4" style="background: ${style.bgColor};">
                ${block.content && block.content.trim() !== '' ? `
                    <div class="section-text mb-4" style="
                        background: white;
                        border: 1px solid ${style.borderColor};
                        border-radius: 12px;
                        padding: 20px;
                        font-size: 14px;
                        line-height: 1.6;
                        color: #1f2937;
                        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
                    ">
                        <div class="d-flex align-items-center mb-3">
                            <div class="me-3 d-flex align-items-center justify-content-center" style="
                                width: 32px;
                                height: 32px;
                                background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
                                border-radius: 8px;
                            ">
                                <i class="fas fa-align-left" style="color: ${style.accentColor}; font-size: 14px;"></i>
                            </div>
                            <h6 class="mb-0 fw-bold" style="color: ${style.accentColor}; font-size: 14px;">
                                Section Content
                            </h6>
                        </div>
                        ${escapeHtml(block.content)}
                    </div>
                ` : ''}
                
                ${childrenHtml !== '' ? `
                    <div class="section-children">
                        <div class="d-flex align-items-center mb-3">
                            <div class="me-3 d-flex align-items-center justify-content-center" style="
                                width: 32px;
                                height: 32px;
                                background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
                                border-radius: 8px;
                            ">
                                <i class="fas fa-sitemap" style="color: ${style.accentColor}; font-size: 14px;"></i>
                            </div>
                            <h6 class="mb-0 fw-bold" style="color: ${style.accentColor}; font-size: 14px;">
                                Section Blocks (${block.children ? block.children.length : 0})
                            </h6>
                        </div>
                        ${childrenHtml}
                    </div>
                ` : ''}
                
                ${block.errors && block.errors.length > 0 ? `
                    <div class="section-errors mt-3" style="
                        background: white;
                        border: 1px solid #fecaca;
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
                                <i class="fas fa-exclamation-triangle" style="color: #dc2626; font-size: 14px;"></i>
                            </div>
                            <div>
                                <h6 class="mb-0 fw-bold" style="color: #dc2626; font-size: 14px;">
                                    Section-Level Issues (${block.errors.length})
                                </h6>
                                <small style="color: #6b7280;">Issues affecting the section structure</small>
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