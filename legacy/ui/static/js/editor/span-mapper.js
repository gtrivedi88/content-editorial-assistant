/**
 * Span Mapper — converts backend character offsets to DOM Range objects.
 *
 * The key challenge: `innerText` (sent to the backend) includes \n at block
 * boundaries (<p>, <h1>, <li>, <br>), but TreeWalker text nodes don't include
 * those newlines. This causes offset drift when content has multiple blocks.
 *
 * Solution: we build a mapping that accounts for block boundaries, matching
 * exactly how `innerText` serializes the DOM.
 */

// Block-level elements that produce a newline in innerText
const BLOCK_TAGS = new Set([
    'P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'LI', 'TR', 'BLOCKQUOTE', 'PRE', 'HR', 'UL', 'OL',
    'TABLE', 'THEAD', 'TBODY', 'DT', 'DD', 'FIGCAPTION',
]);

/**
 * Build a flat array of { node, offset, length } entries that maps
 * innerText character positions to DOM text nodes, accounting for
 * newlines inserted by block boundaries.
 */
function buildTextMap(editorEl) {
    const entries = [];
    let pos = 0;

    function walk(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            const len = node.textContent.length;
            if (len > 0) {
                entries.push({ node, pos, length: len });
                pos += len;
            }
            return;
        }

        if (node.nodeType !== Node.ELEMENT_NODE) return;

        const tag = node.tagName;

        // BR produces a newline
        if (tag === 'BR') {
            pos += 1;
            return;
        }

        // Block elements: add newline before (if not the first thing)
        const isBlock = BLOCK_TAGS.has(tag);
        if (isBlock && pos > 0 && entries.length > 0) {
            pos += 1; // newline before block
        }

        for (const child of node.childNodes) {
            walk(child);
        }

        // Some block elements add a trailing newline for double-spacing in innerText
        // (e.g., <p> produces \n\n between paragraphs, but the second \n is from the next block)
    }

    walk(editorEl);
    return entries;
}

/**
 * Convert a [startChar, endChar] span (relative to innerText) to a DOM Range.
 *
 * @param {HTMLElement} editorEl - The contenteditable element
 * @param {number} startChar - Start character offset (inclusive)
 * @param {number} endChar - End character offset (exclusive)
 * @returns {Range|null}
 */
export function charSpanToDomRange(editorEl, startChar, endChar) {
    const map = buildTextMap(editorEl);

    let startNode = null, startOffset = 0;
    let endNode = null, endOffset = 0;

    for (const entry of map) {
        const entryEnd = entry.pos + entry.length;

        if (!startNode && entryEnd > startChar) {
            startNode = entry.node;
            startOffset = startChar - entry.pos;
        }

        if (!endNode && entryEnd >= endChar) {
            endNode = entry.node;
            endOffset = endChar - entry.pos;
            break;
        }
    }

    if (startNode && endNode) {
        try {
            const range = document.createRange();
            range.setStart(startNode, Math.min(startOffset, startNode.textContent.length));
            range.setEnd(endNode, Math.min(endOffset, endNode.textContent.length));
            return range;
        } catch (e) {
            console.warn('[SpanMapper] Range creation failed, falling back to text search:', e);
        }
    }

    // Fallback: couldn't map by offset. Should not normally happen.
    return null;
}

/**
 * Fallback: find text directly in DOM text nodes (bypasses innerText offsets entirely).
 * Walks all text nodes and searches for the flagged string within them.
 *
 * @param {HTMLElement} editorEl
 * @param {string} flaggedText - The exact text to find
 * @param {number} hintStart - Approximate character position (for disambiguation)
 * @returns {Range|null}
 */
export function findTextInDom(editorEl, flaggedText, hintStart) {
    if (!flaggedText) return null;

    // Walk all text nodes and search for the flagged text within each
    const walker = document.createTreeWalker(editorEl, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) {
        textNodes.push(walker.currentNode);
    }

    // First try: find the text within a single text node
    for (const node of textNodes) {
        const idx = node.textContent.indexOf(flaggedText);
        if (idx >= 0) {
            try {
                const range = document.createRange();
                range.setStart(node, idx);
                range.setEnd(node, idx + flaggedText.length);
                return range;
            } catch (e) {
                // Continue searching
            }
        }
    }

    // Second try: the flagged text might span adjacent text nodes
    // (e.g., across a <mark> boundary from a previous underline)
    // Concatenate adjacent text node content and search
    for (let i = 0; i < textNodes.length - 1; i++) {
        const combined = textNodes[i].textContent + textNodes[i + 1].textContent;
        const idx = combined.indexOf(flaggedText);
        if (idx >= 0 && idx < textNodes[i].textContent.length) {
            try {
                const range = document.createRange();
                range.setStart(textNodes[i], idx);
                const overlapLen = flaggedText.length - (textNodes[i].textContent.length - idx);
                range.setEnd(textNodes[i + 1], Math.min(overlapLen, textNodes[i + 1].textContent.length));
                return range;
            } catch (e) {
                // Continue searching
            }
        }
    }

    return null;
}

/**
 * Get the plain text content of the editor (matching what the backend receives).
 */
export function getPlainText(editorEl) {
    return editorEl.innerText || editorEl.textContent || '';
}
