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

/**
 * Normalize whitespace identically to the backend preprocessor.
 * Used as a fallback in text search when flaggedText newlines don't
 * match the DOM (e.g. backend sent \n but DOM still has \r\n).
 */
function _normalize(text) {
    return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\t/g, ' ');
}

/**
 * Count codepoints instead of UTF-16 code units (SK-14).
 * Python len("🚀") == 1 but JS "🚀".length == 2.
 * Backend sends codepoint-based offsets, so the text map must count
 * codepoints to keep alignment.
 *
 * @param {string} str
 * @returns {number} codepoint count
 */
function _codepointLength(str) {
    return [...str].length;
}

// Block-level elements that produce a newline in innerText
const BLOCK_TAGS = new Set([
    'P', 'DIV', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
    'LI', 'TR', 'BLOCKQUOTE', 'PRE', 'HR', 'UL', 'OL',
    'TABLE', 'THEAD', 'TBODY', 'DT', 'DD', 'FIGCAPTION',
]);

/**
 * Build a flat array of { node, offset, length, utf16Length } entries
 * that maps innerText character positions (codepoints) to DOM text
 * nodes, accounting for block boundaries.
 */
function buildTextMap(editorEl) {
    const entries = [];
    let pos = 0;

    function walk(node) {
        if (node.nodeType === Node.TEXT_NODE) {
            const cpLen = _codepointLength(node.textContent);
            const utf16Len = node.textContent.length;
            if (cpLen > 0) {
                entries.push({ node, pos, length: cpLen, utf16Length: utf16Len });
                pos += cpLen;
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
    }

    walk(editorEl);
    console.log('[SpanMapper] buildTextMap: %d entries, totalPos=%d, childNodes=%d, textContent.len=%d, innerText.len=%d',
        entries.length, pos, editorEl.childNodes.length,
        (editorEl.textContent || '').length,
        (editorEl.innerText || '').length);
    if (entries.length <= 5) {
        entries.forEach((e, i) => console.log('[SpanMapper]   entry[%d]: pos=%d len=%d text=%s', i, e.pos, e.length, JSON.stringify(e.node.textContent.substring(0, 80))));
    } else {
        console.log('[SpanMapper]   entry[0]: pos=%d len=%d', entries[0].pos, entries[0].length);
        console.log('[SpanMapper]   entry[last]: pos=%d len=%d', entries[entries.length - 1].pos, entries[entries.length - 1].length);
    }
    return entries;
}

/**
 * Convert a codepoint offset within a text node to a UTF-16 offset
 * suitable for Range.setStart/setEnd.
 *
 * @param {string} text - the text node's textContent
 * @param {number} cpOffset - codepoint offset within the node
 * @returns {number} UTF-16 offset
 */
function _codepointToUtf16Offset(text, cpOffset) {
    const codepoints = [...text];
    const clamped = Math.min(cpOffset, codepoints.length);
    let utf16 = 0;
    for (let i = 0; i < clamped; i++) {
        utf16 += codepoints[i].length; // surrogate pairs have .length === 2
    }
    return utf16;
}

/**
 * Convert a [startChar, endChar] span (codepoint offsets relative to
 * innerText) to a DOM Range.
 *
 * @param {HTMLElement} editorEl - The contenteditable element
 * @param {number} startChar - Start codepoint offset (inclusive)
 * @param {number} endChar - End codepoint offset (exclusive)
 * @returns {Range|null}
 */
export function charSpanToDomRange(editorEl, startChar, endChar) {
    console.log('[SpanMapper] charSpanToDomRange called: startChar=%d, endChar=%d', startChar, endChar);
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

    console.log('[SpanMapper] charSpanToDomRange result: startNode=%s, startOffset=%d, endNode=%s, endOffset=%d',
        startNode ? 'FOUND' : 'NULL', startOffset, endNode ? 'FOUND' : 'NULL', endOffset);

    if (startNode && endNode) {
        try {
            const range = document.createRange();
            // Convert codepoint offsets to UTF-16 for DOM API (SK-14)
            const startUtf16 = _codepointToUtf16Offset(startNode.textContent, startOffset);
            const endUtf16 = _codepointToUtf16Offset(endNode.textContent, endOffset);
            range.setStart(startNode, Math.min(startUtf16, startNode.textContent.length));
            range.setEnd(endNode, Math.min(endUtf16, endNode.textContent.length));
            console.log('[SpanMapper] Range created, text=%s', JSON.stringify(range.toString().substring(0, 80)));
            return range;
        } catch (e) {
            console.warn('[SpanMapper] Range creation failed, falling back to text search:', e);
        }
    }

    // Fallback: couldn't map by offset. Should not normally happen.
    console.warn('[SpanMapper] charSpanToDomRange FAILED for [%d, %d] — returning null', startChar, endChar);
    return null;
}

/**
 * Fallback: find text directly in DOM text nodes (bypasses innerText offsets entirely).
 * Walks all text nodes and searches for the flagged string within them.
 *
 * @param {HTMLElement} editorEl
 * @param {string} flaggedText - The exact text to find
 * @param {number} hintStart - Approximate character position (for disambiguation)
 * @param {string} [sentence] - Optional containing sentence for anchored search (SK-7)
 * @returns {Range|null}
 */
export function findTextInDom(editorEl, flaggedText, hintStart, sentence) {
    console.log('[SpanMapper] findTextInDom called: flaggedText=%s, hintStart=%d',
        JSON.stringify((flaggedText || '').substring(0, 80)), hintStart);
    if (!flaggedText) return null;

    // Walk all text nodes and search for the flagged text within each
    const walker = document.createTreeWalker(editorEl, NodeFilter.SHOW_TEXT);
    const textNodes = [];
    while (walker.nextNode()) {
        textNodes.push(walker.currentNode);
    }
    console.log('[SpanMapper] findTextInDom: %d text nodes found', textNodes.length);

    // First try: find the text within a single text node.
    // Collect ALL occurrences and pick the one closest to hintStart.
    {
        let bestRange = null;
        let bestDistance = Infinity;
        let cumulativeOffset = 0;

        for (const node of textNodes) {
            let searchFrom = 0;
            while (searchFrom < node.textContent.length) {
                const idx = node.textContent.indexOf(flaggedText, searchFrom);
                if (idx < 0) break;
                const globalPos = cumulativeOffset + idx;
                const distance = Math.abs(globalPos - (hintStart || 0));
                if (distance < bestDistance) {
                    try {
                        const range = document.createRange();
                        range.setStart(node, idx);
                        range.setEnd(node, idx + flaggedText.length);
                        bestRange = range;
                        bestDistance = distance;
                    } catch (e) {
                        // Continue searching
                    }
                }
                searchFrom = idx + 1;
            }
            cumulativeOffset += node.textContent.length;
        }
        if (bestRange) {
            console.log('[SpanMapper] findTextInDom: FOUND closest match (distance=%d)', bestDistance);
            return bestRange;
        }
    }
    console.log('[SpanMapper] findTextInDom: NOT found in any single text node');

    // Second try: the flagged text might span adjacent text nodes
    // (e.g., across a <mark> boundary from a previous underline)
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

    // Third try: normalize flaggedText in case of whitespace mismatch.
    // Use closest-match logic with hintStart.
    const normalizedFlagged = _normalize(flaggedText);
    if (normalizedFlagged !== flaggedText) {
        console.log('[SpanMapper] findTextInDom: retrying with normalized flaggedText');
        let bestRange = null;
        let bestDistance = Infinity;
        let cumulativeOffset = 0;

        for (const node of textNodes) {
            const normalizedNode = _normalize(node.textContent);
            let searchFrom = 0;
            while (searchFrom < normalizedNode.length) {
                const idx = normalizedNode.indexOf(normalizedFlagged, searchFrom);
                if (idx < 0) break;
                const globalPos = cumulativeOffset + idx;
                const distance = Math.abs(globalPos - (hintStart || 0));
                if (distance < bestDistance) {
                    try {
                        const range = document.createRange();
                        range.setStart(node, idx);
                        range.setEnd(node, Math.min(idx + normalizedFlagged.length, node.textContent.length));
                        bestRange = range;
                        bestDistance = distance;
                    } catch (e) {
                        // Continue searching
                    }
                }
                searchFrom = idx + 1;
            }
            cumulativeOffset += node.textContent.length;
        }
        if (bestRange) {
            console.log('[SpanMapper] findTextInDom: FOUND via normalized search (distance=%d)', bestDistance);
            return bestRange;
        }
    }

    // Fourth try (SK-7): sentence-anchored relocation — find the sentence
    // first, then locate flaggedText within it. Handles the case where the
    // user edited text and the absolute span drifted.
    if (sentence) {
        const sentRange = _findSentenceInDom(textNodes, sentence);
        if (sentRange) {
            return sentRange;
        }
    }

    console.log('[SpanMapper] findTextInDom: NOT found across adjacent nodes either — returning null');
    return null;
}

/**
 * Sentence-anchored relocation helper (SK-7).
 * Finds the sentence text in DOM nodes, then searches for flaggedText
 * within the sentence's DOM range.
 *
 * @param {Text[]} textNodes - All text nodes in the editor
 * @param {string} sentence - The containing sentence from the issue
 * @returns {Range|null}
 */
function _findSentenceInDom(textNodes, sentence) {
    if (!sentence) return null;
    const normalizedSent = _normalize(sentence);
    for (const node of textNodes) {
        const normalizedNode = _normalize(node.textContent);
        const idx = normalizedNode.indexOf(normalizedSent);
        if (idx >= 0) {
            console.log('[SpanMapper] sentence-anchored: found sentence at idx=%d', idx);
            try {
                const range = document.createRange();
                range.setStart(node, idx);
                range.setEnd(node, Math.min(idx + normalizedSent.length, node.textContent.length));
                return range;
            } catch (e) {
                // Sentence found but range failed
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
