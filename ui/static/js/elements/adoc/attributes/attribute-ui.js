/**
 * AsciiDoc Attribute Block UI Module
 * Handles rendering of skipped attribute blocks with placeholders
 */

/**
 * Create an attribute block placeholder display
 * @param {Object} block - The attribute block data (or placeholder info)
 * @param {number} displayIndex - Display index for the block
 * @returns {string} HTML string for the attribute block placeholder
 */
function createAttributeBlock(block, displayIndex) {
    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered" style="border-left: 4px solid var(--pf-v5-global--Color--300);">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="fas fa-cog pf-v5-u-mr-sm" style="color: var(--pf-v5-global--Color--300);"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">Attribute Block</span>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-grey">
                        <span class="pf-v5-c-label__content">Skipped</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-empty-state pf-m-sm">
                    <div class="pf-v5-c-empty-state__content">
                        <i class="fas fa-ban pf-v5-c-empty-state__icon" style="color: var(--pf-v5-global--Color--300);"></i>
                        <h3 class="pf-v5-c-title pf-m-md">Attribute block - skipped scanning</h3>
                        <div class="pf-v5-c-empty-state__body">
                            Document metadata and configuration attributes are not analyzed for style issues.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Detect attribute patterns in content and insert placeholder after title
 * @param {string} content - Original content to scan
 * @param {Array} blocks - Existing structural blocks
 * @returns {Array} Blocks with attribute placeholders inserted
 */
function insertAttributePlaceholders(content, blocks) {
    if (!content || !blocks.length) return blocks;
    
    // Find the first title/heading block
    const titleIndex = blocks.findIndex(block => 
        block.block_type === 'heading' || block.block_type === 'title'
    );
    
    if (titleIndex === -1) return blocks;
    
    // Check if there are attribute patterns after the title
    const hasAttributeBlock = detectAttributePatternsAfterTitle(content);
    if (!hasAttributeBlock) return blocks;
    
    // Insert attribute placeholder after the title
    const blocksWithPlaceholder = [...blocks];
    blocksWithPlaceholder.splice(titleIndex + 1, 0, {
        isAttributePlaceholder: true,
        block_type: 'attribute_placeholder',
        content: 'Skipped attribute block'
    });
    
    return blocksWithPlaceholder;
}

/**
 * Detect if there are attribute patterns after the title in the content
 * @param {string} content - Content to scan
 * @returns {boolean} True if attribute patterns are found after title
 */
function detectAttributePatternsAfterTitle(content) {
    const lines = content.split('\n');
    let foundTitle = false;
    let attributeCount = 0;
    
    for (const line of lines) {
        const trimmed = line.trim();
        
        // Skip until we find the title
        if (!foundTitle && trimmed.startsWith('=')) {
            foundTitle = true;
            continue;
        }
        
        if (!foundTitle) continue;
        
        // After title, look for attribute patterns
        if (isAttributeLine(trimmed)) {
            attributeCount++;
        } else if (trimmed && !isWhiteSpaceOrEmpty(trimmed)) {
            // Hit non-attribute content, stop scanning
            break;
        }
    }
    
    return attributeCount > 0;
}

/**
 * Check if a line is an attribute line
 * @param {string} line - Line to check
 * @returns {boolean} True if line is an attribute
 */
function isAttributeLine(line) {
    // AsciiDoc attribute entry pattern: :attribute-name: value
    if (/^:[a-zA-Z][\w-]*:\s*/.test(line)) return true;
    
    // Author line pattern: Name <email>
    if (/^[^<>\n]+\s*<[^<>\s]+@[^<>\s]+>/.test(line)) return true;
    
    // Revision line pattern: v1.0, date: description
    if (/^v?\d+\.[\d.]+\s*,/.test(line)) return true;
    
    // Negated attribute pattern: :!attribute:
    if (/^:![a-zA-Z][\w-]*:/.test(line)) return true;
    
    return false;
}

/**
 * Check if a line is whitespace or empty
 * @param {string} line - Line to check
 * @returns {boolean} True if line is whitespace or empty
 */
function isWhiteSpaceOrEmpty(line) {
    return !line || line.trim() === '';
}

/**
 * Check if this module can handle the given block type
 * @param {Object} block - Block to check
 * @returns {boolean} True if this module can handle the block
 */
function canHandleAttribute(block) {
    return block.block_type === 'attribute_placeholder' || block.isAttributePlaceholder;
}

// Make functions globally available
if (typeof window !== 'undefined') {
    window.createAttributeBlock = createAttributeBlock;
    window.insertAttributePlaceholders = insertAttributePlaceholders;
    window.canHandleAttribute = canHandleAttribute;
}

// Export functions for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        createAttributeBlock,
        insertAttributePlaceholders,
        canHandleAttribute
    };
} 