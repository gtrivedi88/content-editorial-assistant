/**
 * Integration Validation Test
 * Quick smoke test to ensure all components are working together
 */

// Simple integration validation
function validateSmartFilterIntegration() {
    const results = {
        smartFilterSystemLoaded: false,
        smartFilterChipsLoaded: false,
        basicFilteringWorks: false,
        uiComponentsGenerate: false,
        integrationComplete: false
    };
    
    try {
        // Check if SmartFilterSystem is loaded
        if (typeof SmartFilterSystem !== 'undefined') {
            results.smartFilterSystemLoaded = true;
            console.log('✅ SmartFilterSystem loaded');
        }
        
        // Check if SmartFilterChips is loaded
        if (window.SmartFilterChips) {
            results.smartFilterChipsLoaded = true;
            console.log('✅ SmartFilterChips loaded');
        }
        
        // Test basic filtering
        if (window.SmartFilterSystem) {
            const testErrors = [
                { confidence: 0.9, type: 'test', message: 'Critical test' },
                { confidence: 0.6, type: 'test', message: 'Warning test' }
            ];
            
            const filtered = window.SmartFilterSystem.applyFilters(testErrors);
            if (filtered.length === 2) {
                results.basicFilteringWorks = true;
                console.log('✅ Basic filtering works');
            }
        }
        
        // Test UI component generation
        if (window.SmartFilterChips) {
            const testCounts = { critical: 1, error: 0, warning: 1, suggestion: 0 };
            const testFilters = new Set(['critical', 'warning']);
            
            const html = window.SmartFilterChips.createSmartFilterChips(testCounts, testFilters);
            if (html && html.includes('smart-filter-container')) {
                results.uiComponentsGenerate = true;
                console.log('✅ UI components generate correctly');
            }
        }
        
        // Overall integration check
        results.integrationComplete = Object.values(results).slice(0, 4).every(Boolean);
        
        if (results.integrationComplete) {
            console.log('🎉 Smart Filter System integration validation PASSED!');
        } else {
            console.error('❌ Smart Filter System integration validation FAILED');
            console.error('Results:', results);
        }
        
    } catch (error) {
        console.error('❌ Integration validation error:', error);
        results.integrationComplete = false;
    }
    
    return results;
}

// Run validation when script loads
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', function() {
        setTimeout(validateSmartFilterIntegration, 100);
    });
}

console.log('🧪 Integration validation script loaded');
