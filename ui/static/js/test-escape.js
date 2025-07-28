
// Test script to verify escapeHtml function
function escapeHtml(text) {
    if (typeof text !== 'string') return text;
    
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// Test the function
const testText = "It's designed to work";
console.log('Original:', testText);
console.log('Escaped:', escapeHtml(testText));
