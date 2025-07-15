/**
 * AsciiDoc Element Bootstrap Module
 * Automatically loads and registers all element modules
 */

/**
 * Initialize and register all AsciiDoc element modules
 */
function initializeAsciiDocElements() {
    console.log('[AsciiDoc Bootstrap] Initializing element modules...');
    
    // Get or create the global registry
    const registry = window.AsciiDocElementRegistry || new AsciiDocElementRegistry();
    
    // Register all element modules
    registerAllModules(registry);
    
    // Set up fallback handler (simple generic block creator to avoid circular reference)
    registry.setFallbackHandler((block, displayIndex) => {
        // Use the registry's built-in generic block creator
        return registry.createGenericBlock(block, displayIndex);
    });
    
    // Store registry globally
    window.AsciiDocElementRegistry = registry;
    
    console.log('[AsciiDoc Bootstrap] Initialization complete:', registry.getStats());
    
    return registry;
}

/**
 * Register all available element modules
 * @param {AsciiDocElementRegistry} registry - The registry to register modules with
 */
function registerAllModules(registry) {
    // Note: In a real implementation, these modules would be loaded dynamically
    // For now, we assume they're already loaded via script tags
    
    const moduleConfigs = [
        {
            type: 'titles',
            checkGlobal: () => typeof createTitleBlock === 'function' && typeof canHandleTitle === 'function',
            module: () => ({ createTitleBlock, canHandleTitle })
        },
        {
            type: 'paragraphs',
            checkGlobal: () => typeof createParagraphBlock === 'function' && typeof canHandleParagraph === 'function',
            module: () => ({ createParagraphBlock, canHandleParagraph })
        },
        {
            type: 'admonitions',
            checkGlobal: () => typeof createAdmonitionBlock === 'function' && typeof canHandleAdmonition === 'function',
            module: () => ({ createAdmonitionBlock, canHandleAdmonition })
        },
        {
            type: 'code_blocks',
            checkGlobal: () => typeof createCodeBlockElement === 'function' && typeof canHandleCodeBlock === 'function',
            module: () => ({ createCodeBlockElement, canHandleCodeBlock })
        },
        {
            type: 'lists',
            checkGlobal: () => typeof createListBlockElement === 'function' && typeof canHandleList === 'function',
            module: () => ({ createListBlockElement, canHandleList })
        },
        {
            type: 'tables',
            checkGlobal: () => typeof createTableBlockElement === 'function' && typeof canHandleTable === 'function',
            module: () => ({ createTableBlockElement, parseTableContent, canHandleTable })
        },
        {
            type: 'delimited_blocks',
            checkGlobal: () => typeof createDelimitedBlockElement === 'function' && typeof canHandleDelimitedBlock === 'function',
            module: () => ({ createDelimitedBlockElement, canHandleDelimitedBlock })
        },
        {
            type: 'sections',
            checkGlobal: () => typeof createSectionBlockElement === 'function' && typeof canHandleSection === 'function',
            module: () => ({ createSectionBlockElement, canHandleSection })
        },
        {
            type: 'procedures',
            checkGlobal: () => typeof createProcedureBlockElement === 'function' && typeof canHandleProcedure === 'function',
            module: () => ({ createProcedureBlockElement, generateProcedureSteps, canHandleProcedure })
        }
    ];

    moduleConfigs.forEach(config => {
        try {
            if (config.checkGlobal()) {
                const module = config.module();
                registry.registerModule(config.type, module);
            } else {
                console.warn(`[AsciiDoc Bootstrap] Module ${config.type} not available (functions not found)`);
            }
        } catch (error) {
            console.error(`[AsciiDoc Bootstrap] Error registering ${config.type} module:`, error);
        }
    });
}

/**
 * Create a modular block using the registry system
 * @param {Object} block - Block data
 * @param {number} displayIndex - Display index
 * @returns {string} HTML string for the block
 */
function createModularBlock(block, displayIndex) {
    const registry = window.AsciiDocElementRegistry;
    
    if (!registry) {
        console.error('[AsciiDoc Bootstrap] Registry not initialized, using basic fallback');
        // Simple fallback without circular reference
        const blockType = block.block_type || 'unknown';
        const issueCount = block.errors ? block.errors.length : 0;
        const status = issueCount > 0 ? 'red' : 'green';
        const statusText = issueCount > 0 ? `${issueCount} Issue(s)` : 'Clean';
        
        return `
            <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top" id="block-${displayIndex}">
                <div class="pf-v5-c-card__header">
                    <div class="pf-v5-c-card__header-main">
                        <i class="fas fa-exclamation-triangle pf-v5-u-mr-sm"></i>
                        <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                        <span class="pf-v5-u-ml-sm">${blockType} (Fallback)</span>
                    </div>
                    <div class="pf-v5-c-card__actions">
                        <span class="pf-v5-c-label pf-m-outline pf-m-${status}">
                            <span class="pf-v5-c-label__content">${statusText}</span>
                        </span>
                    </div>
                </div>
                <div class="pf-v5-c-card__body">
                    <div class="pf-v5-u-p-md pf-v5-u-background-color-200" style="white-space: pre-wrap; word-wrap: break-word; border-radius: var(--pf-v5-global--BorderRadius--sm);">
                        ${escapeHtml ? escapeHtml(block.content || 'No content') : (block.content || 'No content')}
                    </div>
                </div>
            </div>
        `;
    }
    
    return registry.createBlockHtml(block, displayIndex);
}

/**
 * Get registry statistics for debugging
 * @returns {Object} Registry statistics
 */
function getElementRegistryStats() {
    const registry = window.AsciiDocElementRegistry;
    return registry ? registry.getStats() : { error: 'Registry not initialized' };
}

// Auto-initialize when DOM is ready
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeAsciiDocElements);
    } else {
        // DOM already loaded
        initializeAsciiDocElements();
    }
}

// Export functions for global use
if (typeof window !== 'undefined') {
    window.initializeAsciiDocElements = initializeAsciiDocElements;
    window.createModularBlock = createModularBlock;
    window.getElementRegistryStats = getElementRegistryStats;
}

// Export for module system
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        initializeAsciiDocElements,
        createModularBlock,
        getElementRegistryStats
    };
} 