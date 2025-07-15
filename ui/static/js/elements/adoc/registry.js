/**
 * AsciiDoc Element Registry
 * Central registry for managing element-specific UI modules
 */

class AsciiDocElementRegistry {
    constructor() {
        this.elementModules = new Map();
        this.loadedModules = new Set();
        this.fallbackHandler = null;
    }

    /**
     * Register an element module
     * @param {string} elementType - The element type (e.g., 'title', 'paragraph')
     * @param {Object} module - The module containing UI functions
     */
    registerModule(elementType, module) {
        this.elementModules.set(elementType, module);
        this.loadedModules.add(elementType);
        console.log(`[AsciiDoc Registry] Registered ${elementType} module`);
    }

    /**
     * Get the appropriate module for a block type
     * @param {Object} block - The block to find a handler for
     * @returns {Object|null} The module that can handle this block, or null
     */
    getModuleForBlock(block) {
        if (!block || !block.block_type) {
            return null;
        }

        // Try each registered module to see if it can handle this block
        for (const [elementType, module] of this.elementModules) {
            try {
                const canHandleMethod = this.getCanHandleMethod(module);
                if (canHandleMethod && canHandleMethod(block)) {
                    return module;
                }
            } catch (error) {
                console.warn(`[AsciiDoc Registry] Error checking if ${elementType} can handle block:`, error);
            }
        }

        return null;
    }

    /**
     * Get the 'canHandle' method from a module
     * @param {Object} module - The module to check
     * @returns {Function|null} The canHandle function or null
     */
    getCanHandleMethod(module) {
        // Try different naming patterns for the canHandle method
        const possibleMethods = [
            'canHandleTitle', 'canHandleParagraph', 'canHandleAdmonition',
            'canHandleCodeBlock', 'canHandleList', 'canHandleTable',
            'canHandleDelimitedBlock', 'canHandleSection', 'canHandleProcedure'
        ];

        for (const methodName of possibleMethods) {
            if (typeof module[methodName] === 'function') {
                return module[methodName];
            }
        }

        // Fallback to generic canHandle method
        if (typeof module.canHandle === 'function') {
            return module.canHandle;
        }

        return null;
    }

    /**
     * Create HTML for a block using the appropriate module
     * @param {Object} block - The block to render
     * @param {number} displayIndex - Display index for the block
     * @returns {string} HTML string for the block
     */
    createBlockHtml(block, displayIndex) {
        const module = this.getModuleForBlock(block);
        
        if (module) {
            try {
                const createMethod = this.getCreateMethod(module);
                if (createMethod) {
                    return createMethod(block, displayIndex);
                }
            } catch (error) {
                console.error(`[AsciiDoc Registry] Error creating HTML for block:`, error);
            }
        }

        // Fall back to default handler or generic block creation
        if (this.fallbackHandler) {
            return this.fallbackHandler(block, displayIndex);
        }

        return this.createGenericBlock(block, displayIndex);
    }

    /**
     * Get the 'create' method from a module
     * @param {Object} module - The module to check
     * @returns {Function|null} The create function or null
     */
    getCreateMethod(module) {
        // Try different naming patterns for the create method
        const possibleMethods = [
            'createTitleBlock', 'createParagraphBlock', 'createAdmonitionBlock',
            'createCodeBlockElement', 'createListBlockElement', 'createTableBlockElement',
            'createDelimitedBlockElement', 'createSectionBlockElement', 'createProcedureBlockElement'
        ];

        for (const methodName of possibleMethods) {
            if (typeof module[methodName] === 'function') {
                return module[methodName];
            }
        }

        // Fallback to generic create method
        if (typeof module.create === 'function') {
            return module.create;
        }

        return null;
    }

    /**
     * Create a generic block when no specific module is found
     * @param {Object} block - The block data
     * @param {number} displayIndex - Display index for the block
     * @returns {string} HTML string for generic block
     */
    createGenericBlock(block, displayIndex) {
        const blockType = block.block_type || 'unknown';
        const issueCount = block.errors ? block.errors.length : 0;
        const status = issueCount > 0 ? 'red' : 'green';
        const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';

        return `
            <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
                <div class="pf-v5-c-card__header">
                    <div class="pf-v5-c-card__header-main">
                        <i class="fas fa-file-alt pf-v5-u-mr-sm"></i>
                        <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                        <span class="pf-v5-u-ml-sm">${blockType}</span>
                        <span class="pf-v5-c-label pf-m-compact pf-m-orange pf-v5-u-ml-sm">No handler</span>
                    </div>
                    <div class="pf-v5-c-card__actions">
                        <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                            <span class="pf-v5-c-label__content">${statusText}</span>
                        </span>
                    </div>
                </div>
                <div class="pf-v5-c-card__body">
                    <div class="pf-v5-u-p-md pf-v5-u-background-color-200" style="white-space: pre-wrap; word-wrap: break-word; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                        ${escapeHtml(block.content || 'No content')}
                    </div>
                </div>
                ${issueCount > 0 ? `
                <div class="pf-v5-c-card__footer">
                    <div class="pf-v5-l-stack pf-m-gutter">
                        ${(block.errors || []).map(error => createInlineError(error)).join('')}
                    </div>
                </div>` : ''}
            </div>
        `;
    }

    /**
     * Set a fallback handler for unknown block types
     * @param {Function} handler - Fallback handler function
     */
    setFallbackHandler(handler) {
        this.fallbackHandler = handler;
    }

    /**
     * Get statistics about registered modules
     * @returns {Object} Registry statistics
     */
    getStats() {
        return {
            totalModules: this.elementModules.size,
            loadedModules: Array.from(this.loadedModules),
            availableTypes: Array.from(this.elementModules.keys())
        };
    }
}

// Create global registry instance
if (typeof window !== 'undefined') {
    window.AsciiDocElementRegistry = window.AsciiDocElementRegistry || new AsciiDocElementRegistry();
}

// Export for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AsciiDocElementRegistry;
} 