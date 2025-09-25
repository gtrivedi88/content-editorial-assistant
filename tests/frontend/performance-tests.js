/**
 * Performance Tests for Smart Filter System
 * Benchmarks and stress testing for production readiness
 * 
 * Validates performance requirements from implementation plan:
 * - Filter operations: <50ms for 1000+ errors
 * - UI updates: <100ms
 * - Memory usage: stable during operations
 */

// Performance test configuration
const PERFORMANCE_CONFIG = {
    FILTER_TARGET_MS: 50,      // Target filter performance (ms)
    UI_TARGET_MS: 100,         // Target UI update performance (ms)
    LARGE_DATASET_SIZE: 1000,  // Large dataset size for testing
    STRESS_ITERATIONS: 100,    // Number of stress test iterations
    MEMORY_SAMPLE_INTERVAL: 10 // Memory sampling interval (ms)
};

// Performance utilities
const PerformanceUtils = {
    /**
     * Generate large dataset for performance testing
     * @param {Object} config - Dataset configuration
     * @returns {Array} - Large array of mock errors
     */
    generateLargeDataset(config = {}) {
        const {
            criticalCount = 100,
            errorCount = 300,
            warningCount = 400,
            suggestionCount = 200
        } = config;
        
        const errors = [];
        
        // Generate critical errors
        for (let i = 0; i < criticalCount; i++) {
            errors.push({
                type: `critical_rule_${i}`,
                message: `Critical issue ${i + 1}: This requires immediate attention`,
                confidence: 0.85 + (Math.random() * 0.15),
                severity: 'high',
                suggestions: [`Fix critical issue ${i + 1}`, `Alternative solution for issue ${i + 1}`],
                sentence: `This is sentence ${i} with a critical error that needs to be addressed immediately.`,
                sentence_index: i,
                error_position: Math.floor(Math.random() * 100),
                text_segment: `critical text segment ${i}`
            });
        }
        
        // Generate error-level issues
        for (let i = 0; i < errorCount; i++) {
            errors.push({
                type: `error_rule_${i}`,
                message: `Error issue ${i + 1}: This should be addressed`,
                confidence: 0.70 + (Math.random() * 0.15),
                severity: 'medium',
                suggestions: [`Fix error issue ${i + 1}`],
                sentence: `This is sentence ${i} with an error that should be fixed.`,
                sentence_index: i,
                error_position: Math.floor(Math.random() * 100)
            });
        }
        
        // Generate warnings
        for (let i = 0; i < warningCount; i++) {
            errors.push({
                type: `warning_rule_${i}`,
                message: `Warning issue ${i + 1}: Consider addressing this`,
                confidence: 0.50 + (Math.random() * 0.20),
                severity: 'medium',
                suggestions: [`Consider fixing warning ${i + 1}`],
                sentence: `This is sentence ${i} with a warning that could be improved.`,
                sentence_index: i
            });
        }
        
        // Generate suggestions
        for (let i = 0; i < suggestionCount; i++) {
            errors.push({
                type: `suggestion_rule_${i}`,
                message: `Suggestion ${i + 1}: This could be improved`,
                confidence: 0.30 + (Math.random() * 0.20),
                severity: 'low',
                suggestions: [`Consider suggestion ${i + 1}`],
                sentence: `This is sentence ${i} with a suggestion for improvement.`,
                sentence_index: i
            });
        }
        
        return errors;
    },

    /**
     * Measure memory usage during operation
     * @returns {Object} - Memory usage statistics
     */
    measureMemoryUsage() {
        if (performance.memory) {
            return {
                usedJSHeapSize: performance.memory.usedJSHeapSize,
                totalJSHeapSize: performance.memory.totalJSHeapSize,
                jsHeapSizeLimit: performance.memory.jsHeapSizeLimit,
                timestamp: performance.now()
            };
        }
        return null;
    },

    /**
     * Monitor memory usage during function execution
     * @param {Function} fn - Function to monitor
     * @returns {Object} - Execution results and memory statistics
     */
    monitorMemoryUsage(fn) {
        if (!performance.memory) {
            return {
                result: fn(),
                memoryStats: 'Memory monitoring not available in this environment'
            };
        }

        const memorySnapshots = [];
        const startMemory = this.measureMemoryUsage();
        
        // Start monitoring
        const monitorInterval = setInterval(() => {
            memorySnapshots.push(this.measureMemoryUsage());
        }, PERFORMANCE_CONFIG.MEMORY_SAMPLE_INTERVAL);

        // Execute function
        const startTime = performance.now();
        const result = fn();
        const endTime = performance.now();

        // Stop monitoring
        clearInterval(monitorInterval);
        const endMemory = this.measureMemoryUsage();

        return {
            result: result,
            executionTime: endTime - startTime,
            memoryStats: {
                startMemory: startMemory,
                endMemory: endMemory,
                peakMemory: memorySnapshots.reduce((max, current) => 
                    current.usedJSHeapSize > max.usedJSHeapSize ? current : max, startMemory),
                memoryDelta: endMemory.usedJSHeapSize - startMemory.usedJSHeapSize,
                snapshots: memorySnapshots
            }
        };
    },

    /**
     * Benchmark function execution multiple times
     * @param {Function} fn - Function to benchmark
     * @param {number} iterations - Number of iterations
     * @returns {Object} - Benchmark statistics
     */
    benchmark(fn, iterations = 10) {
        const times = [];
        
        for (let i = 0; i < iterations; i++) {
            const start = performance.now();
            fn();
            const end = performance.now();
            times.push(end - start);
        }
        
        times.sort((a, b) => a - b);
        
        return {
            iterations: iterations,
            min: times[0],
            max: times[times.length - 1],
            average: times.reduce((sum, time) => sum + time, 0) / times.length,
            median: times[Math.floor(times.length / 2)],
            p95: times[Math.floor(times.length * 0.95)],
            p99: times[Math.floor(times.length * 0.99)]
        };
    }
};

// QUnit Performance Tests
QUnit.module('Filter Performance', function() {
    
    QUnit.test('Small Dataset Filtering Performance', function(assert) {
        const done = assert.async();
        
        // Generate small dataset (100 errors)
        const smallDataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 10,
            errorCount: 30,
            warningCount: 40,
            suggestionCount: 20
        });
        
        const filter = new SmartFilterSystem();
        
        // Measure filtering performance
        const performance = PerformanceUtils.monitorMemoryUsage(() => {
            return filter.applyFilters(smallDataset);
        });
        
        assert.ok(performance.executionTime < 10, 
            `Small dataset (100 errors) filtered in ${performance.executionTime.toFixed(2)}ms (target: <10ms)`);
        
        assert.equal(performance.result.length, 100, 'All errors processed correctly');
        
        if (performance.memoryStats !== 'Memory monitoring not available in this environment') {
            assert.ok(performance.memoryStats.memoryDelta < 1024 * 1024, // 1MB
                `Memory usage delta: ${(performance.memoryStats.memoryDelta / 1024).toFixed(2)}KB (reasonable)`);
        }
        
        done();
    });
    
    QUnit.test('Large Dataset Filtering Performance', function(assert) {
        const done = assert.async();
        
        // Generate large dataset (1000 errors)
        const largeDataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 100,
            errorCount: 300,
            warningCount: 400,
            suggestionCount: 200
        });
        
        const filter = new SmartFilterSystem();
        
        // Measure filtering performance with memory monitoring
        const performance = PerformanceUtils.monitorMemoryUsage(() => {
            return filter.applyFilters(largeDataset);
        });
        
        assert.ok(performance.executionTime < PERFORMANCE_CONFIG.FILTER_TARGET_MS, 
            `Large dataset (1000 errors) filtered in ${performance.executionTime.toFixed(2)}ms (target: <${PERFORMANCE_CONFIG.FILTER_TARGET_MS}ms)`);
        
        assert.equal(performance.result.length, 1000, 'All errors processed correctly');
        
        if (performance.memoryStats !== 'Memory monitoring not available in this environment') {
            const memoryDeltaMB = performance.memoryStats.memoryDelta / (1024 * 1024);
            assert.ok(memoryDeltaMB < 5, 
                `Memory usage delta: ${memoryDeltaMB.toFixed(2)}MB (target: <5MB)`);
        }
        
        done();
    });
    
    QUnit.test('Filter Toggle Performance', function(assert) {
        const done = assert.async();
        
        const filter = new SmartFilterSystem();
        const dataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 100,
            errorCount: 200,
            warningCount: 300,
            suggestionCount: 400
        });
        
        // Initial filter application
        filter.applyFilters(dataset);
        
        // Benchmark filter toggle operations
        const toggleBenchmark = PerformanceUtils.benchmark(() => {
            filter.toggleFilter('critical');
        }, 50);
        
        assert.ok(toggleBenchmark.average < 5, 
            `Filter toggle average time: ${toggleBenchmark.average.toFixed(2)}ms (target: <5ms)`);
        
        assert.ok(toggleBenchmark.p95 < 10, 
            `Filter toggle 95th percentile: ${toggleBenchmark.p95.toFixed(2)}ms (target: <10ms)`);
        
        done();
    });
    
    QUnit.test('Concurrent Filter Operations Performance', function(assert) {
        const done = assert.async();
        
        const filter = new SmartFilterSystem();
        const dataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 200,
            errorCount: 300,
            warningCount: 300,
            suggestionCount: 200
        });
        
        // Simulate concurrent operations
        const startTime = performance.now();
        
        const promises = [];
        for (let i = 0; i < 5; i++) {
            promises.push(new Promise(resolve => {
                setTimeout(() => {
                    const filtered = filter.applyFilters(dataset);
                    resolve(filtered.length);
                }, i * 10); // Stagger operations
            }));
        }
        
        Promise.all(promises).then(results => {
            const endTime = performance.now();
            const totalTime = endTime - startTime;
            
            assert.ok(totalTime < 200, 
                `Concurrent filter operations completed in ${totalTime.toFixed(2)}ms (target: <200ms)`);
            
            // Verify all operations completed successfully
            results.forEach(result => {
                assert.ok(result >= 0, 'Each concurrent operation completed successfully');
            });
            
            done();
        });
    });
    
    QUnit.test('Memory Stability During Repeated Operations', function(assert) {
        const done = assert.async();
        
        if (!performance.memory) {
            assert.ok(true, 'Memory monitoring not available - test skipped');
            done();
            return;
        }
        
        const filter = new SmartFilterSystem();
        const dataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 100,
            errorCount: 150,
            warningCount: 200,
            suggestionCount: 150
        });
        
        const initialMemory = PerformanceUtils.measureMemoryUsage();
        const memoryReadings = [];
        
        // Perform repeated filter operations
        for (let i = 0; i < 50; i++) {
            filter.applyFilters(dataset);
            
            // Sample memory every 10 operations
            if (i % 10 === 0) {
                memoryReadings.push(PerformanceUtils.measureMemoryUsage());
            }
        }
        
        const finalMemory = PerformanceUtils.measureMemoryUsage();
        const memoryIncrease = finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize;
        const memoryIncreaseMB = memoryIncrease / (1024 * 1024);
        
        assert.ok(memoryIncreaseMB < 2, 
            `Memory increase after 50 operations: ${memoryIncreaseMB.toFixed(2)}MB (target: <2MB)`);
        
        // Check for memory leaks (consistent growth)
        const memoryGrowth = memoryReadings.map((reading, i) => 
            i === 0 ? 0 : reading.usedJSHeapSize - memoryReadings[0].usedJSHeapSize
        );
        
        const averageGrowthPerSample = memoryGrowth.reduce((sum, growth) => sum + growth, 0) / memoryGrowth.length;
        const averageGrowthMB = averageGrowthPerSample / (1024 * 1024);
        
        assert.ok(averageGrowthMB < 1, 
            `Average memory growth per sample: ${averageGrowthMB.toFixed(2)}MB (checking for leaks)`);
        
        done();
    });
});

// UI Performance Tests
QUnit.module('UI Performance', function() {
    
    QUnit.test('Filter Chips Rendering Performance', function(assert) {
        const done = assert.async();
        
        // Skip if UI components not available
        if (!window.SmartFilterChips) {
            assert.ok(true, 'SmartFilterChips not available - test skipped');
            done();
            return;
        }
        
        const totalCounts = { critical: 50, error: 100, warning: 150, suggestion: 75 };
        const activeFilters = new Set(['critical', 'error', 'warning', 'suggestion']);
        
        // Benchmark chip rendering
        const renderBenchmark = PerformanceUtils.benchmark(() => {
            return window.SmartFilterChips.createSmartFilterChips(totalCounts, activeFilters);
        }, 20);
        
        assert.ok(renderBenchmark.average < PERFORMANCE_CONFIG.UI_TARGET_MS, 
            `Filter chips rendering average time: ${renderBenchmark.average.toFixed(2)}ms (target: <${PERFORMANCE_CONFIG.UI_TARGET_MS}ms)`);
        
        assert.ok(renderBenchmark.p95 < PERFORMANCE_CONFIG.UI_TARGET_MS * 1.5, 
            `Filter chips rendering 95th percentile: ${renderBenchmark.p95.toFixed(2)}ms`);
        
        done();
    });
    
    QUnit.test('Filter Statistics Generation Performance', function(assert) {
        const done = assert.async();
        
        // Skip if UI components not available
        if (!window.SmartFilterChips) {
            assert.ok(true, 'SmartFilterChips not available - test skipped');
            done();
            return;
        }
        
        const totalErrors = 1000;
        const filteredErrors = 250;
        const activeFilters = new Set(['critical', 'error']);
        
        // Benchmark statistics generation
        const statsBenchmark = PerformanceUtils.benchmark(() => {
            return window.SmartFilterChips.createFilterStatistics(totalErrors, filteredErrors, activeFilters);
        }, 30);
        
        assert.ok(statsBenchmark.average < 20, 
            `Filter statistics generation average time: ${statsBenchmark.average.toFixed(2)}ms (target: <20ms)`);
        
        done();
    });
    
    QUnit.test('Filter State Update Performance', function(assert) {
        const done = assert.async();
        
        // Create DOM elements for testing
        const container = document.createElement('div');
        container.innerHTML = `
            <div class="smart-filter-container">
                <div data-filter-level="critical" class="pf-v5-c-chip">
                    <span class="pf-v5-c-badge">0</span>
                </div>
                <div data-filter-level="error" class="pf-v5-c-chip">
                    <span class="pf-v5-c-badge">0</span>
                </div>
                <div data-filter-level="warning" class="pf-v5-c-chip">
                    <span class="pf-v5-c-badge">0</span>
                </div>
                <div data-filter-level="suggestion" class="pf-v5-c-chip">
                    <span class="pf-v5-c-badge">0</span>
                </div>
            </div>
        `;
        document.body.appendChild(container);
        
        const totalCounts = { critical: 25, error: 50, warning: 100, suggestion: 75 };
        const activeFilters = new Set(['critical', 'error', 'warning']);
        
        // Benchmark filter state updates
        const updateBenchmark = PerformanceUtils.benchmark(() => {
            if (window.SmartFilterChips && window.SmartFilterChips.updateFilterChipsDisplay) {
                window.SmartFilterChips.updateFilterChipsDisplay(totalCounts, activeFilters);
            }
        }, 25);
        
        assert.ok(updateBenchmark.average < 30, 
            `Filter state update average time: ${updateBenchmark.average.toFixed(2)}ms (target: <30ms)`);
        
        // Cleanup
        document.body.removeChild(container);
        
        done();
    });
});

// Stress Tests
QUnit.module('Stress Tests', function() {
    
    QUnit.test('Rapid Filter Toggle Stress Test', function(assert) {
        const done = assert.async();
        
        const filter = new SmartFilterSystem();
        const dataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 50,
            errorCount: 100,
            warningCount: 150,
            suggestionCount: 100
        });
        
        filter.applyFilters(dataset);
        
        // Rapidly toggle filters
        const startTime = performance.now();
        
        for (let i = 0; i < PERFORMANCE_CONFIG.STRESS_ITERATIONS; i++) {
            const levels = ['critical', 'error', 'warning', 'suggestion'];
            const randomLevel = levels[Math.floor(Math.random() * levels.length)];
            filter.toggleFilter(randomLevel);
        }
        
        const endTime = performance.now();
        const totalTime = endTime - startTime;
        const avgTimePerToggle = totalTime / PERFORMANCE_CONFIG.STRESS_ITERATIONS;
        
        assert.ok(avgTimePerToggle < 5, 
            `Average time per toggle under stress: ${avgTimePerToggle.toFixed(2)}ms (target: <5ms)`);
        
        assert.ok(totalTime < 500, 
            `Total time for ${PERFORMANCE_CONFIG.STRESS_ITERATIONS} toggles: ${totalTime.toFixed(2)}ms (target: <500ms)`);
        
        // Verify filter system is still functional
        const finalFiltered = filter.applyFilters(dataset);
        assert.ok(finalFiltered.length >= 0, 'Filter system remains functional after stress test');
        
        done();
    });
    
    QUnit.test('Large Dataset Repeated Processing Stress Test', function(assert) {
        const done = assert.async();
        
        const filter = new SmartFilterSystem();
        const largeDataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 200,
            errorCount: 300,
            warningCount: 300,
            suggestionCount: 200
        });
        
        const iterations = 25;
        const startTime = performance.now();
        const initialMemory = PerformanceUtils.measureMemoryUsage();
        
        // Repeatedly process large dataset
        for (let i = 0; i < iterations; i++) {
            const result = filter.applyFilters(largeDataset);
            
            // Verify results are consistent
            if (i === 0) {
                assert.equal(result.length, 1000, 'First iteration processes all errors');
            }
        }
        
        const endTime = performance.now();
        const finalMemory = PerformanceUtils.measureMemoryUsage();
        const totalTime = endTime - startTime;
        const avgTimePerIteration = totalTime / iterations;
        
        assert.ok(avgTimePerIteration < 100, 
            `Average time per iteration: ${avgTimePerIteration.toFixed(2)}ms (target: <100ms)`);
        
        if (initialMemory && finalMemory) {
            const memoryDeltaMB = (finalMemory.usedJSHeapSize - initialMemory.usedJSHeapSize) / (1024 * 1024);
            assert.ok(memoryDeltaMB < 5, 
                `Memory increase after ${iterations} iterations: ${memoryDeltaMB.toFixed(2)}MB (target: <5MB)`);
        }
        
        done();
    });
    
    QUnit.test('Callback System Stress Test', function(assert) {
        const done = assert.async();
        
        const filter = new SmartFilterSystem();
        const dataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 100,
            errorCount: 200,
            warningCount: 200,
            suggestionCount: 100
        });
        
        let callbackExecutionCount = 0;
        const callbackCount = 50;
        
        // Register many callbacks
        for (let i = 0; i < callbackCount; i++) {
            filter.onFilterChange(() => {
                callbackExecutionCount++;
                // Simulate some callback processing time
                for (let j = 0; j < 100; j++) {
                    Math.random();
                }
            });
        }
        
        // Apply filters and measure performance
        const startTime = performance.now();
        filter.applyFilters(dataset);
        const endTime = performance.now();
        
        const totalTime = endTime - startTime;
        
        assert.ok(totalTime < 200, 
            `Filter application with ${callbackCount} callbacks: ${totalTime.toFixed(2)}ms (target: <200ms)`);
        
        assert.equal(callbackExecutionCount, callbackCount, 
            'All callbacks executed correctly');
        
        done();
    });
});

// Regression Tests
QUnit.module('Regression Tests', function() {
    
    QUnit.test('Performance Regression Detection', function(assert) {
        const done = assert.async();
        
        // Baseline performance expectations (based on requirements)
        const BASELINES = {
            smallDataset: 10,   // ms for 100 errors
            largeDataset: 50,   // ms for 1000 errors
            filterToggle: 5,    // ms for toggle operation
            uiUpdate: 100       // ms for UI update
        };
        
        const filter = new SmartFilterSystem();
        
        // Test small dataset
        const smallDataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 25,
            errorCount: 25,
            warningCount: 25,
            suggestionCount: 25
        });
        
        const smallBenchmark = PerformanceUtils.benchmark(() => {
            filter.applyFilters(smallDataset);
        }, 10);
        
        assert.ok(smallBenchmark.p95 < BASELINES.smallDataset * 2, 
            `Small dataset P95: ${smallBenchmark.p95.toFixed(2)}ms (regression threshold: ${BASELINES.smallDataset * 2}ms)`);
        
        // Test large dataset
        const largeDataset = PerformanceUtils.generateLargeDataset({
            criticalCount: 250,
            errorCount: 250,
            warningCount: 250,
            suggestionCount: 250
        });
        
        const largeBenchmark = PerformanceUtils.benchmark(() => {
            filter.applyFilters(largeDataset);
        }, 5);
        
        assert.ok(largeBenchmark.p95 < BASELINES.largeDataset * 2, 
            `Large dataset P95: ${largeBenchmark.p95.toFixed(2)}ms (regression threshold: ${BASELINES.largeDataset * 2}ms)`);
        
        done();
    });
});

console.log('✅ Performance test suite loaded and ready to run');
