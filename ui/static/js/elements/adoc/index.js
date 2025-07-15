/**
 * AsciiDoc Element Modules - Main Index
 * Loads all element-specific modules and initializes the registry system
 */

// This file serves as the entry point for the AsciiDoc element module system
// It ensures all modules are loaded in the correct order

console.log('[AsciiDoc Elements] Loading element modules...');

// The modules will be loaded via individual script tags in the HTML
// This file just provides a convenient way to ensure everything is initialized

/**
 * Verify all required modules are loaded
 * @returns {Object} Status of module loading
 */
function verifyModuleLoading() {
    const requiredFunctions = [
        // Registry system
        'AsciiDocElementRegistry',
        'initializeAsciiDocElements',
        'createModularBlock',
        
        // Element modules
        'createTitleBlock', 'canHandleTitle',
        'createParagraphBlock', 'canHandleParagraph',
        'createAdmonitionBlock', 'canHandleAdmonition',
        'createCodeBlockElement', 'canHandleCodeBlock',
        'createListBlockElement', 'canHandleList',
        'createTableBlockElement', 'canHandleTable',
        'createDelimitedBlockElement', 'canHandleDelimitedBlock',
        'createSectionBlockElement', 'canHandleSection',
        'createProcedureBlockElement', 'canHandleProcedure'
    ];

    const missing = [];
    const available = [];

    requiredFunctions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            available.push(funcName);
        } else {
            missing.push(funcName);
        }
    });

    return {
        total: requiredFunctions.length,
        available: available.length,
        missing: missing.length,
        missingFunctions: missing,
        availableFunctions: available,
        isComplete: missing.length === 0
    };
}

/**
 * Initialize the complete AsciiDoc element system
 * @returns {Object} Initialization result
 */
function initializeCompleteSystem() {
    console.log('[AsciiDoc Elements] Starting complete system initialization...');
    
    const moduleStatus = verifyModuleLoading();
    console.log('[AsciiDoc Elements] Module loading status:', moduleStatus);
    
    if (!moduleStatus.isComplete) {
        console.warn('[AsciiDoc Elements] Some modules are missing:', moduleStatus.missingFunctions);
    }
    
    // Initialize the registry system
    let registry = null;
    try {
        registry = initializeAsciiDocElements();
        console.log('[AsciiDoc Elements] Registry initialized successfully');
    } catch (error) {
        console.error('[AsciiDoc Elements] Failed to initialize registry:', error);
        return { success: false, error: error.message };
    }
    
    return {
        success: true,
        registry: registry,
        moduleStatus: moduleStatus,
        stats: registry ? registry.getStats() : null
    };
}

// Export for global access
if (typeof window !== 'undefined') {
    window.verifyModuleLoading = verifyModuleLoading;
    window.initializeCompleteSystem = initializeCompleteSystem;
}

// Auto-initialize when loaded
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(initializeCompleteSystem, 100); // Small delay to ensure all modules are loaded
        });
    } else {
        // DOM already loaded
        setTimeout(initializeCompleteSystem, 100);
    }
}

console.log('[AsciiDoc Elements] Index module loaded'); 