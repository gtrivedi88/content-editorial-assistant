/**
 * Content Type Selection Popup — modal dialog shown when the frontend
 * detector cannot confidently determine the content type.
 *
 * Promise-based API: show() returns a Promise<string> that resolves
 * with the user's selected content type.
 */

import { createElement } from '../shared/dom-utils.js';

const CONTENT_TYPES = [
    { value: 'concept', label: 'Concept' },
    { value: 'procedure', label: 'Procedure' },
    { value: 'reference', label: 'Reference' },
    { value: 'release_notes', label: 'Release Notes' },
    { value: 'assembly', label: 'Assembly' },
];

export class ContentTypePopup {
    constructor() {
        this._overlay = null;
        this._resolve = null;
    }

    /**
     * Show the content type selection popup.
     *
     * @returns {Promise<string>} Resolves with the selected content type value
     */
    show() {
        // Remove any existing popup
        this.hide();

        return new Promise((resolve) => {
            this._resolve = resolve;
            this._render();
        });
    }

    /**
     * Hide and clean up the popup.
     */
    hide() {
        if (this._overlay) {
            this._overlay.remove();
            this._overlay = null;
        }
        if (this._resolve) {
            this._resolve('concept');
            this._resolve = null;
        }
    }

    /**
     * Render the popup DOM.
     */
    _render() {
        // Overlay
        this._overlay = createElement('div', {
            className: 'cea-ct-popup-overlay',
        });

        // Dialog
        const dialog = createElement('div', {
            className: 'cea-ct-popup',
        });
        dialog.setAttribute('role', 'dialog');
        dialog.setAttribute('aria-modal', 'true');
        dialog.setAttribute('aria-label', 'Select content type');

        // Title
        const title = createElement('h3', {
            className: 'cea-ct-popup__title',
        });
        title.textContent = 'What type of content is this?';
        dialog.appendChild(title);

        // Description
        const desc = createElement('p', {
            className: 'cea-ct-popup__desc',
        });
        desc.textContent = 'We could not auto-detect the content type. Please select one to ensure accurate analysis.';
        dialog.appendChild(desc);

        // Select dropdown
        const select = createElement('select', {
            className: 'cea-ct-popup__select',
        });
        select.setAttribute('aria-label', 'Content type');
        for (const ct of CONTENT_TYPES) {
            const option = createElement('option');
            option.value = ct.value;
            option.textContent = ct.label;
            select.appendChild(option);
        }
        dialog.appendChild(select);

        // Actions
        const actions = createElement('div', {
            className: 'cea-ct-popup__actions',
        });

        const confirmBtn = createElement('button', {
            className: 'cea-toolbar-btn primary',
        });
        confirmBtn.textContent = 'Continue';
        confirmBtn.addEventListener('click', () => {
            const selected = select.value;
            this._overlay.remove();
            this._overlay = null;
            if (this._resolve) {
                const fn = this._resolve;
                this._resolve = null;
                fn(selected);
            }
        });
        actions.appendChild(confirmBtn);

        dialog.appendChild(actions);
        this._overlay.appendChild(dialog);
        document.body.appendChild(this._overlay);

        // Keyboard handling
        this._overlay.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                e.stopPropagation();
                const selected = select.value;
                this._overlay.remove();
                this._overlay = null;
                if (this._resolve) {
                    const fn = this._resolve;
                    this._resolve = null;
                    fn(selected);
                }
            }
        });

        // Focus the select for keyboard accessibility
        requestAnimationFrame(() => select.focus());
    }
}
