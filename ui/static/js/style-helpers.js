/**
 * Style Helpers Module - Utilities, Colors, and Styling Functions
 * Contains utility functions, color schemes, and insight generators
 */

// HTML escape utility
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Safe HTML renderer for table cells - allows common formatting tags
function renderSafeTableCellHtml(text) {
    if (!text) return '';
    
    // First escape all HTML to be safe
    let escaped = escapeHtml(text);
    
    // Then selectively un-escape safe formatting tags
    const safeTagsMap = {
        '&lt;code&gt;': '<code style="background: rgba(14, 184, 166, 0.1); color: #0d9488; padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 13px;">',
        '&lt;/code&gt;': '</code>',
        '&lt;strong&gt;': '<strong>',
        '&lt;/strong&gt;': '</strong>',
        '&lt;em&gt;': '<em>',
        '&lt;/em&gt;': '</em>',
        '&lt;b&gt;': '<strong>',
        '&lt;/b&gt;': '</strong>',
        '&lt;i&gt;': '<em>',
        '&lt;/i&gt;': '</em>'
    };
    
    // Replace escaped safe tags with their HTML equivalents
    Object.keys(safeTagsMap).forEach(escapedTag => {
        const htmlTag = safeTagsMap[escapedTag];
        escaped = escaped.replace(new RegExp(escapedTag, 'gi'), htmlTag);
    });
    
    return escaped;
}

// Get a human-readable display name for a block type
function getBlockTypeDisplayName(blockType, context) {
    const level = context.level !== undefined ? context.level : 0;
    const admonitionType = context.admonition_type;
    
    const displayNames = {
        'heading': `HEADING (Level ${level})`,
        'paragraph': 'PARAGRAPH',
        'ordered_list': 'ORDERED LIST',
        'unordered_list': 'UNORDERED LIST',
        'list_item': 'LIST ITEM',
        'list_title': 'LIST TITLE',
        'admonition': `ADMONITION (${admonitionType ? admonitionType.toUpperCase() : 'NOTE'})`,
        'sidebar': 'SIDEBAR',
        'example': 'EXAMPLE',
        'quote': 'QUOTE',
        'verse': 'VERSE',
        'listing': 'CODE BLOCK',
        'literal': 'LITERAL BLOCK',
        'section': 'SECTION',
        'attribute_entry': 'ATTRIBUTE',
        'comment': 'COMMENT',
        'table': 'TABLE',
        'image': 'IMAGE',
        'audio': 'AUDIO',
        'video': 'VIDEO'
    };
    
    return displayNames[blockType] || blockType.toUpperCase().replace(/_/g, ' ');
}

// Color and style helper functions for statistics
function getFleschColor(score) {
    if (score >= 70) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score >= 50) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getFogColor(score) {
    if (score <= 12) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score <= 16) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getGradeColor(score) {
    if (score <= 12) return 'linear-gradient(135deg, #10b981, #059669)';
    if (score <= 16) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernPassiveVoiceGradient(percentage) {
    if (percentage <= 15) return 'linear-gradient(135deg, #10b981, #059669)';
    if (percentage <= 25) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernSentenceLengthGradient(length) {
    if (length >= 15 && length <= 20) return 'linear-gradient(135deg, #10b981, #059669)';
    if (length <= 25) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

function getModernComplexWordsGradient(percentage) {
    if (percentage <= 20) return 'linear-gradient(135deg, #10b981, #059669)';
    if (percentage <= 30) return 'linear-gradient(135deg, #f59e0b, #d97706)';
    return 'linear-gradient(135deg, #ef4444, #dc2626)';
}

// Insight generation functions
function getGradeLevelInsight(gradeLevel, meetsTarget) {
    if (!gradeLevel) return 'Grade level could not be determined.';
    
    if (meetsTarget) {
        return 'Perfect! Your content is accessible to your target technical audience.';
    } else if (gradeLevel < 9) {
        return 'Content may be too simple for technical documentation.';
    } else {
        return 'Consider simplifying complex sentences for better accessibility.';
    }
}

function getPassiveVoiceInsight(percentage) {
    if (percentage <= 15) return 'Excellent active voice usage!';
    if (percentage <= 25) return 'Consider reducing passive voice usage.';
    return 'Too much passive voice. Rewrite for active voice.';
}

function getSentenceLengthInsight(length) {
    if (length >= 15 && length <= 20) return 'Perfect sentence length for technical writing!';
    if (length < 15) return 'Sentences might be too short. Consider combining some.';
    return 'Sentences are too long. Break them down for clarity.';
}

function getComplexWordsInsight(percentage) {
    if (percentage <= 20) return 'Good balance of complex and simple words.';
    if (percentage <= 30) return 'Consider simplifying some complex terms.';
    return 'Too many complex words may hurt readability.';
} 