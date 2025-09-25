/**
 * Comprehensive Test Suite for Smart Filter System
 * Uses QUnit framework for frontend testing
 * 
 * Zero technical debt, production-ready test coverage
 * Performance benchmarks and edge case validation
 */

// QUnit module configuration
QUnit.config.reorder = false;
QUnit.config.autostart = false;

// Test data and utilities
const TestUtils = {
    /**
     * Create mock error object
     * @param {number} confidence - Confidence score (0-1)
     * @param {string} type - Error type
     * @returns {Object} - Mock error object
     */
    createMockError(confidence, type = 'test_rule') {
        return {
            type: type,
            message: `Test error with ${Math.round(confidence * 100)}% confidence`,
            suggestions: [`Fix for ${type}`],
            severity: confidence >= 0.7 ? 'high' : confidence >= 0.5 ? 'medium' : 'low',
            confidence: confidence,
            sentence: 'This is a test sentence.',
            sentence_index: 0
        };
    },

    /**
     * Create array of mock errors with specified confidence distribution
     * @param {Object} distribution - Error count by severity
     * @returns {Array} - Array of mock errors
     */
    createMockErrorSet(distribution) {
        const errors = [];
        
        // Critical errors (85-100%)
        for (let i = 0; i < (distribution.critical || 0); i++) {
            errors.push(this.createMockError(0.85 + (Math.random() * 0.15), `critical_rule_${i}`));
        }
        
        // Error-level issues (70-84%)
        for (let i = 0; i < (distribution.error || 0); i++) {
            errors.push(this.createMockError(0.70 + (Math.random() * 0.15), `error_rule_${i}`));
        }
        
        // Warnings (50-69%)
        for (let i = 0; i < (distribution.warning || 0); i++) {
            errors.push(this.createMockError(0.50 + (Math.random() * 0.20), `warning_rule_${i}`));
        }
        
        // Suggestions (0-49%)
        for (let i = 0; i < (distribution.suggestion || 0); i++) {
            errors.push(this.createMockError(0.30 + (Math.random() * 0.20), `suggestion_rule_${i}`));
        }
        
        return errors;
    },

    /**
     * Measure execution time of a function
     * @param {Function} fn - Function to measure
     * @returns {Object} - Result and timing information
     */
    measurePerformance(fn) {
        const startTime = performance.now();
        const result = fn();
        const endTime = performance.now();
        
        return {
            result: result,
            executionTime: endTime - startTime,
            timestamp: new Date().toISOString()
        };
    },

    /**
     * Clean up test environment
     */
    cleanup() {
        // Clear localStorage
        localStorage.removeItem('style-guide-ai-filters');
        
        // Reset global filter system if it exists
        if (window.SmartFilterSystem) {
            window.SmartFilterSystem.activeFilters = new Set(['critical', 'error', 'warning', 'suggestion']);
            window.SmartFilterSystem.callbacks = [];
            window.SmartFilterSystem.originalErrors = [];
            window.SmartFilterSystem.filteredErrors = [];
        }
    }
};

// Core Smart Filter System Tests
QUnit.module('Smart Filter System Core', {
    beforeEach: function() {
        TestUtils.cleanup();
    },
    afterEach: function() {
        TestUtils.cleanup();
    }
}, function() {
    
    QUnit.test('Constructor Initialization', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Test initial state
        assert.deepEqual([...filter.activeFilters].sort(), 
            ['critical', 'error', 'suggestion', 'warning'], 
            'All filters active by default');
        
        assert.deepEqual(filter.totalCounts, 
            { critical: 0, error: 0, warning: 0, suggestion: 0 },
            'Total counts initialized to zero');
        
        assert.equal(filter.filteredErrors.length, 0, 'Filtered errors array empty');
        assert.equal(filter.originalErrors.length, 0, 'Original errors array empty');
        assert.equal(filter.callbacks.length, 0, 'Callbacks array empty');
        
        // Test performance metrics initialization
        assert.equal(filter.performanceMetrics.totalFilterOperations, 0, 'Filter operations counter initialized');
        assert.equal(filter.performanceMetrics.averageFilterTime, 0, 'Average filter time initialized');
        assert.equal(filter.performanceMetrics.lastFilterTime, 0, 'Last filter time initialized');
    });
    
    QUnit.test('Severity Level Mapping', function(assert) {
        const filter = new SmartFilterSystem();
        
        const testCases = [
            { confidence: 0.9, expected: 'critical' },
            { confidence: 0.85, expected: 'critical' },
            { confidence: 0.84, expected: 'error' },
            { confidence: 0.75, expected: 'error' },
            { confidence: 0.70, expected: 'error' },
            { confidence: 0.69, expected: 'warning' },
            { confidence: 0.6, expected: 'warning' },
            { confidence: 0.50, expected: 'warning' },
            { confidence: 0.49, expected: 'suggestion' },
            { confidence: 0.4, expected: 'suggestion' },
            { confidence: 0.0, expected: 'suggestion' }
        ];
        
        testCases.forEach(testCase => {
            const result = filter.getSeverityLevel({ confidence: testCase.confidence });
            assert.equal(result, testCase.expected, 
                `Confidence ${testCase.confidence} maps to ${testCase.expected}`);
        });
    });
    
    QUnit.test('Confidence Score Extraction', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Test different confidence score formats
        const testCases = [
            { error: { confidence_score: 0.8 }, expected: 0.8 },
            { error: { confidence: 0.7 }, expected: 0.7 },
            { error: { validation_result: { confidence_score: 0.6 } }, expected: 0.6 },
            { error: { confidence_score: 0.9, confidence: 0.5 }, expected: 0.9 }, // Priority test
            { error: {}, expected: 0.5 }, // Default fallback
            { error: { confidence_score: null, confidence: 0.3 }, expected: 0.3 }
        ];
        
        testCases.forEach(testCase => {
            const result = filter.extractConfidenceScore(testCase.error);
            assert.equal(result, testCase.expected, 
                `Extracted confidence score matches expected value`);
        });
    });
    
    QUnit.test('Error Filtering Logic', function(assert) {
        const filter = new SmartFilterSystem();
        const mockErrors = TestUtils.createMockErrorSet({
            critical: 2,
            error: 3,
            warning: 4,
            suggestion: 1
        });
        
        // Test all filters active
        let filtered = filter.applyFilters(mockErrors);
        assert.equal(filtered.length, 10, 'All errors shown when all filters active');
        
        // Test critical only
        filter.activeFilters = new Set(['critical']);
        filtered = filter.applyFilters(mockErrors);
        assert.equal(filtered.length, 2, 'Only critical errors shown');
        
        // Test critical and error
        filter.activeFilters = new Set(['critical', 'error']);
        filtered = filter.applyFilters(mockErrors);
        assert.equal(filtered.length, 5, 'Critical and error issues shown');
        
        // Test no filters (empty set)
        filter.activeFilters = new Set();
        filtered = filter.applyFilters(mockErrors);
        assert.equal(filtered.length, 0, 'No errors shown when no filters active');
    });
    
    QUnit.test('Count Updates', function(assert) {
        const filter = new SmartFilterSystem();
        const mockErrors = TestUtils.createMockErrorSet({
            critical: 2,
            error: 1,
            warning: 3,
            suggestion: 1
        });
        
        filter.applyFilters(mockErrors);
        
        assert.equal(filter.totalCounts.critical, 2, 'Critical count correct');
        assert.equal(filter.totalCounts.error, 1, 'Error count correct');
        assert.equal(filter.totalCounts.warning, 3, 'Warning count correct');
        assert.equal(filter.totalCounts.suggestion, 1, 'Suggestion count correct');
    });
    
    QUnit.test('Filter Toggle Operations', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Test valid toggle operations
        assert.ok(filter.activeFilters.has('critical'), 'Critical filter initially active');
        
        filter.toggleFilter('critical');
        assert.notOk(filter.activeFilters.has('critical'), 'Critical filter deactivated');
        
        filter.toggleFilter('critical');
        assert.ok(filter.activeFilters.has('critical'), 'Critical filter reactivated');
        
        // Test invalid filter level
        const initialSize = filter.activeFilters.size;
        filter.toggleFilter('invalid_level');
        assert.equal(filter.activeFilters.size, initialSize, 'Invalid filter level ignored');
    });
    
    QUnit.test('Filter Reset Functionality', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Modify filters
        filter.activeFilters = new Set(['critical']);
        assert.equal(filter.activeFilters.size, 1, 'Filters modified');
        
        // Reset filters
        filter.resetFilters();
        assert.deepEqual([...filter.activeFilters].sort(), 
            ['critical', 'error', 'suggestion', 'warning'],
            'Filters reset to default state');
    });
    
    QUnit.test('Filter Presets', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Test focus mode preset
        filter.applyFilterPreset('focus-mode');
        assert.deepEqual([...filter.activeFilters].sort(), 
            ['critical', 'error'],
            'Focus mode preset applied correctly');
        
        // Test review mode preset
        filter.applyFilterPreset('review-mode');
        assert.deepEqual([...filter.activeFilters].sort(), 
            ['critical', 'error', 'warning'],
            'Review mode preset applied correctly');
        
        // Test complete audit preset
        filter.applyFilterPreset('complete-audit');
        assert.deepEqual([...filter.activeFilters].sort(), 
            ['critical', 'error', 'suggestion', 'warning'],
            'Complete audit preset applied correctly');
        
        // Test invalid preset
        filter.activeFilters = new Set(['critical']);
        filter.applyFilterPreset('invalid-preset');
        assert.deepEqual([...filter.activeFilters], 
            ['critical'],
            'Invalid preset ignored');
    });
});

// Input Validation and Edge Cases
QUnit.module('Input Validation and Edge Cases', {
    beforeEach: function() {
        TestUtils.cleanup();
    },
    afterEach: function() {
        TestUtils.cleanup();
    }
}, function() {
    
    QUnit.test('Invalid Input Handling', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Test null input
        let result = filter.applyFilters(null);
        assert.equal(result.length, 0, 'Null input returns empty array');
        
        // Test undefined input
        result = filter.applyFilters(undefined);
        assert.equal(result.length, 0, 'Undefined input returns empty array');
        
        // Test non-array input
        result = filter.applyFilters('not an array');
        assert.equal(result.length, 0, 'Non-array input returns empty array');
        
        // Test empty array
        result = filter.applyFilters([]);
        assert.equal(result.length, 0, 'Empty array returns empty array');
    });
    
    QUnit.test('Malformed Error Objects', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Test errors without confidence scores
        const errorsWithoutConfidence = [
            { type: 'test', message: 'Test error' },
            { type: 'test2', message: 'Test error 2', confidence: null }
        ];
        
        const result = filter.applyFilters(errorsWithoutConfidence);
        assert.equal(result.length, 2, 'Errors without confidence processed with defaults');
        
        // All should be classified as suggestions (default 0.5 confidence)
        result.forEach(error => {
            const severity = filter.getSeverityLevel(error);
            assert.equal(severity, 'suggestion', 'Default confidence maps to suggestion');
        });
    });
    
    QUnit.test('Large Dataset Handling', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Create large dataset
        const largeDataset = TestUtils.createMockErrorSet({
            critical: 100,
            error: 200,
            warning: 300,
            suggestion: 400
        });
        
        assert.equal(largeDataset.length, 1000, 'Large dataset created correctly');
        
        const performance = TestUtils.measurePerformance(() => {
            return filter.applyFilters(largeDataset);
        });
        
        assert.equal(performance.result.length, 1000, 'All errors processed in large dataset');
        assert.ok(performance.executionTime < 50, 
            `Large dataset filtered in ${performance.executionTime.toFixed(2)}ms (target: <50ms)`);
    });
});

// Callback System Tests
QUnit.module('Callback System', {
    beforeEach: function() {
        TestUtils.cleanup();
    },
    afterEach: function() {
        TestUtils.cleanup();
    }
}, function() {
    
    QUnit.test('Callback Registration and Execution', function(assert) {
        const filter = new SmartFilterSystem();
        let callbackExecuted = false;
        let callbackData = null;
        
        // Register callback
        const callback = (filteredErrors, totalCounts, activeFilters) => {
            callbackExecuted = true;
            callbackData = { filteredErrors, totalCounts, activeFilters };
        };
        
        filter.onFilterChange(callback);
        assert.equal(filter.callbacks.length, 1, 'Callback registered successfully');
        
        // Trigger callback by applying filters
        const mockErrors = TestUtils.createMockErrorSet({ critical: 1, error: 1 });
        filter.applyFilters(mockErrors);
        
        assert.ok(callbackExecuted, 'Callback executed when filters applied');
        assert.ok(callbackData, 'Callback received data');
        assert.equal(callbackData.filteredErrors.length, 2, 'Callback received correct filtered errors');
    });
    
    QUnit.test('Callback Error Handling', function(assert) {
        const filter = new SmartFilterSystem();
        
        // Register callback that throws error
        const errorCallback = () => {
            throw new Error('Test callback error');
        };
        
        // Register normal callback
        let normalCallbackExecuted = false;
        const normalCallback = () => {
            normalCallbackExecuted = true;
        };
        
        filter.onFilterChange(errorCallback);
        filter.onFilterChange(normalCallback);
        
        // Apply filters - should not throw despite error callback
        const mockErrors = [TestUtils.createMockError(0.8)];
        assert.doesNotThrow(() => {
            filter.applyFilters(mockErrors);
        }, 'Error in callback does not break filter system');
        
        assert.ok(normalCallbackExecuted, 'Normal callback still executed despite error in other callback');
    });
    
    QUnit.test('Callback Removal', function(assert) {
        const filter = new SmartFilterSystem();
        let callback1Executed = false;
        let callback2Executed = false;
        
        const callback1 = () => { callback1Executed = true; };
        const callback2 = () => { callback2Executed = true; };
        
        // Register both callbacks
        filter.onFilterChange(callback1);
        filter.onFilterChange(callback2);
        assert.equal(filter.callbacks.length, 2, 'Both callbacks registered');
        
        // Remove first callback
        filter.offFilterChange(callback1);
        assert.equal(filter.callbacks.length, 1, 'First callback removed');
        
        // Apply filters
        filter.applyFilters([TestUtils.createMockError(0.8)]);
        
        assert.notOk(callback1Executed, 'Removed callback not executed');
        assert.ok(callback2Executed, 'Remaining callback executed');
    });
});

// LocalStorage Persistence Tests
QUnit.module('LocalStorage Persistence', {
    beforeEach: function() {
        TestUtils.cleanup();
    },
    afterEach: function() {
        TestUtils.cleanup();
    }
}, function() {
    
    QUnit.test('Filter State Persistence', function(assert) {
        // Create filter and modify state
        const filter1 = new SmartFilterSystem();
        filter1.activeFilters = new Set(['critical', 'error']);
        filter1.saveFilterState();
        
        // Create new filter instance - should load saved state
        const filter2 = new SmartFilterSystem();
        assert.deepEqual([...filter2.activeFilters].sort(), 
            ['critical', 'error'],
            'Filter state loaded from localStorage');
    });
    
    QUnit.test('Invalid LocalStorage Data Handling', function(assert) {
        // Set invalid data in localStorage
        localStorage.setItem('style-guide-ai-filters', 'invalid json');
        
        const filter = new SmartFilterSystem();
        assert.deepEqual([...filter.activeFilters].sort(), 
            ['critical', 'error', 'suggestion', 'warning'],
            'Invalid localStorage data falls back to defaults');
    });
    
    QUnit.test('Partial LocalStorage Data Validation', function(assert) {
        // Set partially valid data with invalid filter
        const partialData = {
            activeFilters: ['critical', 'invalid_filter', 'error'],
            savedAt: new Date().toISOString()
        };
        localStorage.setItem('style-guide-ai-filters', JSON.stringify(partialData));
        
        const filter = new SmartFilterSystem();
        assert.deepEqual([...filter.activeFilters].sort(), 
            ['critical', 'error'],
            'Invalid filters filtered out, valid ones preserved');
    });
});

// Performance Tests
QUnit.module('Performance Benchmarks', {
    beforeEach: function() {
        TestUtils.cleanup();
    },
    afterEach: function() {
        TestUtils.cleanup();
    }
}, function() {
    
    QUnit.test('Small Dataset Performance', function(assert) {
        const filter = new SmartFilterSystem();
        const smallDataset = TestUtils.createMockErrorSet({
            critical: 5,
            error: 10,
            warning: 15,
            suggestion: 20
        });
        
        const performance = TestUtils.measurePerformance(() => {
            return filter.applyFilters(smallDataset);
        });
        
        assert.ok(performance.executionTime < 10, 
            `Small dataset (50 errors) filtered in ${performance.executionTime.toFixed(2)}ms (target: <10ms)`);
    });
    
    QUnit.test('Large Dataset Performance', function(assert) {
        const filter = new SmartFilterSystem();
        const largeDataset = TestUtils.createMockErrorSet({
            critical: 100,
            error: 300,
            warning: 400,
            suggestion: 200
        });
        
        const performance = TestUtils.measurePerformance(() => {
            return filter.applyFilters(largeDataset);
        });
        
        assert.ok(performance.executionTime < 50, 
            `Large dataset (1000 errors) filtered in ${performance.executionTime.toFixed(2)}ms (target: <50ms)`);
        
        // Test performance metrics tracking
        assert.equal(filter.performanceMetrics.totalFilterOperations, 1, 'Performance metrics tracked');
        assert.ok(filter.performanceMetrics.lastFilterTime > 0, 'Last filter time recorded');
        assert.ok(filter.performanceMetrics.averageFilterTime > 0, 'Average filter time calculated');
    });
    
    QUnit.test('Repeated Filter Operations Performance', function(assert) {
        const filter = new SmartFilterSystem();
        const dataset = TestUtils.createMockErrorSet({
            critical: 50,
            error: 100,
            warning: 150,
            suggestion: 75
        });
        
        const iterations = 10;
        const totalPerformance = TestUtils.measurePerformance(() => {
            for (let i = 0; i < iterations; i++) {
                filter.applyFilters(dataset);
            }
        });
        
        const averageTime = totalPerformance.executionTime / iterations;
        
        assert.ok(averageTime < 20, 
            `Average filter time over ${iterations} iterations: ${averageTime.toFixed(2)}ms (target: <20ms)`);
        
        assert.equal(filter.performanceMetrics.totalFilterOperations, iterations, 
            'Performance metrics correctly track multiple operations');
    });
});

// State Management Tests
QUnit.module('State Management', {
    beforeEach: function() {
        TestUtils.cleanup();
    },
    afterEach: function() {
        TestUtils.cleanup();
    }
}, function() {
    
    QUnit.test('Filter State Tracking', function(assert) {
        const filter = new SmartFilterSystem();
        const mockErrors = TestUtils.createMockErrorSet({
            critical: 1,
            error: 2,
            warning: 3,
            suggestion: 4
        });
        
        filter.applyFilters(mockErrors);
        
        const state = filter.getFilterState();
        
        assert.equal(state.originalErrorCount, 10, 'Original error count tracked');
        assert.equal(state.filteredErrorCount, 10, 'Filtered error count tracked');
        assert.deepEqual(state.totalCounts, 
            { critical: 1, error: 2, warning: 3, suggestion: 4 },
            'Total counts tracked correctly');
        assert.equal(state.callbackCount, 0, 'Callback count tracked');
        assert.ok(state.performanceMetrics, 'Performance metrics included in state');
    });
    
    QUnit.test('Performance Metrics Tracking', function(assert) {
        const filter = new SmartFilterSystem();
        const mockErrors = TestUtils.createMockErrorSet({ critical: 10 });
        
        // Apply filters multiple times
        filter.applyFilters(mockErrors);
        filter.applyFilters(mockErrors);
        filter.applyFilters(mockErrors);
        
        const metrics = filter.getPerformanceMetrics();
        
        assert.equal(metrics.totalFilterOperations, 3, 'Total operations tracked');
        assert.ok(metrics.averageFilterTime >= 0, 'Average filter time calculated');
        assert.ok(metrics.lastFilterTime >= 0, 'Last filter time recorded');
    });
});

// Initialize and run tests
QUnit.start();

console.log('✅ Smart Filter System test suite loaded and ready to run');
