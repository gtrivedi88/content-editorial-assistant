/**
 * Error Display Module - Error Cards and Inline Error Display
 * Handles all error-related UI components and styling
 */

// Create inline error display with premium design
function createInlineError(error) {
    const errorTypes = {
        'STYLE': { color: '#dc2626', bg: '#fef2f2', icon: 'fas fa-exclamation-circle' },
        'GRAMMAR': { color: '#b45309', bg: '#fefbeb', icon: 'fas fa-spell-check' },
        'STRUCTURE': { color: '#1e40af', bg: '#eff6ff', icon: 'fas fa-sitemap' },
        'PUNCTUATION': { color: '#6b21a8', bg: '#faf5ff', icon: 'fas fa-quote-right' },
        'CAPITALIZATION': { color: '#059669', bg: '#ecfdf5', icon: 'fas fa-font' },
        'TERMINOLOGY': { color: '#c2410c', bg: '#fff7ed', icon: 'fas fa-book' },
        'PASSIVE_VOICE': { color: '#b45309', bg: '#fefbeb', icon: 'fas fa-exchange-alt' },
        'READABILITY': { color: '#0e7490', bg: '#ecfeff', icon: 'fas fa-eye' },
        'ADMONITIONS': { color: '#1e40af', bg: '#eff6ff', icon: 'fas fa-info-circle' },
        'HEADINGS': { color: '#7c2d12', bg: '#fef7ed', icon: 'fas fa-heading' },
        'LISTS': { color: '#059669', bg: '#ecfdf5', icon: 'fas fa-list' },
        'PROCEDURES': { color: '#0e7490', bg: '#ecfeff', icon: 'fas fa-tasks' }
    };
    
    const errorType = error.error_type || 'STYLE';
    const typeStyle = errorTypes[errorType] || errorTypes['STYLE'];
    
    return `
        <div class="error-item mb-3" style="
            background: white;
            border: 1px solid ${typeStyle.bg};
            border-left: 4px solid ${typeStyle.color};
            border-radius: 12px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
            transition: all 0.2s ease;
        " onmouseover="this.style.transform='translateY(-1px)'; this.style.boxShadow='0 4px 16px rgba(0, 0, 0, 0.08)'" 
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 2px 8px rgba(0, 0, 0, 0.04)'">
            <div class="d-flex align-items-start">
                <div class="me-3 d-flex align-items-center justify-content-center" style="
                    width: 36px;
                    height: 36px;
                    background: ${typeStyle.bg};
                    border-radius: 10px;
                    flex-shrink: 0;
                ">
                    <i class="${typeStyle.icon}" style="color: ${typeStyle.color}; font-size: 16px;"></i>
                </div>
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center mb-2">
                        <span class="badge me-2" style="
                            background: ${typeStyle.color};
                            color: white;
                            padding: 4px 10px;
                            border-radius: 6px;
                            font-size: 10px;
                            font-weight: 600;
                            letter-spacing: 0.5px;
                        ">${errorType}</span>
                        <div class="fw-semibold" style="color: #374151; font-size: 14px;">
                            ${error.message || 'Style issue detected'}
                        </div>
                    </div>
                    ${error.suggestion ? `
                    <div class="d-flex align-items-start" style="
                        background: ${typeStyle.bg};
                        border-radius: 8px;
                        padding: 12px;
                        margin-top: 8px;
                    ">
                        <i class="fas fa-lightbulb me-2" style="
                            color: ${typeStyle.color};
                            margin-top: 2px;
                            font-size: 14px;
                        "></i>
                        <div style="color: #4b5563; font-size: 13px; line-height: 1.5;">
                            <strong style="color: ${typeStyle.color};">Suggestion:</strong> ${error.suggestion}
                        </div>
                    </div>
                    ` : ''}
                </div>
            </div>
        </div>
    `;
}

// Note: createErrorCard function is already defined in utility-functions.js
// This module focuses on the more complex inline error display used within blocks 