/**
 * Underline Renderer — creates/removes <mark> underlines in the editor.
 */

import { charSpanToDomRange, findTextInDom, getPlainText } from './span-mapper.js';

/**
 * Render solid single-color underlines for all errors in the editor.
 * Applies from last-to-first (descending by span start) to preserve offsets.
 *
 * @param {HTMLElement} editorEl
 * @param {Array} errors - Normalized error objects with globalSpan and group
 */
export function renderUnderlines(editorEl, errors) {
    // Sort descending by span start to avoid offset invalidation
    const sorted = [...errors].sort((a, b) => b.globalSpan[0] - a.globalSpan[0]);

    for (const error of sorted) {
        const [start, end] = error.globalSpan;
        if (start === end) continue;

        let range = charSpanToDomRange(editorEl, start, end);

        // Verify the range found the right text; fallback to text search if not
        if (range && error.flagged_text) {
            const rangeText = range.toString();
            if (rangeText !== error.flagged_text) {
                // Offset drift detected — fall back to searching for the flagged text
                const fallback = findTextInDom(editorEl, error.flagged_text, start);
                if (fallback) range = fallback;
            }
        }

        if (!range) {
            // Last resort: try finding the flagged text anywhere
            if (error.flagged_text) {
                range = findTextInDom(editorEl, error.flagged_text, start);
            }
            if (!range) continue;
        }

        // Check if this range is already inside a <mark>
        const ancestor = range.commonAncestorContainer;
        if (ancestor.nodeType === Node.ELEMENT_NODE && ancestor.closest?.('.cea-underline')) continue;
        if (ancestor.nodeType === Node.TEXT_NODE && ancestor.parentElement?.closest?.('.cea-underline')) continue;

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
