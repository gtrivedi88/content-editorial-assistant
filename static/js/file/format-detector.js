/**
 * Format Detector — detects AsciiDoc, Markdown, DITA from content or filename.
 */

const FORMAT_MAP = {
    '.md': 'markdown',
    '.adoc': 'asciidoc',
    '.dita': 'dita',
    '.xml': 'dita',
    '.txt': 'plaintext',
    '.pdf': 'auto',
    '.docx': 'auto',
};

/**
 * Detect format from filename extension.
 */
export function detectFormatFromFilename(filename) {
    if (!filename) return 'auto';
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return FORMAT_MAP[ext] || 'auto';
}

// AsciiDoc markers (require 2+ matches for detection)
const ASCIIDOC_PATTERNS = [
    /^=+ .+/m,                     // = Heading, == Heading
    /^====+\s*$/m,                 // ==== (delimiter)
    /^----+\s*$/m,                 // ---- (listing delimiter)
    /^\[(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$/m,  // [NOTE]
    /^:[\w-]+:\s/m,                // :attribute: value
    /^\.\w+/m,                     // .Title
    /\bxref:[^\s]+\[/,             // xref:page.adoc[text]
    /\binclude::/,                 // include::file[]
    /\bimage::/,                   // image::file[]
    /\{[\w-]+\}/,                  // {attribute}
    /^\*+ /m,                      // * list item, ** nested
    /^\.\. /m,                     // .. ordered list continuation
];

// Markdown markers (require 2+ matches for detection)
const MARKDOWN_PATTERNS = [
    /^#{1,6} .+/m,                 // # Heading
    /^```[\w]*\s*$/m,              // ``` code fence
    /^- .+/m,                      // - list item
    /^\d+\. .+/m,                  // 1. ordered list
    /\[.+\]\(.+\)/,                // [text](url)
    /^>\s+.+/m,                    // > blockquote
    /\*\*.+\*\*/,                  // **bold**
    /^---+\s*$/m,                  // --- horizontal rule
    /!\[.+\]\(.+\)/,              // ![alt](img)
];

// DITA markers (require 1+ match — very distinctive)
const DITA_PATTERNS = [
    /<!DOCTYPE\s+(?:concept|task|reference|topic)/i,
    /<(?:concept|task|reference|topic)\b/i,
    /<conbody|<taskbody|<refbody/i,
    /<\/(?:concept|task|reference|topic)>/i,
];

/**
 * Auto-detect markup format from pasted content.
 * Returns { format, confidence, markers } or null if plain text.
 *
 * Requires 2+ pattern matches for AsciiDoc/Markdown (avoids false positives).
 * Requires 1+ for DITA (very distinctive tags).
 */
export function detectFormatFromContent(text) {
    if (!text || text.length < 20) return null;

    // Check DITA first (most distinctive)
    const ditaMatches = DITA_PATTERNS.filter(p => p.test(text));
    if (ditaMatches.length >= 1) {
        return { format: 'dita', confidence: 'high', markers: ditaMatches.length };
    }

    // Check AsciiDoc
    const adocMatches = ASCIIDOC_PATTERNS.filter(p => p.test(text));
    if (adocMatches.length >= 2) {
        return {
            format: 'asciidoc',
            confidence: adocMatches.length >= 4 ? 'high' : 'medium',
            markers: adocMatches.length,
        };
    }

    // Check Markdown
    const mdMatches = MARKDOWN_PATTERNS.filter(p => p.test(text));
    if (mdMatches.length >= 2) {
        return {
            format: 'markdown',
            confidence: mdMatches.length >= 4 ? 'high' : 'medium',
            markers: mdMatches.length,
        };
    }

    return null; // Plain text
}
