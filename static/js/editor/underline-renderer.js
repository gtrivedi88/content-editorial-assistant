/**
 * Underline Renderer — creates/removes <mark> underlines in the editor.
 * Uses viewport-based rendering: only injects <mark> elements for issues
 * in the visible scroll region (with 200px buffer). Caps at 150 active marks.
 */

import { charSpanToDomRange, findTextInDom, getPlainText } from './span-mapper.js';

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
    console.log('[UnderlineRenderer] renderUnderlines called with %d errors', errors.length);
    errors.forEach((e, i) => console.log('[UnderlineRenderer]   error[%d]: id=%s rule=%s globalSpan=[%d,%d] flagged_text=%s',
        i, e.id, e.rule_name || e.type, e.globalSpan[0], e.globalSpan[1],
        JSON.stringify((e.flagged_text || '').substring(0, 60))));
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

    // Clear existing marks
    clearUnderlines(editorEl);

    // Sort descending by span start to avoid offset invalidation
    const sorted = [...visibleErrors].sort((a, b) => b.globalSpan[0] - a.globalSpan[0]);

    for (const error of sorted) {
        _renderSingleMark(editorEl, error);
    }

    // Verify how many marks actually got created
    const markCount = editorEl.querySelectorAll('.cea-underline').length;
    console.log('[UnderlineRenderer] _viewportRender DONE: %d marks created in DOM', markCount);
}

/**
 * Render a single <mark> element for an error.
 */
function _renderSingleMark(editorEl, error) {
    const [start, end] = error.globalSpan;
    let range = null;
    console.log('[UnderlineRenderer] _renderSingleMark: id=%s rule=%s span=[%d,%d] flagged_text=%s',
        error.id, error.rule_name || error.type, start, end,
        JSON.stringify((error.flagged_text || '').substring(0, 60)));

    if (start !== end) {
        // Offset-based mapping when a valid span exists
        range = charSpanToDomRange(editorEl, start, end);

        // Verify the range found the right text; fallback to text search if not
        if (range && error.flagged_text) {
            const rangeText = range.toString();
            console.log('[UnderlineRenderer]   rangeText=%s vs flagged=%s match=%s',
                JSON.stringify(rangeText.substring(0, 60)),
                JSON.stringify(error.flagged_text.substring(0, 60)),
                rangeText === error.flagged_text);
            if (rangeText !== error.flagged_text) {
                // Offset drift detected — fall back to searching for the flagged text
                console.log('[UnderlineRenderer]   DRIFT detected, trying findTextInDom fallback');
                const fallback = findTextInDom(editorEl, error.flagged_text, start, error.sentence);
                if (fallback) {
                    console.log('[UnderlineRenderer]   findTextInDom fallback SUCCEEDED');
                    range = fallback;
                } else {
                    // Discard the drifted range — don't highlight wrong text.
                    // Legacy principle: never create a mark that wraps incorrect text.
                    console.log('[UnderlineRenderer]   findTextInDom fallback FAILED — discarding drifted range');
                    range = null;
                }
            }
        }
    }

    if (!range) {
        // Last resort: search for the flagged text anywhere in the DOM.
        // Covers [0,0] spans from unresolved LLM issues.
        console.log('[UnderlineRenderer]   No range from offset mapping, trying last-resort text search');
        if (error.flagged_text) {
            range = findTextInDom(editorEl, error.flagged_text, start, error.sentence);
        }
        if (!range) {
            console.warn('[UnderlineRenderer]   ALL METHODS FAILED for error %s — no highlight created', error.id);
            return;
        }
    }

    // Check if this range is already inside a <mark>
    const ancestor = range.commonAncestorContainer;
    if (ancestor.nodeType === Node.ELEMENT_NODE && ancestor.closest?.('.cea-underline')) return;
    if (ancestor.nodeType === Node.TEXT_NODE && ancestor.parentElement?.closest?.('.cea-underline')) return;

    try {
        const mark = document.createElement('mark');
        mark.className = 'cea-underline';
        mark.dataset.errorId = error.id;
        mark.dataset.group = error.group;
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
 */
export function replaceUnderlineText(editorEl, errorId, newText) {
    const mark = editorEl.querySelector(`.cea-underline[data-error-id="${errorId}"]`);
    if (mark) {
        mark.textContent = newText;
        mark.classList.add('cea-underline--resolved');
        // Remove the mark wrapper after a brief visual feedback
        setTimeout(() => {
            removeUnderline(editorEl, errorId);
        }, 600);
    }
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
