/**
 * Underline Renderer — creates/removes <mark> underlines in the editor.
 * Uses viewport-based rendering: only injects <mark> elements for issues
 * in the visible scroll region (with 200px buffer). Caps at 150 active marks.
 */

import { charSpanToDomRange, findTextInDom, getPlainText, buildTextMap, buildVirtualString } from './span-mapper.js';
import { getCategory } from '../shared/style-guide-groups.js';

/**
 * Full errors array maintained in memory for viewport-based rendering.
 */
let allErrors = [];
let editorRef = null;
let renderScheduled = false;
let scrollHandler = null;
const MAX_ACTIVE_MARKS = 150;
const VIEWPORT_BUFFER = 200;

/**
 * Schedule a viewport-aware render. Debounced at 100ms using requestAnimationFrame.
 * Call this instead of renderUnderlines() for scroll-triggered re-renders.
 */
export function scheduleRender() {
    if (renderScheduled) return;
    renderScheduled = true;
    requestAnimationFrame(() => {
        renderScheduled = false;
        if (editorRef && allErrors.length > 0) {
            _viewportRender(editorRef, allErrors);
        }
    });
}

/**
 * Render solid single-color underlines for all errors in the editor.
 * Sets up viewport-based rendering with scroll listener.
 *
 * @param {HTMLElement} editorEl
 * @param {Array} errors - Normalized error objects with globalSpan and group
 */
export function renderUnderlines(editorEl, errors) {
    allErrors = errors;
    editorRef = editorEl;

    // Set up scroll listener for viewport-based rendering
    const editorArea = editorEl.closest('.cea-editor-area');
    if (editorArea && !scrollHandler) {
        scrollHandler = () => scheduleRender();
        editorArea.addEventListener('scroll', scrollHandler, { passive: true });
    }

    _viewportRender(editorEl, errors);
}

/**
 * Viewport-aware rendering: only inject marks for visible errors.
 * Uses the editor's scroll position to determine visible character range.
 */
function _viewportRender(editorEl, errors) {
    // If total errors fit within the cap, render all — no viewport filtering needed
    let visibleErrors;
    if (errors.length <= MAX_ACTIVE_MARKS) {
        visibleErrors = errors;
    } else {
        // Viewport filtering for large error counts
        const editorArea = editorEl.closest('.cea-editor-area') || editorEl;
        const scrollTop = editorArea.scrollTop;
        const clientHeight = editorArea.clientHeight;
        const visibleTop = scrollTop - VIEWPORT_BUFFER;
        const visibleBottom = scrollTop + clientHeight + VIEWPORT_BUFFER;

        const plainText = getPlainText(editorEl);
        const totalHeight = editorEl.scrollHeight || 1;
        const charsPerPixel = plainText.length / totalHeight;

        const estimatedCharStart = Math.max(0, Math.floor(visibleTop * charsPerPixel));
        const estimatedCharEnd = Math.min(plainText.length, Math.ceil(visibleBottom * charsPerPixel));

        visibleErrors = errors.filter((error) => {
            const [start, end] = error.globalSpan;
            return end >= estimatedCharStart && start <= estimatedCharEnd;
        });

        if (visibleErrors.length > MAX_ACTIVE_MARKS) {
            visibleErrors = visibleErrors.slice(0, MAX_ACTIVE_MARKS);
        }
    }

    clearUnderlines(editorEl);

    // Build shared data structures once for all errors
    const textMap = buildTextMap(editorEl);
    const virtual = buildVirtualString(null, editorEl);

    // Sort descending by span start to avoid offset invalidation
    const sorted = [...visibleErrors].sort((a, b) => b.globalSpan[0] - a.globalSpan[0]);

    for (const error of sorted) {
        _renderSingleMark(editorEl, error, textMap, virtual);
    }
}

/**
 * Render a single <mark> element for an error.
 * Content-first: uses text search as primary path, offsets as fallback.
 *
 * @param {HTMLElement} editorEl
 * @param {Object} error
 * @param {Array} [textMap] - Pre-built text map for offset-based fallback
 * @param {Object} [virtual] - Pre-built virtual string for content-first search
 */
function _renderSingleMark(editorEl, error, textMap, virtual) {
    const [start, end] = error.globalSpan;
    let range = null;

    // PRIMARY: content-first search via virtual string
    if (error.flagged_text) {
        range = findTextInDom(editorEl, error.flagged_text, start, error.sentence, virtual);
    }

    // FALLBACK: offset-based mapping when content search fails
    if (!range && start !== end) {
        range = charSpanToDomRange(editorEl, start, end, textMap);
        // Safety: verify offset-based range actually matches the flagged text
        if (range && error.flagged_text) {
            const rangeText = range.toString();
            if (rangeText !== error.flagged_text) {
                range = null;
            }
        }
    }

    if (!range) return;

    // Check if this range is already inside a <mark>
    const ancestor = range.commonAncestorContainer;
    if (ancestor.nodeType === Node.ELEMENT_NODE && ancestor.closest?.('.cea-underline')) return;
    if (ancestor.nodeType === Node.TEXT_NODE && ancestor.parentElement?.closest?.('.cea-underline')) return;

    try {
        const mark = document.createElement('mark');
        mark.className = 'cea-underline';
        mark.dataset.errorId = error.id;
        mark.dataset.group = error.group;
        mark.dataset.cat = getCategory(error);
        mark.setAttribute('tabindex', '0');
        mark.setAttribute('role', 'button');
        mark.setAttribute('aria-label', error.message);
        range.surroundContents(mark);
    } catch (e) {
        // surroundContents fails on partial element selections
        // Fall back to extracting and wrapping
        try {
            const mark = document.createElement('mark');
            mark.className = 'cea-underline';
            mark.dataset.errorId = error.id;
            mark.dataset.group = error.group;
            mark.dataset.cat = getCategory(error);
            mark.setAttribute('tabindex', '0');
            mark.setAttribute('role', 'button');
            mark.setAttribute('aria-label', error.message);

            const fragment = range.extractContents();
            mark.appendChild(fragment);
            range.insertNode(mark);
        } catch (e2) {
            console.warn('[UnderlineRenderer] Could not wrap error:', error.id, e2);
        }
    }
}

/**
 * Remove all underline marks from the editor, preserving text content.
 */
export function clearUnderlines(editorEl) {
    const marks = editorEl.querySelectorAll('.cea-underline');
    for (const mark of marks) {
        const parent = mark.parentNode;
        while (mark.firstChild) {
            parent.insertBefore(mark.firstChild, mark);
        }
        parent.removeChild(mark);
        parent.normalize(); // Merge adjacent text nodes
    }

    // Clean up scroll handler if clearing
    if (editorEl === editorRef) {
        allErrors = [];
    }
}

/**
 * Remove a specific underline by error ID.
 */
export function removeUnderline(editorEl, errorId) {
    const mark = editorEl.querySelector(`.cea-underline[data-error-id="${errorId}"]`);
    if (mark) {
        const parent = mark.parentNode;
        while (mark.firstChild) {
            parent.insertBefore(mark.firstChild, mark);
        }
        parent.removeChild(mark);
        parent.normalize();
    }
}

/**
 * Replace the text of a specific underline (for accept).
 *
 * Handles backtick-wrapped suggestions: when the replacement text is
 * backtick-delimited (e.g., `OSTree`) AND the adjacent DOM text already
 * has backticks (the original source had inline code formatting), the
 * outer backticks are stripped to prevent double-backtick insertion.
 *
 * Sentence-level rewrites: when the LLM returns a full sentence rewrite
 * (much longer than the flagged span), replaces the entire sentence in
 * the DOM instead of just the mark's content to prevent text duplication.
 *
 * @param {HTMLElement} editorEl - The contenteditable editor element
 * @param {string} errorId - The error ID to replace
 * @param {string} newText - The replacement text
 * @param {string} [sentence] - Optional containing sentence for sentence-level replacement
 * @param {string} [scope] - Backend scope signal ("sentence" = sentence-level rewrite)
 */
export function replaceUnderlineText(editorEl, errorId, newText, sentence, scope) {
    const mark = editorEl.querySelector(`.cea-underline[data-error-id="${errorId}"]`);
    if (!mark) return;

    const markText = mark.textContent;
    const isSentenceRewrite = scope === 'sentence'
        || (sentence && newText.length > markText.length * 2 && newText.length > 40);

    // Sentence-level rewrite: replace the full sentence, not just the mark
    if (isSentenceRewrite) {
        if (_replaceSentence(editorEl, mark, newText, sentence)) {
            return;
        }
        // DOM sentence mapping failed — abort rather than stuffing
        // a full sentence into a single-word mark
        console.warn(
            '[UnderlineRenderer] Sentence replacement failed for error',
            errorId, '— cannot safely apply edit',
        );
        return;
    }

    // Simple replacement: swap the mark's text content
    let text = newText;

    // Prevent double backticks: if the replacement is backtick-wrapped
    // and the surrounding DOM text already provides backticks, strip
    // the redundant outer backticks from the replacement.
    if (text.startsWith('`') && text.endsWith('`') && text.length > 2) {
        const prev = mark.previousSibling;
        const next = mark.nextSibling;
        const prevEndsBacktick = prev?.nodeType === Node.TEXT_NODE
            && prev.textContent.endsWith('`');
        const nextStartsBacktick = next?.nodeType === Node.TEXT_NODE
            && next.textContent.startsWith('`');
        if (prevEndsBacktick && nextStartsBacktick) {
            text = text.slice(1, -1);
        }
    }

    mark.textContent = text;
    mark.classList.add('cea-underline--resolved');
    // Remove the mark wrapper after a brief visual feedback
    setTimeout(() => {
        removeUnderline(editorEl, errorId);
    }, 600);
}

/**
 * Replace an entire sentence in the DOM when the LLM returns a
 * sentence-level rewrite.
 *
 * Steps:
 * 1. Pre-check that the sentence exists in the parent's text content
 * 2. Collect other marks that might be removed as collateral
 * 3. Unwrap the target mark (keep its text as a regular text node)
 * 4. Find the sentence in the cleaned text and build a DOM range
 * 5. Replace the sentence via range.deleteContents + range.insertNode
 * 6. Emit cleanup event for marks removed as collateral
 *
 * @param {HTMLElement} editorEl - The contenteditable editor element
 * @param {HTMLElement} mark - The mark element being accepted
 * @param {string} newText - The replacement sentence text
 * @param {string} sentence - The original sentence to find and replace
 * @returns {boolean} True if replacement succeeded or mark was unwrapped
 */
function _replaceSentence(editorEl, mark, newText, sentence) {
    const parent = mark.parentNode;
    if (!parent) return false;

    const normalize = (txt) => txt.replaceAll(/\s+/g, ' ');
    const normSentence = normalize(sentence);

    // Pre-check using normalized text (handles \n vs space mismatch)
    if (!normalize(parent.textContent).includes(normSentence)) {
        return false;
    }

    // Collect other mark IDs in parent for collateral cleanup
    const otherMarkIds = [];
    parent.querySelectorAll('.cea-underline').forEach(m => {
        if (m !== mark) otherMarkIds.push(m.dataset.errorId);
    });

    // Unwrap the target mark, preserving its text content
    while (mark.firstChild) {
        parent.insertBefore(mark.firstChild, mark);
    }
    mark.remove();
    parent.normalize();

    // Find the sentence using normalized text
    const sentIdx = normalize(parent.textContent).indexOf(normSentence);
    if (sentIdx === -1) {
        // Extremely unlikely after pre-check — mark already unwrapped
        return true;
    }

    const sentEnd = sentIdx + normSentence.length;

    // Walk text nodes to build a DOM range covering the sentence.
    // Use proportional offset mapping between normalized and original text.
    const walker = document.createTreeWalker(parent, NodeFilter.SHOW_TEXT);
    let pos = 0;
    let startNode = null, startOffset = 0;
    let endNode = null, endOffset = 0;

    while (walker.nextNode()) {
        const node = walker.currentNode;
        const nodeLen = normalize(node.textContent).length;

        if (!startNode && pos + nodeLen > sentIdx) {
            startNode = node;
            startOffset = Math.floor(
                (sentIdx - pos) * (node.textContent.length / nodeLen),
            );
        }
        if (pos + nodeLen >= sentEnd) {
            endNode = node;
            endOffset = Math.ceil(
                (sentEnd - pos) * (node.textContent.length / nodeLen),
            );
            break;
        }
        pos += nodeLen;
    }

    if (!startNode || !endNode) return true;

    try {
        const range = document.createRange();
        range.setStart(startNode, startOffset);
        range.setEnd(endNode, Math.min(endOffset, endNode.textContent.length));
        range.deleteContents();
        range.insertNode(document.createTextNode(newText));
        parent.normalize();
    } catch (e) {
        console.warn('[UnderlineRenderer] _replaceSentence failed:', e);
        return true;
    }

    // Emit cleanup event for marks that were removed as collateral
    if (otherMarkIds.length > 0) {
        const removedIds = otherMarkIds.filter(id =>
            !editorEl.querySelector(`.cea-underline[data-error-id="${id}"]`)
        );
        if (removedIds.length > 0) {
            globalThis.dispatchEvent(new CustomEvent('cea:errors-removed', {
                detail: { errorIds: removedIds },
            }));
        }
    }

    return true;
}

/**
 * Set active state on a specific underline.
 */
export function setActiveUnderline(editorEl, errorId) {
    // Clear previous
    const prev = editorEl.querySelector('.cea-underline--active');
    if (prev) prev.classList.remove('cea-underline--active');

    if (errorId) {
        const mark = editorEl.querySelector(`.cea-underline[data-error-id="${errorId}"]`);
        if (mark) {
            mark.classList.add('cea-underline--active');
            mark.classList.remove('cea-animate-pulse');
            void mark.offsetWidth; // reflow
            mark.classList.add('cea-animate-pulse');
            return mark;
        }
    }
    return null;
}

/**
 * Show/hide underlines based on active group.
 */
export function filterUnderlines(editorEl, group) {
    const marks = editorEl.querySelectorAll('.cea-underline');
    for (const mark of marks) {
        if (group === 'all' || mark.dataset.group === group) {
            mark.classList.remove('cea-underline--filtered');
        } else {
            mark.classList.add('cea-underline--filtered');
        }
    }
}
