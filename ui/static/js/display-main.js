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
            <div class="pf-v5-l-grid__item pf-m-8-col-on-md pf-m-12-col">
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

                    <!-- Modular Compliance Section - NEW for Phase 4 -->
                    ${analysis.modular_compliance ? `
                        <div class="pf-v5-l-stack__item">
                            ${generateModularComplianceSection(analysis.modular_compliance)}
                        </div>
                    ` : ''}
                </div>
            </div>
            <div class="pf-v5-l-grid__item pf-m-4-col-on-md pf-m-12-col" id="statistics-column">
                ${generateStatisticsCard(analysis)}
                
                <!-- Modular Compliance Statistics - NEW for Phase 4 -->
                ${analysis.modular_compliance ? `
                    ${generateModularComplianceStats(analysis.modular_compliance)}
                ` : ''}
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

// NEW Phase 4: Modular Compliance Display Functions

function generateModularComplianceSection(complianceData) {
    const { content_type, total_issues, compliance_status, issues_by_severity, issues } = complianceData;
    
    // Map compliance status to PatternFly alert variants
    const getStatusVariant = (status) => {
        switch (status) {
            case 'compliant': return 'success';
            case 'mostly_compliant': return 'info';
            case 'needs_improvement': return 'warning';
            case 'non_compliant': return 'danger';
            default: return 'info';
        }
    };
    
    // Get status icon
    const getStatusIcon = (status) => {
        switch (status) {
            case 'compliant': return 'fa-check-circle';
            case 'mostly_compliant': return 'fa-info-circle';
            case 'needs_improvement': return 'fa-exclamation-triangle';
            case 'non_compliant': return 'fa-times-circle';
            default: return 'fa-question-circle';
        }
    };
    
    // Get human-readable status text
    const getStatusText = (status) => {
        switch (status) {
            case 'compliant': return 'Fully Compliant';
            case 'mostly_compliant': return 'Mostly Compliant';
            case 'needs_improvement': return 'Needs Improvement';
            case 'non_compliant': return 'Non-Compliant';
            default: return 'Unknown';
        }
    };
    
    const statusVariant = getStatusVariant(compliance_status);
    const statusIcon = getStatusIcon(compliance_status);
    const statusText = getStatusText(compliance_status);
    
    return `
        <div class="pf-v5-c-card modular-compliance-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h3 class="pf-v5-c-title pf-m-lg">
                        <i class="fas fa-book-open pf-v5-u-mr-sm" style="color: var(--pf-v5-global--primary-color--100);"></i>
                        Modular Documentation Compliance
                    </h3>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-${statusVariant}">
                        <span class="pf-v5-c-label__content">
                            <i class="fas ${statusIcon} pf-v5-c-label__icon"></i>
                            ${statusText}
                        </span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <!-- Module Type Info -->
                <div class="pf-v5-u-mb-md">
                    <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-align-items-center">
                        <div class="pf-v5-l-flex__item">
                            <span class="pf-v5-c-label pf-m-blue pf-m-compact">
                                <span class="pf-v5-c-label__content">
                                    <i class="fas fa-tag pf-v5-c-label__icon"></i>
                                    ${content_type.charAt(0).toUpperCase() + content_type.slice(1)} Module
                                </span>
                            </span>
                        </div>
                        <div class="pf-v5-l-flex__item">
                            <button class="pf-v5-c-button pf-m-link pf-m-inline" onclick="showModuleGuide('${content_type}')">
                                <i class="fas fa-info-circle pf-v5-u-mr-xs"></i>
                                Module Guidelines
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Issues Summary -->
                ${total_issues > 0 ? `
                    <div class="pf-v5-u-mb-lg">
                        <div class="pf-v5-l-grid pf-m-gutter">
                            <div class="pf-v5-l-grid__item pf-m-4-col">
                                <div class="compliance-stat-item ${issues_by_severity.high > 0 ? 'stat-danger' : ''}">
                                    <div class="stat-number">${issues_by_severity.high || 0}</div>
                                    <div class="stat-label">Must Fix (FAIL)</div>
                                </div>
                            </div>
                            <div class="pf-v5-l-grid__item pf-m-4-col">
                                <div class="compliance-stat-item ${issues_by_severity.medium > 0 ? 'stat-warning' : ''}">
                                    <div class="stat-number">${issues_by_severity.medium || 0}</div>
                                    <div class="stat-label">Should Address (WARN)</div>
                                </div>
                            </div>
                            <div class="pf-v5-l-grid__item pf-m-4-col">
                                <div class="compliance-stat-item ${issues_by_severity.low > 0 ? 'stat-info' : ''}">
                                    <div class="stat-number">${issues_by_severity.low || 0}</div>
                                    <div class="stat-label">Nice to Have (INFO)</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Issues List -->
                    <div class="compliance-issues">
                        <h4 class="pf-v5-c-title pf-m-md pf-v5-u-mb-sm">Compliance Issues</h4>
                        <div class="pf-v5-l-stack pf-m-gutter-sm">
                            ${issues.map(issue => generateComplianceIssueCard(issue)).join('')}
                        </div>
                    </div>
                ` : `
                    <div class="pf-v5-c-empty-state pf-m-sm">
                        <div class="pf-v5-c-empty-state__content">
                            <i class="fas fa-check-circle pf-v5-c-empty-state__icon" style="color: var(--pf-v5-global--success-color--100);"></i>
                            <h4 class="pf-v5-c-title pf-m-lg">Excellent work!</h4>
                            <div class="pf-v5-c-empty-state__body">
                                Your ${content_type} module meets all Red Hat modular documentation standards.
                            </div>
                        </div>
                    </div>
                `}
            </div>
        </div>
    `;
}

function generateComplianceIssueCard(issue) {
    // Map severity to issue type labels
    const getSeverityLabel = (severity) => {
        switch (severity) {
            case 'high': return 'FAIL';
            case 'medium': return 'WARN';
            case 'low': return 'INFO';
            default: return 'INFO';
        }
    };
    
    const getSeverityVariant = (severity) => {
        switch (severity) {
            case 'high': return 'red';
            case 'medium': return 'orange';
            case 'low': return 'blue';
            default: return 'blue';
        }
    };
    
    const severityLabel = getSeverityLabel(issue.severity);
    const severityVariant = getSeverityVariant(issue.severity);
    
    return `
        <div class="pf-v5-c-card pf-m-compact compliance-issue-card severity-${issue.severity}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <span class="pf-v5-c-label pf-m-${severityVariant} pf-m-compact">
                        <span class="pf-v5-c-label__content">${severityLabel}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="compliance-issue-content">
                    <p class="issue-message">${issue.message}</p>
                    ${issue.suggestions && issue.suggestions.length > 0 ? `
                        <div class="pf-v5-u-mt-sm">
                            <details class="compliance-suggestions">
                                <summary class="pf-v5-c-button pf-m-link pf-m-inline pf-m-small">
                                    <i class="fas fa-lightbulb pf-v5-u-mr-xs"></i>
                                    View Suggestions (${issue.suggestions.length})
                                </summary>
                                <div class="pf-v5-u-mt-sm">
                                    <ul class="pf-v5-c-list">
                                        ${issue.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                                    </ul>
                                </div>
                            </details>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

function generateModularComplianceStats(complianceData) {
    const { content_type, total_issues, compliance_status, issues_by_severity } = complianceData;
    
    // Calculate compliance percentage
    const calculateComplianceScore = () => {
        const criticalIssues = issues_by_severity.high || 0;
        const warnings = issues_by_severity.medium || 0;
        const info = issues_by_severity.low || 0;
        
        // Score based on issue severity (critical issues heavily penalized)
        let score = 100;
        score -= (criticalIssues * 30);  // Critical issues: -30 points each
        score -= (warnings * 10);       // Warnings: -10 points each
        score -= (info * 5);           // Info: -5 points each
        
        return Math.max(0, Math.min(100, score));
    };
    
    const complianceScore = calculateComplianceScore();
    const getScoreStatus = (score) => {
        if (score >= 90) return 'success';
        if (score >= 70) return 'warning';
        return 'danger';
    };
    
    return `
        <div class="pf-v5-c-card pf-v5-u-mt-md" style="margin-top: 1rem;">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h3 class="pf-v5-c-title pf-m-lg">
                        <i class="fas fa-clipboard-check pf-v5-u-mr-sm" style="color: var(--pf-v5-global--primary-color--100);"></i>
                        Compliance Score
                    </h3>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <!-- Compliance Score Gauge -->
                <div class="pf-v5-u-text-align-center pf-v5-u-mb-lg">
                    <div class="compliance-score-circle">
                        <div class="score-number">${complianceScore}</div>
                        <div class="score-label">Compliance</div>
                    </div>
                </div>
                
                <!-- Progress Bar -->
                <div class="pf-v5-u-mb-md">
                    <div class="pf-v5-c-progress pf-m-${getScoreStatus(complianceScore)}">
                        <div class="pf-v5-c-progress__description">Overall Compliance</div>
                        <div class="pf-v5-c-progress__status">
                            <span class="pf-v5-c-progress__measure">${complianceScore}%</span>
                        </div>
                        <div class="pf-v5-c-progress__bar">
                            <div class="pf-v5-c-progress__indicator" style="width: ${complianceScore}%;">
                                <span class="pf-v5-screen-reader">Progress value</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Module Info -->
                <div class="pf-v5-l-stack pf-m-gutter-sm">
                    <div class="pf-v5-l-stack__item">
                        <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-space-between">
                            <div class="pf-v5-l-flex__item">Module Type</div>
                            <div class="pf-v5-l-flex__item">
                                <strong>${content_type.charAt(0).toUpperCase() + content_type.slice(1)}</strong>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-l-stack__item">
                        <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-space-between">
                            <div class="pf-v5-l-flex__item">Total Issues</div>
                            <div class="pf-v5-l-flex__item">
                                <strong>${total_issues}</strong>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-l-stack__item">
                        <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-justify-content-space-between">
                            <div class="pf-v5-l-flex__item">Status</div>
                            <div class="pf-v5-l-flex__item">
                                <strong>${compliance_status.replace('_', ' ')}</strong>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Show module guidelines modal
function showModuleGuide(moduleType) {
    const guidelines = {
        concept: {
            title: "Concept Module Guidelines",
            description: "Concept modules explain what something is or how it works.",
            requirements: [
                "Start with a clear introductory paragraph",
                "Focus on explaining concepts, not procedures",
                "Use descriptive content, avoid imperative verbs",
                "Include examples and context where helpful"
            ]
        },
        procedure: {
            title: "Procedure Module Guidelines", 
            description: "Procedure modules provide step-by-step instructions.",
            requirements: [
                "Title should be a gerund phrase (ending in -ing)",
                "Include brief introduction explaining the purpose",
                "Provide numbered steps with clear actions",
                "Each step should contain a single action"
            ]
        },
        reference: {
            title: "Reference Module Guidelines",
            description: "Reference modules provide quick lookup information.",
            requirements: [
                "Start with brief introduction explaining the reference data",
                "Organize content in scannable format (tables, lists)",
                "Avoid long paragraphs of explanatory text",
                "Focus on factual, structured information"
            ]
        }
    };
    
    const guide = guidelines[moduleType];
    if (!guide) return;
    
    // Simple alert for now - could be enhanced to modal dialog
    alert(`${guide.title}\n\n${guide.description}\n\nKey Requirements:\n• ${guide.requirements.join('\n• ')}`);
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
