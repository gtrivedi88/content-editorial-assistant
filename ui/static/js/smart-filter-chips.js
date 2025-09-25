/**
 * Smart Filter Chips UI Components
 * PatternFly-based filter chips with world-class UX
 * 
 * Integrates seamlessly with existing Style Guide AI design system
 * Zero technical debt, accessibility compliant, high performance
 */

/**
 * Create smart filter chips container
 * @param {Object} totalCounts - Count of errors by severity level
 * @param {Set} activeFilters - Currently active filter levels
 * @returns {string} - HTML string for filter chips container
 */
function createSmartFilterChips(totalCounts, activeFilters) {
    // Validate inputs with graceful fallbacks
    const counts = totalCounts || { critical: 0, error: 0, warning: 0, suggestion: 0 };
    const filters = activeFilters || new Set(['critical', 'error', 'warning', 'suggestion']);
    
    // Filter chip configuration matching existing design patterns
    const chipConfigs = [
        { 
            level: 'critical', 
            label: 'Critical', 
            icon: 'fas fa-exclamation-circle',
            color: 'pf-m-red',
            bgColor: 'var(--pf-v5-global--danger-color--100)',
            description: 'Critical issues requiring immediate attention'
        },
        { 
            level: 'error', 
            label: 'Error', 
            icon: 'fas fa-times-circle',
            color: 'pf-m-red',
            bgColor: 'var(--pf-v5-global--danger-color--200)',
            description: 'Errors that should be addressed'
        },
        { 
            level: 'warning', 
            label: 'Warning', 
            icon: 'fas fa-exclamation-triangle',
            color: 'pf-m-orange',
            bgColor: 'var(--pf-v5-global--warning-color--100)',
            description: 'Warnings that may need attention'
        },
        { 
            level: 'suggestion', 
            label: 'Suggestion', 
            icon: 'fas fa-lightbulb',
            color: 'pf-m-blue',
            bgColor: 'var(--pf-v5-global--info-color--100)',
            description: 'Suggestions for improvement'
        }
    ];

    return `
        <div class="smart-filter-container pf-v5-u-mb-md" role="toolbar" aria-label="Filter analysis results by severity">
            <div class="pf-v5-l-flex pf-m-space-items-sm pf-m-align-items-center">
                <div class="pf-v5-l-flex__item">
                    <span class="pf-v5-c-content">
                        <strong>Filter by severity:</strong>
                    </span>
                </div>
                ${chipConfigs.map(config => createFilterChip(config, counts, filters)).join('')}
                <div class="pf-v5-l-flex__item">
                    ${createResetButton()}
                </div>
                <div class="pf-v5-l-flex__item pf-v5-u-ml-auto">
                    ${createFilterPresets()}
                </div>
            </div>
        </div>
    `;
}

/**
 * Create individual filter chip
 * @param {Object} config - Filter chip configuration
 * @param {Object} totalCounts - Count of errors by severity level
 * @param {Set} activeFilters - Currently active filter levels
 * @returns {string} - HTML string for filter chip
 */
function createFilterChip(config, totalCounts, activeFilters) {
    const count = totalCounts[config.level] || 0;
    const isActive = activeFilters.has(config.level);
    const isDisabled = count === 0;
    
    // Check if this is exclusive filtering (only one filter active)
    const isExclusive = activeFilters.size === 1 && isActive;
    
    // Determine chip styling based on state
    let chipClass = isActive ? 
        `pf-v5-c-chip ${config.color}` : 
        `pf-v5-c-chip pf-m-outline`;
    
    // Add exclusive indicator styling
    if (isExclusive) {
        chipClass += ' exclusive-filter';
    }
    
    const styles = [];
    if (isDisabled) {
        styles.push('opacity: 0.4');
        styles.push('cursor: not-allowed');
    } else {
        styles.push('cursor: pointer');
        styles.push('transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1)');
        
        // Add glow effect for exclusive selection
        if (isExclusive) {
            styles.push('box-shadow: 0 0 0 2px var(--app-primary-color, #007AFF), 0 4px 12px rgba(0, 122, 255, 0.3)');
        }
    }
    
    // Accessibility attributes with exclusive filter indication
    const exclusiveText = isExclusive ? ' (exclusive)' : '';
    const ariaAttributes = [
        `aria-label="Filter ${config.label} issues (${count} found)${exclusiveText}"`,
        `aria-pressed="${isActive}"`,
        isDisabled ? 'aria-disabled="true"' : '',
        `title="${config.description}. ${count} issues found.${isExclusive ? ' Currently showing ONLY this type.' : ''}"`
    ].filter(attr => attr).join(' ');
    
    return `
        <div class="pf-v5-l-flex__item">
            <div class="${chipClass}" 
                 style="${styles.join('; ')}"
                 data-filter-level="${config.level}"
                 data-count="${count}"
                 ${ariaAttributes}
                 ${isDisabled ? '' : `onclick="toggleFilter('${config.level}')"`}
                 ${isDisabled ? '' : 'tabindex="0"'}
                 ${isDisabled ? '' : `onkeydown="handleFilterChipKeydown(event, '${config.level}')"`}>
                <span class="pf-v5-c-chip__content">
                    <i class="${config.icon} pf-v5-u-mr-xs" aria-hidden="true"></i>
                    <span class="filter-chip-label">${config.label}</span>
                    <span class="pf-v5-c-badge pf-m-read pf-v5-u-ml-xs" aria-label="${count} issues">
                        ${count}
                    </span>
                </span>
            </div>
        </div>
    `;
}

/**
 * Create reset button for filters
 * @returns {string} - HTML string for reset button
 */
function createResetButton() {
    return `
        <button class="pf-v5-c-button pf-m-link pf-m-small" 
                type="button" 
                onclick="resetFilters()"
                aria-label="Reset all filters to show all issues"
                title="Reset filters">
            <i class="fas fa-undo pf-v5-u-mr-xs" aria-hidden="true"></i>
            Reset
        </button>
    `;
}

/**
 * Create filter presets dropdown
 * @returns {string} - HTML string for filter presets
 */
function createFilterPresets() {
    const presets = [
        {
            key: 'focus-mode',
            name: 'Focus Mode',
            description: 'Critical and Error issues only',
            icon: 'fas fa-crosshairs'
        },
        {
            key: 'review-mode',
            name: 'Review Mode',
            description: 'All issues except suggestions',
            icon: 'fas fa-clipboard-check'
        },
        {
            key: 'complete-audit',
            name: 'Complete Audit',
            description: 'All issues including suggestions',
            icon: 'fas fa-search'
        }
    ];

    return `
        <div class="filter-presets" role="group" aria-label="Filter presets">
            <div class="pf-v5-l-flex pf-m-space-items-xs">
                <div class="pf-v5-l-flex__item">
                    <span class="pf-v5-c-content pf-v5-u-font-size-sm pf-v5-u-color-400">
                        <strong>Quick filters:</strong>
                    </span>
                </div>
                ${presets.map(preset => `
                    <div class="pf-v5-l-flex__item">
                        <button class="pf-v5-c-button pf-m-link pf-m-small" 
                                type="button"
                                onclick="applyFilterPreset('${preset.key}')"
                                aria-label="${preset.description}"
                                title="${preset.description}">
                            <i class="${preset.icon} pf-v5-u-mr-xs" aria-hidden="true"></i>
                            ${preset.name}
                        </button>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

/**
 * Handle keyboard navigation for filter chips
 * @param {KeyboardEvent} event - Keyboard event
 * @param {string} level - Filter level
 */
function handleFilterChipKeydown(event, level) {
    // Handle Enter and Space keys for accessibility
    if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        toggleFilter(level);
    }
    
    // Handle arrow key navigation between chips
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
        event.preventDefault();
        navigateFilterChips(event.target, event.key === 'ArrowRight');
    }
}

/**
 * Navigate between filter chips using arrow keys
 * @param {HTMLElement} currentChip - Currently focused chip
 * @param {boolean} forward - Direction of navigation
 */
function navigateFilterChips(currentChip, forward) {
    const allChips = Array.from(document.querySelectorAll('[data-filter-level][tabindex="0"]'));
    const currentIndex = allChips.indexOf(currentChip);
    
    if (currentIndex === -1) return;
    
    let nextIndex;
    if (forward) {
        nextIndex = (currentIndex + 1) % allChips.length;
    } else {
        nextIndex = (currentIndex - 1 + allChips.length) % allChips.length;
    }
    
    allChips[nextIndex].focus();
}

/**
 * Update filter chips display after state change
 * @param {Object} totalCounts - Updated error counts
 * @param {Set} activeFilters - Updated active filters
 */
function updateFilterChipsDisplay(totalCounts, activeFilters) {
    const container = document.querySelector('.smart-filter-container');
    if (!container) return;
    
    // Find all chip elements and update their state
    const chips = container.querySelectorAll('[data-filter-level]');
    chips.forEach(chip => {
        const level = chip.dataset.filterLevel;
        const count = totalCounts[level] || 0;
        const isActive = activeFilters.has(level);
        const isDisabled = count === 0;
        
        // Update visual state
        updateChipVisualState(chip, isActive, isDisabled, count);
        
        // Update accessibility attributes
        updateChipAccessibility(chip, isActive, isDisabled, count);
    });
}

/**
 * Update chip visual state
 * @param {HTMLElement} chip - Chip element
 * @param {boolean} isActive - Whether filter is active
 * @param {boolean} isDisabled - Whether chip is disabled
 * @param {number} count - Error count for this level
 * @private
 */
function updateChipVisualState(chip, isActive, isDisabled, count) {
    // Update chip classes
    const baseClasses = 'pf-v5-c-chip';
    if (isActive) {
        chip.className = `${baseClasses} ${chip.dataset.color || 'pf-m-blue'}`;
    } else {
        chip.className = `${baseClasses} pf-m-outline`;
    }
    
    // Update styles
    const styles = [];
    if (isDisabled) {
        styles.push('opacity: 0.4');
        styles.push('cursor: not-allowed');
    } else {
        styles.push('cursor: pointer');
        styles.push('transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1)');
    }
    chip.style.cssText = styles.join('; ');
    
    // Update count badge
    const badge = chip.querySelector('.pf-v5-c-badge');
    if (badge) {
        badge.textContent = count.toString();
    }
}

/**
 * Update chip accessibility attributes
 * @param {HTMLElement} chip - Chip element
 * @param {boolean} isActive - Whether filter is active
 * @param {boolean} isDisabled - Whether chip is disabled
 * @param {number} count - Error count for this level
 * @private
 */
function updateChipAccessibility(chip, isActive, isDisabled, count) {
    const level = chip.dataset.filterLevel;
    const levelCapitalized = level.charAt(0).toUpperCase() + level.slice(1);
    
    // Update ARIA attributes
    chip.setAttribute('aria-pressed', isActive.toString());
    chip.setAttribute('aria-label', `Filter ${levelCapitalized} issues (${count} found)`);
    
    if (isDisabled) {
        chip.setAttribute('aria-disabled', 'true');
        chip.removeAttribute('tabindex');
        chip.onclick = null;
        chip.onkeydown = null;
    } else {
        chip.removeAttribute('aria-disabled');
        chip.setAttribute('tabindex', '0');
        chip.onclick = () => toggleFilter(level);
        chip.onkeydown = (event) => handleFilterChipKeydown(event, level);
    }
    
    // Update title for enhanced tooltip
    const descriptions = {
        critical: 'Critical issues requiring immediate attention',
        error: 'Errors that should be addressed',
        warning: 'Warnings that may need attention',
        suggestion: 'Suggestions for improvement'
    };
    chip.setAttribute('title', `${descriptions[level] || 'Filter issues'}. ${count} issues found.`);
}

/**
 * Create enhanced filter statistics display
 * @param {number} totalErrors - Total number of errors
 * @param {number} filteredErrors - Number of filtered errors
 * @param {Set} activeFilters - Currently active filters
 * @returns {string} - HTML string for filter statistics
 */
function createFilterStatistics(totalErrors, filteredErrors, activeFilters) {
    if (totalErrors === 0) return '';
    
    const hiddenCount = totalErrors - filteredErrors;
    const filterCount = activeFilters.size;
    const isAllActive = filterCount === 4;
    
    let statusClass = 'pf-m-info';
    let statusIcon = 'fas fa-filter';
    let statusText = '';
    
    if (isAllActive) {
        statusClass = 'pf-m-success';
        statusIcon = 'fas fa-eye';
        statusText = `Showing all ${totalErrors} issues`;
    } else if (hiddenCount === 0) {
        statusClass = 'pf-m-info';
        statusIcon = 'fas fa-filter';
        statusText = `Showing all ${filteredErrors} matching issues`;
    } else {
        statusClass = 'pf-m-warning';
        statusIcon = 'fas fa-eye-slash';
        statusText = `Showing ${filteredErrors} of ${totalErrors} issues (${hiddenCount} hidden)`;
    }
    
    return `
        <div class="filter-statistics pf-v5-u-mt-sm">
            <div class="pf-v5-c-alert pf-m-inline ${statusClass}" role="status">
                <div class="pf-v5-c-alert__icon">
                    <i class="${statusIcon}" aria-hidden="true"></i>
                </div>
                <div class="pf-v5-c-alert__title">
                    ${statusText}
                </div>
            </div>
        </div>
    `;
}

/**
 * Generate CSS styles for smart filter chips
 * Follows existing design patterns and app color scheme
 * @returns {string} - CSS styles for filter chips
 */
function generateSmartFilterStyles() {
    return `
        /* Smart Filter Chips Styles - Integrated with existing design */
        .smart-filter-container {
            background: var(--app-neutral-50, #F9FAFB);
            border: 1px solid var(--app-neutral-200, #E5E7EB);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        
        .smart-filter-container .pf-v5-c-chip {
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
            border-radius: 8px;
            font-weight: 500;
        }
        
        .smart-filter-container .pf-v5-c-chip:not([aria-disabled="true"]):hover {
            transform: translateY(-1px);
            box-shadow: var(--app-shadow-sm, 0 1px 2px 0 rgba(0, 0, 0, 0.05));
        }
        
        .smart-filter-container .pf-v5-c-chip:focus {
            outline: 2px solid var(--app-primary-color, #007AFF);
            outline-offset: 2px;
        }
        
        .smart-filter-container .pf-v5-c-chip[aria-pressed="true"] {
            box-shadow: var(--app-shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
        }
        
        .filter-chip-label {
            font-weight: 600;
        }
        
        .filter-presets .pf-v5-c-button.pf-m-link:hover {
            background-color: var(--app-neutral-100, #F3F4F6);
            border-radius: 6px;
        }
        
        .filter-statistics .pf-v5-c-alert {
            font-size: 0.875rem;
        }
        
        /* Exclusive filter styling - shows when only one filter is selected */
        .smart-filter-container .pf-v5-c-chip.exclusive-filter {
            font-weight: 700;
            box-shadow: 0 0 0 2px var(--app-primary-color, #007AFF), 0 4px 12px rgba(0, 122, 255, 0.3) !important;
        }
        
        .smart-filter-container .pf-v5-c-chip.exclusive-filter:hover {
            box-shadow: 0 0 0 3px var(--app-primary-color, #007AFF), 0 6px 16px rgba(0, 122, 255, 0.4) !important;
        }
        
        /* Responsive design for smaller screens */
        @media (max-width: 768px) {
            .smart-filter-container .pf-v5-l-flex {
                flex-wrap: wrap;
                gap: 0.5rem;
            }
            
            .filter-presets {
                width: 100%;
                margin-top: 0.5rem;
            }
        }
        
        /* High contrast mode support */
        @media (prefers-contrast: high) {
            .smart-filter-container .pf-v5-c-chip {
                border-width: 2px;
            }
        }
        
        /* Reduced motion support */
        @media (prefers-reduced-motion: reduce) {
            .smart-filter-container .pf-v5-c-chip {
                transition: none;
            }
        }
    `;
}

// Initialize filter chips styles when module loads
if (typeof document !== 'undefined') {
    // Inject styles following existing pattern
    const styleId = 'smart-filter-chips-styles';
    if (!document.getElementById(styleId)) {
        const style = document.createElement('style');
        style.id = styleId;
        style.textContent = generateSmartFilterStyles();
        document.head.appendChild(style);
    }
}

// Export functions for global access following existing pattern
if (typeof window !== 'undefined') {
    window.SmartFilterChips = {
        createSmartFilterChips,
        createFilterChip,
        createResetButton,
        createFilterPresets,
        updateFilterChipsDisplay,
        createFilterStatistics,
        handleFilterChipKeydown,
        navigateFilterChips,
        generateSmartFilterStyles
    };
    
    console.log('✅ SmartFilterChips module loaded successfully');
}
