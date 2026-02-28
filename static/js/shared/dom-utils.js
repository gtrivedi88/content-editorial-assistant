/**
 * DOM utility functions.
 */

/**
 * Normalize whitespace to match backend normalization.
 * Identical to Python preprocessor._normalize_whitespace():
 *   CRLF → LF, lone CR → LF, tabs → space.
 * Must be applied before sending text to the backend so that
 * backend spans map directly to the DOM text.
 *
 * @param {string} text
 * @returns {string}
 */
export function normalizeWhitespace(text) {
    return text.normalize('NFC').replace(/\r\n/g, '\n').replace(/\r/g, '\n').replace(/\t/g, ' ');
}

const _escapeEl = document.createElement('div');

/**
 * Escape HTML entities using DOM textContent (safe against XSS).
 */
export function escapeHtml(text) {
    _escapeEl.textContent = text;
    return _escapeEl.innerHTML;
}

/**
 * Create a DOM element with attributes and children.
 * @param {string} tag
 * @param {Object} attrs - { className, id, textContent, innerHTML, dataset, ... }
 * @param {Array<Node|string>} children
 * @returns {HTMLElement}
 */
export function createElement(tag, attrs = {}, children = []) {
    const el = document.createElement(tag);

    for (const [key, value] of Object.entries(attrs)) {
        if (key === 'className') {
            el.className = value;
        } else if (key === 'textContent') {
            el.textContent = value;
        } else if (key === 'innerHTML') {
            el.innerHTML = value;
        } else if (key === 'dataset') {
            for (const [dk, dv] of Object.entries(value)) {
                el.dataset[dk] = dv;
            }
        } else if (key === 'style' && typeof value === 'object') {
            Object.assign(el.style, value);
        } else if (key.startsWith('on') && typeof value === 'function') {
            el.addEventListener(key.slice(2).toLowerCase(), value);
        } else {
            el.setAttribute(key, value);
        }
    }

    for (const child of children) {
        if (typeof child === 'string') {
            el.appendChild(document.createTextNode(child));
        } else if (child instanceof Node) {
            el.appendChild(child);
        }
    }

    return el;
}

/**
 * Debounce a function.
 */
export function debounce(fn, ms) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), ms);
    };
}

/**
 * Scroll an element into view smoothly.
 */
export function scrollToElement(el, block = 'center') {
    if (el) {
        el.scrollIntoView({ behavior: 'smooth', block });
    }
}

/**
 * Generate a UUID v4.
 */
export function generateId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
    });
}

/**
 * Copy text to the clipboard.
 * Uses the modern Clipboard API with fallback for older browsers.
 *
 * @param {string} text - The text to copy
 * @returns {Promise<boolean>} true if copy succeeded
 */
export async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        let success = false;
        try {
            success = document.execCommand('copy');
        } catch {
            success = false;
        }
        document.body.removeChild(textarea);
        return success;
    }
}
