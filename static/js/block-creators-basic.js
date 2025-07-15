/**
 * Basic Block Creators Module - PatternFly Version
 * Handles structural block creation using PatternFly Card components.
 */

// Create a structural block display using a PatternFly Card
function createStructuralBlock(block, displayIndex) {
    // Dispatch to specialized functions for complex types
    if (block.block_type === 'unordered_list' || block.block_type === 'ordered_list') return createListBlock(block, displayIndex);
    if (block.block_type === 'table') return createTableBlock(block, displayIndex);
    if (block.block_type === 'section') return createSectionBlock(block, displayIndex);
    if (['list_item', 'list_title', 'table_row', 'table_cell'].includes(block.block_type)) return '';

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
                             <h3 class="pf-v5-c-title pf-m-md">Analysis Skipped</h3>
                             <div class="pf-v5-c-empty-state__body">Code blocks and attributes are not analyzed for style issues.</div>
                        </div>
                    </div>` :
                    `<div class="pf-v5-u-p-md pf-v5-u-background-color-200" style="white-space: pre-wrap; word-wrap: break-word; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                        ${escapeHtml(block.content)}
                    </div>`
                }
            </div>
            ${!block.should_skip_analysis && issueCount > 0 ? `
            <div class="pf-v5-c-card__footer">
                <div class="pf-v5-l-stack pf-m-gutter">
                    ${(block.errors || []).map(error => createInlineError(error)).join('')}
                </div>
            </div>` : ''}
        </div>
    `;
}

// Create a section block (which is also a card containing other cards)
function createSectionBlock(block, displayIndex) {
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

// Get a human-readable display name for a block type
function getBlockTypeDisplayName(blockType, context) {
    const { level, admonition_type } = context;
    const names = {
        'heading': `Heading (Level ${level})`, 'paragraph': 'Paragraph', 'admonition': `Admonition (${admonition_type || 'NOTE'})`,
        'listing': 'Code Block', 'literal': 'Literal Block', 'quote': 'Quote', 'sidebar': 'Sidebar', 'example': 'Example',
        'verse': 'Verse', 'attribute_entry': 'Attribute', 'comment': 'Comment', 'table': 'Table', 'image': 'Image',
        'audio': 'Audio', 'video': 'Video', 'section': 'Section', 'ordered_list': 'Ordered List', 'unordered_list': 'Unordered List',
        'list_item': 'List Item', 'list_title': 'List Title'
    };
    return names[blockType] || blockType.replace(/_/g, ' ').toUpperCase();
}
