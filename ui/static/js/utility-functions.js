// Enhanced Utility functions for PatternFly UI

// Format rule type for display - handles special cases like word usage rules
function formatRuleType(ruleType) {
    if (!ruleType) return 'Style Issue';
    
    // Group all word usage rules under "Word Usage"
    if (ruleType.startsWith('word_usage_')) {
        return 'Word Usage';
    }
    
    // Group all numbers rules under better names
    if (ruleType.startsWith('numbers_')) {
        const numberTypeMap = {
            'numbers_currency': 'Currency',
            'numbers_dates_times': 'Dates and Times', 
            'numbers_general': 'Numbers',
            'numbers_numerals_vs_words': 'Numbers vs Words',
            'numbers_units_of_measurement': 'Units of Measurement'
        };
        return numberTypeMap[ruleType] || 'Numbers';
    }
    
    // Group all references rules under better names
    if (ruleType.startsWith('references_')) {
        const referenceTypeMap = {
            'references_citations': 'Citations',
            'references_geographic_locations': 'Geographic Locations',
            'references_names_titles': 'Names and Titles',
            'references_product_names': 'Product Names',
            'references_product_versions': 'Product Versions'
        };
        return referenceTypeMap[ruleType] || 'References';
    }
    
    // Group all technical elements under better names
    if (ruleType.startsWith('technical_')) {
        const technicalTypeMap = {
            'technical_commands': 'Commands',
            'technical_files_directories': 'Files and Directories',
            'technical_keyboard_keys': 'Keyboard Keys',
            'technical_mouse_buttons': 'Mouse Buttons',
            'technical_programming_elements': 'Programming Elements',
            'technical_ui_elements': 'UI Elements',
            'technical_web_addresses': 'Web Addresses'
        };
        return technicalTypeMap[ruleType] || 'Technical Elements';
    }
    
    // Group all legal rules under better names
    if (ruleType.startsWith('legal_')) {
        const legalTypeMap = {
            'legal_claims': 'Claims',
            'legal_company_names': 'Company Names',
            'legal_personal_information': 'Personal Information'
        };
        return legalTypeMap[ruleType] || 'Legal Information';
    }
    
    // Group all audience rules under better names
    if (ruleType.startsWith('audience_')) {
        const audienceTypeMap = {
            'audience_tone': 'Tone',
            'audience_global': 'Global Audience',
            'audience_conversational': 'Conversational Style',
            'audience_llm_consumability': 'LLM Consumability'
        };
        return audienceTypeMap[ruleType] || 'Audience and Medium';
    }
    
    // Group all structure format rules under better names
    if (ruleType.startsWith('structure_format_')) {
        const structureTypeMap = {
            'structure_format_highlighting': 'Highlighting',
            'structure_format_glossaries': 'Glossaries'
        };
        return structureTypeMap[ruleType] || 'Structure and Format';
    }
    
    // Handle other specific cases
    const specificTypeMap = {
        'second_person': 'Second Person',
        'sentence_length': 'Sentence Length',
        'anthropomorphism': 'Anthropomorphism',
        'abbreviations': 'Abbreviations',
        'adverbs_only': 'Adverbs',
        'quotation_marks': 'Quotation Marks',
        'punctuation_and_symbols': 'Punctuation and Symbols',
        'exclamation_points': 'Exclamation Points'
    };
    
    if (specificTypeMap[ruleType]) {
        return specificTypeMap[ruleType];
    }
    
    // Default: replace underscores with spaces and title case
    return ruleType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}

// Show loading state using PatternFly EmptyState and Spinner
function showLoading(elementId, message = 'Processing...') {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-c-empty-state pf-m-lg">
                    <div class="pf-v5-c-empty-state__content">
                        <div class="pf-v5-c-empty-state__icon">
                            <span class="pf-v5-c-spinner pf-m-xl" role="status" aria-label="Loading...">
                                <span class="pf-v5-c-spinner__clipper"></span>
                                <span class="pf-v5-c-spinner__lead-ball"></span>
                                <span class="pf-v5-c-spinner__tail-ball"></span>
                            </span>
                        </div>
                        <h2 class="pf-v5-c-title pf-m-xl">Analyzing Your Content</h2>
                        <div class="pf-v5-c-empty-state__body">
                            <p class="pf-v5-u-mb-lg">${message}</p>
                            
                            <div class="pf-v5-l-grid pf-m-gutter">
                                <div class="pf-v5-l-grid__item pf-m-6-col">
                                    <div class="pf-v5-c-card pf-m-plain">
                                        <div class="pf-v5-c-card__body">
                                            <h3 class="pf-v5-c-title pf-m-md pf-v5-u-mb-sm">
                                                <i class="fas fa-search pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                                Analysis Features
                                            </h3>
                                            <ul class="pf-v5-c-list">
                                                <li class="pf-v5-c-list__item">Sentence length and complexity</li>
                                                <li class="pf-v5-c-list__item">Passive voice detection</li>
                                                <li class="pf-v5-c-list__item">Wordy phrases and redundancy</li>
                                                <li class="pf-v5-c-list__item">Readability scores</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                                <div class="pf-v5-l-grid__item pf-m-6-col">
                                    <div class="pf-v5-c-card pf-m-plain">
                                        <div class="pf-v5-c-card__body">
                                            <h3 class="pf-v5-c-title pf-m-md pf-v5-u-mb-sm">
                                                <i class="fas fa-chart-line pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                                                Metrics Calculated
                                            </h3>
                                            <ul class="pf-v5-c-list">
                                                <li class="pf-v5-c-list__item">Grade level assessment</li>
                                                <li class="pf-v5-c-list__item">Technical writing quality</li>
                                                <li class="pf-v5-c-list__item">Word complexity analysis</li>
                                                <li class="pf-v5-c-list__item">Improvement recommendations</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Show error message using enhanced PatternFly Alert
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="pf-v5-c-alert pf-m-danger pf-m-inline fade-in" role="alert">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h4 class="pf-v5-c-alert__title">Analysis Error</h4>
            <div class="pf-v5-c-alert__description">
                <p>${message}</p>
                <div class="pf-v5-u-mt-sm">
                    <button class="pf-v5-c-button pf-m-link pf-m-inline" type="button" onclick="location.reload()">
                        <i class="fas fa-redo pf-v5-u-mr-xs"></i>
                        Try Again
                    </button>
                </div>
            </div>
            <div class="pf-v5-c-alert__action">
                <button class="pf-v5-c-button pf-m-plain" type="button" onclick="this.closest('.pf-v5-c-alert').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
}

// Show success message using enhanced PatternFly Alert
function showSuccess(elementId, message) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.innerHTML = `
        <div class="pf-v5-c-alert pf-m-success pf-m-inline fade-in" role="alert">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-check-circle"></i>
            </div>
            <h4 class="pf-v5-c-alert__title">${message}</h4>
            <div class="pf-v5-c-alert__action">
                <button class="pf-v5-c-button pf-m-plain" type="button" onclick="this.closest('.pf-v5-c-alert').remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>
    `;
}

// Basic highlight errors function (enhanced version is in error-display.js)
function highlightErrors(text, errors) {
    if (!errors || errors.length === 0) return escapeHtml(text);
    
    let highlightedText = escapeHtml(text);
    
    // Simple highlighting - just mark error text
    errors.forEach(error => {
        if (error.text_segment) {
            const segment = escapeHtml(error.text_segment);
            const highlightedSegment = `<mark style="background-color: rgba(201, 25, 11, 0.1); border-bottom: 2px solid var(--app-danger-color);">${segment}</mark>`;
            highlightedText = highlightedText.replace(segment, highlightedSegment);
        }
    });
    
    return highlightedText;
}

// Basic error card function (enhanced version is in error-display.js)
function createErrorCard(error, index = 0) {
    const errorType = error.error_type || 'STYLE';
    const message = error.message || 'Style issue detected';
    
    return `
        <div class="pf-v5-c-alert pf-m-warning pf-m-inline pf-v5-u-mb-sm">
            <div class="pf-v5-c-alert__icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <div class="pf-v5-c-alert__title">${formatRuleType(errorType)}</div>
            <div class="pf-v5-c-alert__description">${message}</div>
        </div>
    `;
}
