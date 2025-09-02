/**
 * Modular Compliance Display Component
 * Integrates with existing PatternFly design system
 * NO duplicate code, uses existing patterns and classes
 */

/**
 * Display modular compliance results in existing layout
 * Integrates seamlessly with current PatternFly design
 */
function displayModularComplianceResults(complianceData, content_type = 'concept') {
    if (!complianceData) return;

    // Create compliance section and insert after main results
    const complianceSection = createModularComplianceSection(complianceData, content_type);
    const resultsContainer = document.getElementById('analysis-results');
    
    if (resultsContainer) {
        // Remove existing compliance section if present
        const existingCompliance = document.getElementById('modular-compliance-section');
        if (existingCompliance) {
            existingCompliance.remove();
        }
        
        // Insert compliance section after existing results
        const mainGrid = resultsContainer.querySelector('.pf-v5-l-grid');
        if (mainGrid) {
            // Add as new grid item
            const complianceGridItem = document.createElement('div');
            complianceGridItem.className = 'pf-v5-l-grid__item pf-m-12-col';
            complianceGridItem.appendChild(complianceSection);
            mainGrid.appendChild(complianceGridItem);
        } else {
            // Fallback: append to results container
            resultsContainer.appendChild(complianceSection);
        }
    }
}

/**
 * Create modular compliance section using existing PatternFly patterns
 */
function createModularComplianceSection(complianceData, content_type) {
    const section = document.createElement('div');
    section.id = 'modular-compliance-section';
    section.className = 'pf-v5-c-card app-card pf-v5-u-mt-lg'; // Use existing app-card class
    
    const moduleType = complianceData.content_type || content_type || 'concept';
    const totalIssues = complianceData.total_issues || 0;
    const issuesBySeverity = complianceData.issues_by_severity || {};
    const complianceStatus = complianceData.compliance_status || 'unknown';
    const issues = complianceData.issues || [];
    
    // Determine status styling using existing patterns
    const statusInfo = getComplianceStatusInfo(complianceStatus, totalIssues);
    
    section.innerHTML = `
        <div class="pf-v5-c-card__header">
            <div class="pf-v5-c-card__header-main">
                <h2 class="pf-v5-c-title pf-m-xl">
                    <i class="fas fa-clipboard-check pf-v5-u-mr-sm" style="color: ${statusInfo.iconColor};"></i>
                    Modular Documentation Compliance
                </h2>
                <p class="pf-v5-c-card__subtitle">
                    ${capitalizeFirst(moduleType)} Module Validation
                </p>
            </div>
            <div class="pf-v5-c-card__actions">
                <span class="pf-v5-c-label ${statusInfo.labelClass}">
                    <span class="pf-v5-c-label__content">
                        <i class="fas fa-${statusInfo.labelIcon} pf-v5-c-label__icon"></i>
                        ${statusInfo.statusText}
                    </span>
                </span>
            </div>
        </div>
        
        <div class="pf-v5-c-card__body">
            <!-- Status Alert -->
            <div class="pf-v5-c-alert pf-m-${statusInfo.alertType} pf-m-inline pf-v5-u-mb-lg">
                <div class="pf-v5-c-alert__icon">
                    <i class="fas fa-${statusInfo.alertIcon}"></i>
                </div>
                <h4 class="pf-v5-c-alert__title">${statusInfo.alertTitle}</h4>
                <div class="pf-v5-c-alert__description">
                    ${getComplianceMessage(complianceStatus, totalIssues, moduleType)}
                </div>
            </div>
            
            <!-- Statistics Grid -->
            ${createComplianceStatisticsGrid(issuesBySeverity, totalIssues)}
            
            <!-- Issues List -->
            ${totalIssues > 0 ? createComplianceIssuesSection(issues) : ''}
        </div>
    `;
    
    return section;
}

/**
 * Create compliance statistics using existing PatternFly grid
 */
function createComplianceStatisticsGrid(issuesBySeverity, totalIssues) {
    if (totalIssues === 0) {
        return `
            <div class="pf-v5-c-empty-state pf-m-sm pf-v5-u-mb-lg">
                <div class="pf-v5-c-empty-state__content">
                    <div class="pf-v5-c-empty-state__icon">
                        <i class="fas fa-check-circle" style="color: var(--pf-v5-global--success-color--100);"></i>
                    </div>
                    <h3 class="pf-v5-c-title pf-m-lg">Excellent compliance!</h3>
                    <div class="pf-v5-c-empty-state__body">
                        Your module meets all requirements for this module type.
                    </div>
                </div>
            </div>
        `;
    }

    const highIssues = issuesBySeverity.high || 0;
    const mediumIssues = issuesBySeverity.medium || 0;
    const lowIssues = issuesBySeverity.low || 0;

    return `
        <div class="pf-v5-l-grid pf-m-gutter pf-v5-u-mb-lg">
            <div class="pf-v5-l-grid__item pf-m-3-col-on-lg pf-m-6-col">
                <div class="pf-v5-c-card pf-m-plain">
                    <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                        <div style="font-size: 2rem; font-weight: 700; color: var(--pf-v5-global--danger-color--100); margin-bottom: 0.5rem;">
                            ${highIssues}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--pf-v5-global--Color--200);">
                            Critical Issues
                        </div>
                    </div>
                </div>
            </div>
            <div class="pf-v5-l-grid__item pf-m-3-col-on-lg pf-m-6-col">
                <div class="pf-v5-c-card pf-m-plain">
                    <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                        <div style="font-size: 2rem; font-weight: 700; color: var(--pf-v5-global--warning-color--100); margin-bottom: 0.5rem;">
                            ${mediumIssues}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--pf-v5-global--Color--200);">
                            Warnings
                        </div>
                    </div>
                </div>
            </div>
            <div class="pf-v5-l-grid__item pf-m-3-col-on-lg pf-m-6-col">
                <div class="pf-v5-c-card pf-m-plain">
                    <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                        <div style="font-size: 2rem; font-weight: 700; color: var(--pf-v5-global--info-color--100); margin-bottom: 0.5rem;">
                            ${lowIssues}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--pf-v5-global--Color--200);">
                            Suggestions
                        </div>
                    </div>
                </div>
            </div>
            <div class="pf-v5-l-grid__item pf-m-3-col-on-lg pf-m-6-col">
                <div class="pf-v5-c-card pf-m-plain">
                    <div class="pf-v5-c-card__body pf-v5-u-text-align-center">
                        <div style="font-size: 2rem; font-weight: 700; color: var(--pf-v5-global--Color--100); margin-bottom: 0.5rem;">
                            ${totalIssues}
                        </div>
                        <div style="font-size: 0.875rem; color: var(--pf-v5-global--Color--200);">
                            Total Issues
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Create compliance issues section using existing error display patterns
 */
function createComplianceIssuesSection(issues) {
    const sortedIssues = [...issues].sort((a, b) => {
        const severityOrder = { 'high': 0, 'medium': 1, 'low': 2 };
        return severityOrder[a.severity] - severityOrder[b.severity];
    });

    return `
        <div class="pf-v5-u-mb-lg">
            <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-md">
                <i class="fas fa-list-ul pf-v5-u-mr-sm"></i>
                Compliance Issues
            </h3>
            <div class="pf-v5-l-stack pf-m-gutter">
                ${sortedIssues.map((issue, index) => createComplianceIssueCard(issue, index)).join('')}
            </div>
        </div>
    `;
}

/**
 * Create individual compliance issue card using existing patterns
 */
function createComplianceIssueCard(issue, index) {
    const severity = issue.severity || 'medium';
    const alertType = getAlertTypeFromSeverity(severity);
    const lineInfo = issue.line_number ? ` (Line ${issue.line_number})` : '';
    const suggestions = issue.suggestions || [];
    
    return `
        <div class="pf-v5-l-stack__item">
            <div class="pf-v5-c-alert pf-m-${alertType} pf-m-expandable ${index < 3 ? '' : 'pf-m-expanded'}">
                <div class="pf-v5-c-alert__toggle">
                    <button class="pf-v5-c-button pf-m-plain" onclick="toggleComplianceIssue(this)">
                        <span class="pf-v5-c-alert__toggle-icon">
                            <i class="fas fa-angle-right"></i>
                        </span>
                    </button>
                </div>
                <div class="pf-v5-c-alert__icon">
                    <i class="fas fa-${getIssueIconFromSeverity(severity)}"></i>
                </div>
                <h4 class="pf-v5-c-alert__title">
                    ${escapeHtml(issue.message || 'Compliance issue')}${lineInfo}
                </h4>
                <div class="pf-v5-c-alert__description ${index < 3 ? '' : 'pf-m-hidden'}">
                    <p class="pf-v5-u-mb-md">${escapeHtml(issue.description || 'No description available')}</p>
                    ${issue.flagged_text ? `
                        <div class="pf-v5-u-mb-md">
                            <strong>Flagged content:</strong>
                            <div class="pf-v5-c-code-block pf-v5-u-mt-sm">
                                <div class="pf-v5-c-code-block__content">
                                    <pre class="pf-v5-c-code-block__code">${escapeHtml(issue.flagged_text)}</pre>
                                </div>
                            </div>
                        </div>
                    ` : ''}
                    ${suggestions.length > 0 ? `
                        <div>
                            <strong>Suggestions:</strong>
                            <ul class="pf-v5-c-list pf-v5-u-mt-sm">
                                ${suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

/**
 * Get compliance status information for styling
 */
function getComplianceStatusInfo(status, totalIssues) {
    switch (status) {
        case 'compliant':
            return {
                iconColor: 'var(--pf-v5-global--success-color--100)',
                labelClass: 'pf-m-green',
                labelIcon: 'check-circle',
                statusText: 'Compliant',
                alertType: 'success',
                alertIcon: 'check-circle',
                alertTitle: 'Module is compliant'
            };
        case 'mostly_compliant':
            return {
                iconColor: 'var(--pf-v5-global--info-color--100)',
                labelClass: 'pf-m-blue',
                labelIcon: 'info-circle',
                statusText: 'Mostly Compliant',
                alertType: 'info',
                alertIcon: 'info-circle',
                alertTitle: 'Module is mostly compliant'
            };
        case 'needs_improvement':
            return {
                iconColor: 'var(--pf-v5-global--warning-color--100)',
                labelClass: 'pf-m-orange',
                labelIcon: 'exclamation-triangle',
                statusText: 'Needs Improvement',
                alertType: 'warning',
                alertIcon: 'exclamation-triangle',
                alertTitle: 'Module needs improvement'
            };
        case 'non_compliant':
        default:
            return {
                iconColor: 'var(--pf-v5-global--danger-color--100)',
                labelClass: 'pf-m-red',
                labelIcon: 'times-circle',
                statusText: 'Non-Compliant',
                alertType: 'danger',
                alertIcon: 'times-circle',
                alertTitle: 'Module is not compliant'
            };
    }
}

/**
 * Get appropriate compliance message
 */
function getComplianceMessage(status, totalIssues, moduleType) {
    const moduleTypeDisplay = capitalizeFirst(moduleType);
    
    switch (status) {
        case 'compliant':
            return `This ${moduleTypeDisplay} module meets all Red Hat modular documentation standards.`;
        case 'mostly_compliant':
            return `This ${moduleTypeDisplay} module meets most requirements with ${totalIssues} minor ${totalIssues === 1 ? 'issue' : 'issues'} to address.`;
        case 'needs_improvement':
            return `This ${moduleTypeDisplay} module has ${totalIssues} ${totalIssues === 1 ? 'issue' : 'issues'} that should be addressed to improve compliance.`;
        case 'non_compliant':
        default:
            return `This ${moduleTypeDisplay} module has ${totalIssues} ${totalIssues === 1 ? 'issue' : 'issues'} that must be resolved to meet compliance standards.`;
    }
}

/**
 * Helper functions using existing patterns
 */
function getAlertTypeFromSeverity(severity) {
    switch (severity) {
        case 'high': return 'danger';
        case 'medium': return 'warning';
        case 'low': return 'info';
        default: return 'warning';
    }
}

function getIssueIconFromSeverity(severity) {
    switch (severity) {
        case 'high': return 'times-circle';
        case 'medium': return 'exclamation-triangle';
        case 'low': return 'info-circle';
        default: return 'exclamation-triangle';
    }
}

function capitalizeFirst(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Toggle compliance issue details
 * Uses existing expandable pattern
 */
function toggleComplianceIssue(button) {
    const alert = button.closest('.pf-v5-c-alert');
    const description = alert.querySelector('.pf-v5-c-alert__description');
    const icon = button.querySelector('.pf-v5-c-alert__toggle-icon i');
    
    if (description.classList.contains('pf-m-hidden')) {
        description.classList.remove('pf-m-hidden');
        icon.className = 'fas fa-angle-down';
        alert.classList.add('pf-m-expanded');
    } else {
        description.classList.add('pf-m-hidden');
        icon.className = 'fas fa-angle-right';
        alert.classList.remove('pf-m-expanded');
    }
}

/**
 * Escape HTML to prevent XSS (use existing function if available)
 */
function escapeHtml(text) {
    if (!text) return '';
    
    // Check if there's an existing escapeHtml function in the global scope (from other modules)
    if (typeof window.escapeHtml === 'function' && window.escapeHtml !== escapeHtml) {
        return window.escapeHtml(text);
    }
    
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Export functions for global access
window.displayModularComplianceResults = displayModularComplianceResults;
window.toggleComplianceIssue = toggleComplianceIssue;
