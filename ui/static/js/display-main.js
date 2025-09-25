/**
 * Main Display Module - Enhanced PatternFly Version
 * Entry Points and Orchestration with world-class design
 */

// Main entry point - orchestrates the display using enhanced PatternFly layouts
function displayAnalysisResults(analysis, content, structuralBlocks = null) {
    const resultsContainer = document.getElementById('analysis-results');
    if (!resultsContainer) return;

    // Store current analysis and content for later use
    currentAnalysis = analysis;
    currentContent = content; // Store content for attribute block detection
    
    // Store original structural blocks before any filtering
    if (structuralBlocks) {
        window.originalStructuralBlocks = JSON.parse(JSON.stringify(structuralBlocks)); // Deep copy
    }

    // Initialize smart filter system with current errors
    const errors = analysis.errors || [];
    const filteredErrors = window.SmartFilterSystem ? 
        window.SmartFilterSystem.applyFilters(errors) : errors;
    
    // Enhanced header with filter chips
    const analysisHeader = createEnhancedAnalysisHeader(analysis, filteredErrors);

    // Use enhanced PatternFly Grid layout for better responsiveness
    resultsContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-8-col-on-lg pf-m-12-col">
                <div class="pf-v5-l-stack pf-m-gutter">
                    <!-- Enhanced Analysis Header with Filters -->
                    <div class="pf-v5-l-stack__item">
                        ${analysisHeader}
                    </div>

                    <!-- Content Display with Filtered Results -->
                    <div class="pf-v5-l-stack__item">
                        ${structuralBlocks ? 
                            displayStructuralBlocks(structuralBlocks, filteredErrors) : 
                            displayFlatContent(content, filteredErrors)}
                    </div>

                    <!-- Filtered Error Summary -->
                    ${!structuralBlocks && filteredErrors.length > 0 ? `
                        <div class="pf-v5-l-stack__item">
                            ${createErrorSummary(filteredErrors)}
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="pf-v5-l-grid__item pf-m-4-col-on-lg pf-m-12-col" id="statistics-column">
                ${generateStatisticsCard(analysis, filteredErrors)}
            </div>
        </div>
    `;

    // Register filter change callback for dynamic updates
    // FIXED: Prevent multiple callback registration
    if (window.SmartFilterSystem) {
        // Clear any existing callbacks to prevent duplicates
        window.SmartFilterSystem.callbacks = [];
        
        window.SmartFilterSystem.onFilterChange(() => {
            refreshDisplayWithFilters();
        });
    }
    
    // Display modular compliance results if available
    if (analysis.modular_compliance) {
        displayModularComplianceResults(analysis.modular_compliance, analysis.content_type);
    }
    
    // Add smooth scroll behavior with offset to account for sticky header
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    
    // Initialize expandable sections and other interactive elements
    initializeExpandableSections();
    initializeTooltips();
}

// Display structural blocks using enhanced PatternFly Cards
function displayStructuralBlocks(blocks, filteredErrors = null) {
    if (!blocks || blocks.length === 0) return displayEmptyStructure();

    // Work on a deep copy to avoid mutating original blocks
    let workingBlocks = JSON.parse(JSON.stringify(blocks));

    // Filter errors within each block using ONLY the pre-filtered errors
    if (filteredErrors && filteredErrors.length >= 0) {
        // Use severity-based matching instead of object references
        const filteredSeverities = new Set();
        filteredErrors.forEach((error) => {
            const severity = window.SmartFilterSystem?.getSeverityLevel(error);
            filteredSeverities.add(severity);
        });
        
        // Filter errors within each block using severity-based matching 
        workingBlocks = workingBlocks.map((block) => {
            if (block.errors) {
                block.errors = block.errors.filter(error => {
                    // Match by severity instead of object properties
                    const severity = window.SmartFilterSystem?.getSeverityLevel(error);
                    return filteredSeverities.has(severity);
                });
            }
            return block;
        });
    }
    
    // Store only the blocks that actually get displayed for rewriteBlock function access
    const displayedBlocks = [];
    let displayIndex = 0;
    const blocksHtml = workingBlocks.map(block => {
        const html = createStructuralBlock(block, displayIndex, workingBlocks);
        if (html) { // Check for non-empty HTML
            displayedBlocks[displayIndex] = block; // Store block with correct index
            displayIndex++;
        }
        return html;
    }).filter(html => html).join('');
    
    // Store the displayed blocks mapping for rewriteBlock function access
    window.currentStructuralBlocks = displayedBlocks;

    return `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h2 class="pf-v5-c-title pf-m-xl">
                        <i class="fas fa-sitemap pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                        Document Structure Analysis
                    </h2>
                </div>
                <div class="pf-v5-c-card__actions">
                    <button class="pf-v5-c-button pf-m-link pf-m-inline" type="button" onclick="toggleAllBlocks()">
                        <i class="fas fa-expand-alt pf-v5-u-mr-xs"></i>
                        Toggle All
                    </button>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-l-stack pf-m-gutter">
                    ${blocksHtml}
                </div>
            </div>
        </div>
    `;
}

// Display flat content with enhanced styling
function displayFlatContent(content, errors) {
    const hasErrors = errors && errors.length > 0;
    
    return `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h2 class="pf-v5-c-title pf-m-lg">
                        <i class="fas fa-file-alt pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                        Content Analysis
                    </h2>
                </div>
                <div class="pf-v5-c-card__actions">
                    ${hasErrors ? `
                        <span class="pf-v5-c-label pf-m-orange">
                            <span class="pf-v5-c-label__content">
                                <i class="fas fa-exclamation-triangle pf-v5-c-label__icon"></i>
                                ${errors.length} Issue${errors.length !== 1 ? 's' : ''}
                            </span>
                        </span>
                    ` : `
                        <span class="pf-v5-c-label pf-m-green">
                            <span class="pf-v5-c-label__content">
                                <i class="fas fa-check-circle pf-v5-c-label__icon"></i>
                                Clean
                            </span>
                        </span>
                    `}
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-code-block">
                    <div class="pf-v5-c-code-block__header">
                        <div class="pf-v5-c-code-block__header-main">
                            <span class="pf-v5-c-code-block__title">Original Content</span>
                        </div>
                        <div class="pf-v5-c-code-block__actions">
                            <button class="pf-v5-c-button pf-m-plain pf-m-small" type="button" onclick="copyToClipboard('${escapeHtml(content).replace(/'/g, "\\'")}')">
                                <i class="fas fa-copy" aria-hidden="true"></i>
                            </button>
                        </div>
                    </div>
                    <div class="pf-v5-c-code-block__content">
                        <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; word-wrap: break-word; max-height: 400px; overflow-y: auto;"><code class="pf-v5-c-code-block__code">${highlightErrors(content, errors)}</code></pre>
                    </div>
                </div>
            </div>
            ${hasErrors ? `
                <div class="pf-v5-c-card__footer">
                    <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-center">
                        <div class="pf-v5-l-flex__item">
                            <div class="pf-v5-c-alert pf-m-info pf-m-inline">
                                <div class="pf-v5-c-alert__icon">
                                    <i class="fas fa-info-circle"></i>
                                </div>
                                <div class="pf-v5-c-alert__title">
                                    Use Structural Analysis for block-level rewriting
                                </div>
                            </div>
                        </div>
                        <div class="pf-v5-l-flex__item">
                            <button class="pf-v5-c-button pf-m-secondary" type="button" onclick="scrollToErrorSummary()">
                                <i class="fas fa-list pf-v5-u-mr-sm"></i>
                                View Issues
                            </button>
                        </div>
                    </div>
                </div>
            ` : `
                <div class="pf-v5-c-card__footer">
                    <div class="pf-v5-c-empty-state pf-m-sm">
                        <div class="pf-v5-c-empty-state__content">
                            <i class="fas fa-thumbs-up pf-v5-c-empty-state__icon" style="color: var(--app-success-color);"></i>
                            <h3 class="pf-v5-c-title pf-m-md">Excellent Writing!</h3>
                            <div class="pf-v5-c-empty-state__body">
                                No style issues detected. Your content follows best practices.
                            </div>
                        </div>
                    </div>
                </div>
            `}
        </div>
    `;
}

// Display empty structure state
function displayEmptyStructure() {
    return `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-empty-state pf-m-lg">
                    <div class="pf-v5-c-empty-state__content">
                        <i class="fas fa-file-alt pf-v5-c-empty-state__icon" style="color: var(--app-primary-color);"></i>
                        <h2 class="pf-v5-c-title pf-m-lg">Simple Content Structure</h2>
                        <div class="pf-v5-c-empty-state__body">
                            This content doesn't have complex structural elements. 
                            The analysis focuses on style and grammar improvements.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Store current rewritten content for copying
window.currentRewrittenContent = '';

// Display rewrite results with enhanced styling
function displayRewriteResults(data) {
    const rewriteContainer = document.getElementById('rewrite-results');
    if (!rewriteContainer) return;
    
    // Store the rewritten content globally for copying
    window.currentRewrittenContent = data.rewritten_text || data.rewritten || '';

    rewriteContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-c-card app-card">
                    <div class="pf-v5-c-card__header">
                        <div class="pf-v5-c-card__header-main">
                            <h2 class="pf-v5-c-title pf-m-xl">
                                <i class="fas fa-magic pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                AI Rewrite Results
                            </h2>
                        </div>
                        <div class="pf-v5-c-card__actions">
                            <div class="pf-v5-l-flex pf-m-space-items-sm">
                                <div class="pf-v5-l-flex__item">
                                    <span class="pf-v5-c-label pf-m-green">
                                        <span class="pf-v5-c-label__content">
                                            <i class="fas fa-check-circle pf-v5-c-label__icon"></i>
                                            Improved
                                        </span>
                                    </span>
                                </div>
                                <div class="pf-v5-l-flex__item">
                                    <button class="pf-v5-c-button pf-m-secondary" type="button" onclick="refineContent()">
                                        <i class="fas fa-star pf-v5-u-mr-xs"></i>
                                        Refine Further
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <div class="pf-v5-c-code-block">
                            <div class="pf-v5-c-code-block__header">
                                <div class="pf-v5-c-code-block__header-main">
                                    <span class="pf-v5-c-code-block__title">Improved Content</span>
                                </div>
                                <div class="pf-v5-c-code-block__actions">
                                    <button class="pf-v5-c-button pf-m-plain pf-m-small" type="button" onclick="copyRewrittenContent()">
                                        <i class="fas fa-copy" aria-hidden="true"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="pf-v5-c-code-block__content">
                                <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; word-wrap: break-word;"><code class="pf-v5-c-code-block__code">${escapeHtml(data.rewritten_text || data.rewritten || '')}</code></pre>
                            </div>
                        </div>
                        
                        ${data.improvements && data.improvements.length > 0 ? `
                            <div class="pf-v5-u-mt-lg">
                                <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">Key Improvements</h3>
                                <div class="pf-v5-l-stack pf-m-gutter">
                                    ${data.improvements.map(improvement => `
                                        <div class="pf-v5-l-stack__item">
                                            <div class="pf-v5-c-alert pf-m-success pf-m-inline">
                                                <div class="pf-v5-c-alert__icon">
                                                    <i class="fas fa-arrow-up"></i>
                                                </div>
                                                <div class="pf-v5-c-alert__title">
                                                    ${improvement}
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

    rewriteContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Helper function to copy rewritten content
function copyRewrittenContent() {
    if (window.currentRewrittenContent) {
        copyToClipboard(window.currentRewrittenContent);
    } else {
        showNotification('No rewritten content available to copy', 'warning');
    }
}

// Display refinement results (Pass 2)
function displayRefinementResults(data) {
    const rewriteContainer = document.getElementById('rewrite-results');
    if (!rewriteContainer) return;
    
    // Store the refined content globally for copying
    window.currentRewrittenContent = data.refined_content || data.refined_text || '';

    rewriteContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-c-card app-card">
                    <div class="pf-v5-c-card__header">
                        <div class="pf-v5-c-card__header-main">
                            <h2 class="pf-v5-c-title pf-m-xl">
                                <i class="fas fa-sparkles pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                AI Refinement Results (Pass 2)
                            </h2>
                        </div>
                        <div class="pf-v5-c-card__actions">
                            <span class="pf-v5-c-label pf-m-green pf-m-large">
                                <span class="pf-v5-c-label__content">
                                    <i class="fas fa-star pf-v5-c-label__icon"></i>
                                    Refined
                                </span>
                            </span>
                        </div>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <div class="pf-v5-c-code-block">
                            <div class="pf-v5-c-code-block__header">
                                <div class="pf-v5-c-code-block__header-main">
                                    <span class="pf-v5-c-code-block__title">Refined Content</span>
                                </div>
                                <div class="pf-v5-c-code-block__actions">
                                    <button class="pf-v5-c-button pf-m-plain pf-m-small" type="button" onclick="copyRewrittenContent()">
                                        <i class="fas fa-copy" aria-hidden="true"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="pf-v5-c-code-block__content">
                                <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; word-wrap: break-word;"><code class="pf-v5-c-code-block__code">${escapeHtml(data.refined_content || data.refined_text || '')}</code></pre>
                            </div>
                        </div>
                        
                        ${data.refinements && data.refinements.length > 0 ? `
                            <div class="pf-v5-u-mt-lg">
                                <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">Refinements Made</h3>
                                <div class="pf-v5-l-stack pf-m-gutter">
                                    ${data.refinements.map(refinement => `
                                        <div class="pf-v5-l-stack__item">
                                            <div class="pf-v5-c-alert pf-m-info pf-m-inline">
                                                <div class="pf-v5-c-alert__icon">
                                                    <i class="fas fa-lightbulb"></i>
                                                </div>
                                                <div class="pf-v5-c-alert__title">
                                                    ${refinement}
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

    rewriteContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Utility functions for enhanced functionality
function scrollToStatistics() {
    const statisticsColumn = document.getElementById('statistics-column');
    if (statisticsColumn) {
        statisticsColumn.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function scrollToErrorSummary() {
    const errorSummary = document.querySelector('[data-error-summary]');
    if (errorSummary) {
        errorSummary.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function toggleAllBlocks() {
    const expandableSections = document.querySelectorAll('.pf-v5-c-expandable-section');
    const allExpanded = Array.from(expandableSections).every(section => 
        section.getAttribute('aria-expanded') === 'true'
    );
    
    expandableSections.forEach(section => {
        const toggle = section.querySelector('.pf-v5-c-expandable-section__toggle');
        const content = section.querySelector('.pf-v5-c-expandable-section__content');
        
        if (allExpanded) {
            section.setAttribute('aria-expanded', 'false');
            toggle.setAttribute('aria-expanded', 'false');
            content.style.display = 'none';
        } else {
            section.setAttribute('aria-expanded', 'true');
            toggle.setAttribute('aria-expanded', 'true');
            content.style.display = 'block';
        }
    });
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Content copied to clipboard!', 'success');
    }).catch(() => {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showNotification('Content copied to clipboard!', 'success');
    });
}

function initializeExpandableSections() {
    const expandableSections = document.querySelectorAll('.pf-v5-c-expandable-section');
    
    expandableSections.forEach(section => {
        const toggle = section.querySelector('.pf-v5-c-expandable-section__toggle');
        const content = section.querySelector('.pf-v5-c-expandable-section__content');
        
        if (toggle && content) {
            toggle.addEventListener('click', () => {
                const isExpanded = section.getAttribute('aria-expanded') === 'true';
                
                section.setAttribute('aria-expanded', !isExpanded);
                toggle.setAttribute('aria-expanded', !isExpanded);
                content.style.display = isExpanded ? 'none' : 'block';
                
                // Rotate the icon
                const icon = toggle.querySelector('.pf-v5-c-expandable-section__toggle-icon i');
                if (icon) {
                    icon.style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(90deg)';
                    icon.style.transition = 'transform 0.2s ease';
                }
            });
        }
    });
}

function initializeTooltips() {
    // Initialize tooltips for marked text
    const markedElements = document.querySelectorAll('mark[title]');
    markedElements.forEach(element => {
        element.addEventListener('mouseenter', function() {
            // Simple tooltip implementation
            const tooltip = document.createElement('div');
            tooltip.className = 'pf-v5-c-tooltip';
            tooltip.textContent = this.getAttribute('title');
            tooltip.style.position = 'absolute';
            tooltip.style.background = 'rgba(0,0,0,0.8)';
            tooltip.style.color = 'white';
            tooltip.style.padding = '0.5rem';
            tooltip.style.borderRadius = '4px';
            tooltip.style.fontSize = '0.875rem';
            tooltip.style.zIndex = '9999';
            tooltip.style.pointerEvents = 'none';
            
            document.body.appendChild(tooltip);
            
            const rect = this.getBoundingClientRect();
            tooltip.style.left = rect.left + 'px';
            tooltip.style.top = (rect.top - tooltip.offsetHeight - 5) + 'px';
            
            this._tooltip = tooltip;
        });
        
        element.addEventListener('mouseleave', function() {
            if (this._tooltip) {
                this._tooltip.remove();
                this._tooltip = null;
            }
        });
    });
}

/**
 * Create enhanced analysis header with smart filter chips
 * @param {Object} analysis - Analysis results object
 * @param {Array} filteredErrors - Currently filtered errors array
 * @returns {string} - HTML string for enhanced analysis header
 */
function createEnhancedAnalysisHeader(analysis, filteredErrors) {
    const totalErrors = analysis.errors?.length || 0;
    const showingCount = filteredErrors.length;
    
    // Create filter chips if SmartFilterChips is available
    const filterChips = window.SmartFilterChips && window.SmartFilterSystem ? 
        window.SmartFilterChips.createSmartFilterChips(
            window.SmartFilterSystem.totalCounts, 
            window.SmartFilterSystem.activeFilters
        ) : '';
    
    // Create filter statistics
    const filterStats = window.SmartFilterChips && totalErrors > 0 ? 
        window.SmartFilterChips.createFilterStatistics(totalErrors, showingCount, 
            window.SmartFilterSystem ? window.SmartFilterSystem.activeFilters : new Set()) : '';
    
    return `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h2 class="pf-v5-c-title pf-m-xl">
                        <i class="fas fa-search pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                        Analysis Results
                    </h2>
                </div>
                <div class="pf-v5-c-card__actions">
                    <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-align-items-center">
                        <div class="pf-v5-l-flex__item">
                            <span class="pf-v5-c-label pf-m-${totalErrors > 0 ? 'orange' : 'green'}">
                                <span class="pf-v5-c-label__content">
                                    <i class="fas fa-${totalErrors > 0 ? 'exclamation-triangle' : 'check-circle'} pf-v5-c-label__icon"></i>
                                    ${totalErrors > 0 ? `Showing ${showingCount} of ${totalErrors} Issues` : 'No Issues Found'}
                                </span>
                            </span>
                        </div>
                        <div class="pf-v5-l-flex__item">
                            <button class="pf-v5-c-button pf-m-link pf-m-inline" type="button" onclick="scrollToStatistics()">
                                <i class="fas fa-chart-line pf-v5-u-mr-xs"></i>
                                View Stats
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            ${filterChips ? `
                <div class="pf-v5-c-card__body">
                    ${filterChips}
                    ${filterStats}
                </div>
            ` : ''}
        </div>
    `;
}

/**
 * Refresh display with current filter settings
 * Called when filters change to update the UI dynamically
 * FIXED: Prevent infinite callback loop by using direct filtering
 */
function refreshDisplayWithFilters() {
    // Only refresh if we have current analysis data
    if (!currentAnalysis || !currentContent) {
        console.warn('RefreshDisplayWithFilters: No current analysis data available');
        return;
    }
    
    const errors = currentAnalysis.errors || [];
    
    // Use the already filtered errors from SmartFilterSystem
    let filteredErrors = errors;
    if (window.SmartFilterSystem) {
        // Use the already filtered errors instead of re-filtering
        filteredErrors = window.SmartFilterSystem.filteredErrors || [];
        
        // SAFETY: If filteredErrors is empty but we have originalErrors, reapply filters
        if (filteredErrors.length === 0 && window.SmartFilterSystem.originalErrors.length > 0) {
            filteredErrors = window.SmartFilterSystem.originalErrors.filter(error => {
                const severityLevel = window.SmartFilterSystem.getSeverityLevel(error);
                return window.SmartFilterSystem.activeFilters.has(severityLevel);
            });
            // Update the system's filteredErrors
            window.SmartFilterSystem.filteredErrors = filteredErrors;
        }
        
        // Ensure counts are up to date
        window.SmartFilterSystem.updateCounts(errors);
    }
    
    // Update main content areas with filtered errors
    updateContentDisplay(filteredErrors);
    updateErrorSummary(filteredErrors);
    updateStatisticsDisplay(currentAnalysis, filteredErrors);
    updateFilterChipsDisplay();
    
    // Update the header statistics message
    updateAnalysisHeaderCounts(errors.length, filteredErrors.length);
    
    // Update the filter statistics display ("X issues (Y hidden)")
    updateFilterStatisticsDisplay(errors.length, filteredErrors.length);
    
    console.log(`🔄 Display refreshed with ${filteredErrors.length} filtered errors`);
}

/**
 * Update content display with filtered errors
 * @param {Array} filteredErrors - Currently filtered errors
 * @private
 */
function updateContentDisplay(filteredErrors) {
    const contentContainer = document.querySelector('.pf-v5-l-stack__item:nth-child(2)');
    if (!contentContainer) return;
    
    // Use original blocks instead of potentially filtered ones
    const hasStructuralBlocks = window.originalStructuralBlocks && window.originalStructuralBlocks.length > 0;
    
    if (hasStructuralBlocks) {
        contentContainer.innerHTML = displayStructuralBlocks(window.originalStructuralBlocks, filteredErrors);
    } else {
        contentContainer.innerHTML = displayFlatContent(currentContent, filteredErrors);
    }
}

/**
 * Update error summary with filtered errors
 * @param {Array} filteredErrors - Currently filtered errors
 * @private
 */
function updateErrorSummary(filteredErrors) {
    const errorSummaryContainer = document.querySelector('.pf-v5-l-stack__item:nth-child(3)');
    if (!errorSummaryContainer) return;
    
    if (filteredErrors.length > 0) {
        errorSummaryContainer.innerHTML = createErrorSummary(filteredErrors);
        errorSummaryContainer.style.display = 'block';
    } else {
        errorSummaryContainer.style.display = 'none';
    }
}

/**
 * Update statistics display with filtered errors
 * @param {Object} analysis - Analysis results object
 * @param {Array} filteredErrors - Currently filtered errors
 * @private
 */
function updateStatisticsDisplay(analysis, filteredErrors) {
    const statisticsColumn = document.getElementById('statistics-column');
    if (!statisticsColumn) return;
    
    statisticsColumn.innerHTML = generateStatisticsCard(analysis, filteredErrors);
}

/**
 * Update filter chips display after filter state changes
 * @private
 */
function updateFilterChipsDisplay() {
    if (window.SmartFilterChips && window.SmartFilterSystem) {
        window.SmartFilterChips.updateFilterChipsDisplay(
            window.SmartFilterSystem.totalCounts,
            window.SmartFilterSystem.activeFilters
        );
    }
}

/**
 * Update the analysis header statistics display
 * DIRECT FIX: Updates the "Showing X of Y Issues" message
 * @param {number} totalErrors - Total number of errors
 * @param {number} filteredErrors - Number of filtered errors
 * @private
 */
function updateAnalysisHeaderCounts(totalErrors, filteredErrors) {
    const headerLabel = document.querySelector('.pf-v5-c-card__actions .pf-v5-c-label__content');
    if (headerLabel) {
        const icon = headerLabel.querySelector('i');
        const iconClass = totalErrors > 0 ? 'fas fa-exclamation-triangle' : 'fas fa-check-circle';
        const labelClass = totalErrors > 0 ? 'orange' : 'green';
        
        // Update the message
        if (totalErrors > 0) {
            headerLabel.innerHTML = `
                <i class="${iconClass} pf-v5-c-label__icon"></i>
                Showing ${filteredErrors} of ${totalErrors} Issues
            `;
        } else {
            headerLabel.innerHTML = `
                <i class="${iconClass} pf-v5-c-label__icon"></i>
                No Issues Found
            `;
        }
        
        // Update the label color
        const labelElement = headerLabel.closest('.pf-v5-c-label');
        if (labelElement) {
            labelElement.className = `pf-v5-c-label pf-m-${labelClass}`;
        }
    }
}

/**
 * Update the filter statistics display ("Showing X of Y issues (Z hidden)")
 * DIRECT FIX: Updates the yellow/orange alert message below filter chips
 * @param {number} totalErrors - Total number of errors
 * @param {number} filteredErrors - Number of filtered errors  
 * @private
 */
function updateFilterStatisticsDisplay(totalErrors, filteredErrors) {
    if (!window.SmartFilterChips || !window.SmartFilterSystem) return;
    
    // Find the existing filter statistics container
    const existingStats = document.querySelector('.filter-statistics');
    if (existingStats) {
        // Generate new statistics HTML
        const newStatsHtml = window.SmartFilterChips.createFilterStatistics(
            totalErrors, 
            filteredErrors, 
            window.SmartFilterSystem.activeFilters
        );
        
        // Replace the existing statistics
        if (newStatsHtml) {
            existingStats.outerHTML = newStatsHtml;
        } else {
            existingStats.remove();
        }
    }
}
