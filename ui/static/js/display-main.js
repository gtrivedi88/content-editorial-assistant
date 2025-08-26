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

    // Use enhanced PatternFly Grid layout for better responsiveness
    resultsContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-8-col-on-lg pf-m-12-col">
                <div class="pf-v5-l-stack pf-m-gutter">
                    <!-- Analysis Header -->
                    <div class="pf-v5-l-stack__item">
                        <div class="pf-v5-c-card app-card">
                            <div class="pf-v5-c-card__header">
                                <div class="pf-v5-c-card__header-main">
                                    <h2 class="pf-v5-c-title pf-m-xl">
                                        <i class="fas fa-search pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                                        Analysis Results
                                    </h2>
                                </div>
                                <div class="pf-v5-c-card__actions">
                                    <div class="pf-v5-l-flex pf-m-space-items-sm">
                                        <div class="pf-v5-l-flex__item">
                                            <span class="pf-v5-c-label pf-m-${analysis.errors?.length > 0 ? 'orange' : 'green'}">
                                                <span class="pf-v5-c-label__content">
                                                    <i class="fas fa-${analysis.errors?.length > 0 ? 'exclamation-triangle' : 'check-circle'} pf-v5-c-label__icon"></i>
                                                    ${analysis.errors?.length || 0} Issues
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
                        </div>
                    </div>

                    <!-- Content Display -->
                    <div class="pf-v5-l-stack__item">
                        ${structuralBlocks ? displayStructuralBlocks(structuralBlocks) : displayFlatContent(content, analysis.errors)}
                    </div>

                    <!-- Error Summary - Only show for plain text analysis, not for structural blocks -->
                    ${!structuralBlocks && analysis.errors?.length > 0 ? `
                        <div class="pf-v5-l-stack__item">
                            ${createErrorSummary(analysis.errors)}
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="pf-v5-l-grid__item pf-m-4-col-on-lg pf-m-12-col" id="statistics-column">
                ${generateStatisticsCard(analysis)}
            </div>
        </div>
    `;

    // Add smooth scroll behavior
    resultsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Initialize expandable sections and other interactive elements
    initializeExpandableSections();
    initializeTooltips();
}

// Display structural blocks using enhanced PatternFly Cards
function displayStructuralBlocks(blocks) {
    if (!blocks || blocks.length === 0) return displayEmptyStructure();

    // Store blocks globally for rewriteBlock function access
    window.currentStructuralBlocks = blocks;

    // Work directly with blocks - no need for complex attribute placeholders
    let displayIndex = 0;
    const blocksHtml = blocks.map(block => {
        const html = createStructuralBlock(block, displayIndex, blocks);
        if (html) { // Check for non-empty HTML
            displayIndex++;
        }
        return html;
    }).filter(html => html).join('');

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

    rewriteContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
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

    rewriteContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
        errorSummary.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
