
// Test script to verify escapeHtml function
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    
    // First decode any existing HTML entities, especially smart quotes
    text = decodeHtmlEntities(text);
    
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Decode common HTML entities, especially smart quotes that cause display issues
function decodeHtmlEntities(text) {
    if (typeof text !== 'string') return text;
    
    // Create a temporary element to decode HTML entities
    const tempElement = document.createElement('div');
    tempElement.innerHTML = text;
    let decoded = tempElement.textContent || tempElement.innerText || '';
    
    // Fallback manual decoding for common problematic entities
    const entityMap = {
        '&#8217;': "'",  // Right single quotation mark (curly apostrophe)
        '&#8216;': "'",  // Left single quotation mark
        '&#8220;': '"',  // Left double quotation mark
        '&#8221;': '"',  // Right double quotation mark
        '&#8211;': '–',  // En dash
        '&#8212;': '—',  // Em dash
        '&#8230;': '…',  // Horizontal ellipsis
        '&rsquo;': "'",  // Right single quotation mark
        '&lsquo;': "'",  // Left single quotation mark
        '&rdquo;': '"',  // Right double quotation mark
        '&ldquo;': '"',  // Left double quotation mark
        '&ndash;': '–',  // En dash
        '&mdash;': '—',  // Em dash
        '&hellip;': '…' // Horizontal ellipsis
    };
    
    // Apply manual decoding as fallback
    Object.keys(entityMap).forEach(entity => {
        const char = entityMap[entity];
        decoded = decoded.replace(new RegExp(entity, 'g'), char);
    });
    
    return decoded;
}

// Test the function
const testText = "It's designed to work";
console.log('Original:', testText);
console.log('Escaped:', escapeHtml(testText));
