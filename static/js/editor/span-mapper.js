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
 * CRLF → LF, lone CR → LF, tabs → space, multi-space → single space.
 */
function _normalize(text) {
    return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\t/g, ' ').replace(/ {2,}/g, ' ');
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
export function buildTextMap(editorEl) {
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

        if (tag === 'BR') {
            pos += 1;
            return;
        }

        const isBlock = BLOCK_TAGS.has(tag);
        if (isBlock && pos > 0 && entries.length > 0) {
            pos += 1;
        }

        for (const child of node.childNodes) {
            walk(child);
        }
    }

    walk(editorEl);
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
 * @param {Array} [prebuiltMap] - Optional pre-built text map to avoid redundant DOM walks
 * @returns {Range|null}
 */
export function charSpanToDomRange(editorEl, startChar, endChar, prebuiltMap) {
    const map = prebuiltMap || buildTextMap(editorEl);

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
            const startUtf16 = _codepointToUtf16Offset(startNode.textContent, startOffset);
            const endUtf16 = _codepointToUtf16Offset(endNode.textContent, endOffset);
            range.setStart(startNode, Math.min(startUtf16, startNode.textContent.length));
            range.setEnd(endNode, Math.min(endUtf16, endNode.textContent.length));
            return range;
        } catch (e) {
            console.warn('[SpanMapper] Range creation failed for [%d, %d]:', startChar, endChar, e);
        }
    }

    return null;
}

// ---------------------------------------------------------------------------
// Virtual string infrastructure — concatenates all text nodes into one
// searchable string with a segment map for converting virtual positions
// back to DOM Range objects.  Built once per render pass.
// ---------------------------------------------------------------------------

/**
 * Build a virtual string from all text nodes under a root element.
 * Returns { str, segments } where segments[i] = { node, start, length }.
 *
 * @param {Text[]} textNodes - Pre-collected text nodes (or null to collect from editorEl)
 * @param {HTMLElement} [editorEl] - Editor element (used only when textNodes is null)
 * @returns {{ str: string, segments: Array<{node: Text, start: number, length: number}> }}
 */
export function buildVirtualString(textNodes, editorEl) {
    if (!textNodes) {
        textNodes = [];
        const walker = document.createTreeWalker(editorEl, NodeFilter.SHOW_TEXT);
        while (walker.nextNode()) textNodes.push(walker.currentNode);
    }
    let str = '';
    const segments = [];
    for (const node of textNodes) {
        const len = node.textContent.length;
        if (len > 0) {
            segments.push({ node, start: str.length, length: len });
            str += node.textContent;
        }
    }
    return { str, segments };
}

/**
 * Convert a [matchStart, matchStart+matchLen) range in the virtual string
 * back to a DOM Range spanning the correct text nodes.
 *
 * @param {{ segments: Array<{node: Text, start: number, length: number}> }} virtual
 * @param {number} matchStart - Start position in virtual string
 * @param {number} matchLen - Length of matched text
 * @returns {Range|null}
 */
function _virtualRangeToDOM(virtual, matchStart, matchLen) {
    const matchEnd = matchStart + matchLen;
    let startNode = null, startOffset = 0;
    let endNode = null, endOffset = 0;

    for (const seg of virtual.segments) {
        const segEnd = seg.start + seg.length;
        if (!startNode && segEnd > matchStart) {
            startNode = seg.node;
            startOffset = matchStart - seg.start;
        }
        if (segEnd >= matchEnd) {
            endNode = seg.node;
            endOffset = matchEnd - seg.start;
            break;
        }
    }

    if (!startNode || !endNode) return null;

    try {
        const range = document.createRange();
        range.setStart(startNode, Math.min(startOffset, startNode.textContent.length));
        range.setEnd(endNode, Math.min(endOffset, endNode.textContent.length));
        return range;
    } catch (e) {
        return null;
    }
}

/**
 * Find ALL occurrences of `needle` in `haystack` and return the one
 * whose position is closest to `hint`.
 *
 * @param {string} haystack
 * @param {string} needle
 * @param {number} hint - Approximate position for disambiguation
 * @returns {number} Best match index, or -1
 */
function _closestIndexOf(haystack, needle, hint) {
    let bestIdx = -1;
    let bestDist = Infinity;
    let from = 0;
    while (from <= haystack.length - needle.length) {
        const idx = haystack.indexOf(needle, from);
        if (idx < 0) break;
        const dist = Math.abs(idx - (hint || 0));
        if (dist < bestDist) {
            bestDist = dist;
            bestIdx = idx;
        }
        from = idx + 1;
    }
    return bestIdx;
}

/**
 * Content-first text search: find flaggedText in the DOM using a virtual
 * string built from all text nodes.  Handles text spanning arbitrary
 * node boundaries (bold, code, inline formatting).
 *
 * Strategies (each relaxes one constraint):
 *   1. Single-node exact match (fast path, closest to hintStart)
 *   2. Virtual-exact match (handles N-node spans, closest to hintStart)
 *   3. Virtual-normalized match (handles whitespace differences)
 *   4. Sentence-within-virtual (find sentence, narrow to flaggedText)
 *
 * @param {HTMLElement} editorEl
 * @param {string} flaggedText - The exact text to find
 * @param {number} hintStart - Approximate character position (for disambiguation)
 * @param {string} [sentence] - Optional containing sentence for anchored search
 * @param {Object} [prebuiltVirtual] - Optional pre-built virtual string to avoid redundant walks
 * @returns {Range|null}
 */
export function findTextInDom(editorEl, flaggedText, hintStart, sentence, prebuiltVirtual) {
    if (!flaggedText) return null;

    const virtual = prebuiltVirtual || buildVirtualString(null, editorEl);

    // Strategy 1: single-node exact match (fast path)
    {
        let bestRange = null;
        let bestDistance = Infinity;

        for (const seg of virtual.segments) {
            const nodeText = seg.node.textContent;
            let searchFrom = 0;
            while (searchFrom < nodeText.length) {
                const idx = nodeText.indexOf(flaggedText, searchFrom);
                if (idx < 0) break;
                const globalPos = seg.start + idx;
                const distance = Math.abs(globalPos - (hintStart || 0));
                if (distance < bestDistance) {
                    try {
                        const range = document.createRange();
                        range.setStart(seg.node, idx);
                        range.setEnd(seg.node, idx + flaggedText.length);
                        bestRange = range;
                        bestDistance = distance;
                    } catch (e) {
                        // skip
                    }
                }
                searchFrom = idx + 1;
            }
        }
        if (bestRange) return bestRange;
    }

    // Strategy 2: virtual-exact match (handles text spanning N nodes)
    {
        const idx = _closestIndexOf(virtual.str, flaggedText, hintStart);
        if (idx >= 0) {
            const range = _virtualRangeToDOM(virtual, idx, flaggedText.length);
            if (range) return range;
        }
    }

    // Strategy 3: virtual-normalized match (whitespace/newline differences)
    {
        const normVirtual = _normalize(virtual.str);
        const normFlagged = _normalize(flaggedText);
        if (normFlagged !== flaggedText || normVirtual !== virtual.str) {
            const idx = _closestIndexOf(normVirtual, normFlagged, hintStart);
            if (idx >= 0) {
                const range = _virtualRangeToDOM(virtual, idx, normFlagged.length);
                if (range) return range;
            }
        }
    }

    // Strategy 4: sentence-anchored — find sentence in virtual string,
    // then locate flaggedText within the sentence range
    if (sentence) {
        const range = _findSentenceInDom(virtual, sentence, flaggedText, hintStart);
        if (range) return range;
    }

    return null;
}

/**
 * Sentence-anchored relocation: find the sentence in the virtual string,
 * then narrow to flaggedText within the sentence range.  Returns the
 * narrow range for the flagged text, not the sentence.
 *
 * @param {Object} virtual - Pre-built virtual string
 * @param {string} sentence - The containing sentence from the issue
 * @param {string} flaggedText - The flagged text to narrow to
 * @param {number} hintStart - Disambiguation hint
 * @returns {Range|null}
 */
function _findSentenceInDom(virtual, sentence, flaggedText, hintStart) {
    if (!sentence) return null;

    const normVirtual = _normalize(virtual.str);
    const normSentence = _normalize(sentence);
    const sentIdx = _closestIndexOf(normVirtual, normSentence, hintStart);
    if (sentIdx < 0) return null;

    // Narrow: search for flaggedText within the sentence region
    const sentEnd = sentIdx + normSentence.length;
    const normFlagged = _normalize(flaggedText);
    const withinIdx = normVirtual.indexOf(normFlagged, sentIdx);

    if (withinIdx >= 0 && withinIdx + normFlagged.length <= sentEnd) {
        const range = _virtualRangeToDOM(virtual, withinIdx, normFlagged.length);
        if (range) return range;
    }

    // Fallback: exact (non-normalized) search within sentence region
    const exactIdx = virtual.str.indexOf(flaggedText, sentIdx);
    if (exactIdx >= 0 && exactIdx + flaggedText.length <= sentIdx + normSentence.length + 5) {
        const range = _virtualRangeToDOM(virtual, exactIdx, flaggedText.length);
        if (range) return range;
    }

    return null;
}

/**
 * Get the plain text content of the editor (matching what the backend receives).
 */
export function getPlainText(editorEl) {
    return editorEl.innerText || editorEl.textContent || '';
}
