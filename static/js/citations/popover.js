/**
 * Citation Popover — floating tooltip for style guide excerpts.
 * On citation click: fetches GET /api/v1/citations/<rule_type>, renders tooltip.
 * Accessible: role="tooltip", keyboard dismissible (Escape), click-outside dismiss.
 */

import { getCitation } from '../state/actions.js';
import { createElement, escapeHtml } from '../shared/dom-utils.js';

export class CitationPopover {
    constructor() {
        this._popoverEl = null;
        this._currentRuleType = null;
        this._clickOutsideHandler = null;

        // Listen for citation click events from issue cards
        globalThis.addEventListener('cea:show-citation', (e) => {
            const { ruleType, anchorEl } = e.detail;
            this._handleCitationClick(ruleType, anchorEl);
        });
    }

    /**
     * Handle citation link click.
     */
    async _handleCitationClick(ruleType, anchorEl) {
        // Toggle off if same rule type is already showing
        if (this._currentRuleType === ruleType && this._popoverEl) {
            this.hide();
            return;
        }

        this.hide();
        this._currentRuleType = ruleType;

        // Show loading state
        const loadingPopover = this._createPopover(anchorEl);
        const body = loadingPopover.querySelector('.cea-citation-popover__body');
        body.innerHTML = '';
        body.appendChild(createElement('div', {
            className: 'cea-suggestion-loading',
            innerHTML: '<span class="cea-suggestion-spinner"></span> Loading citation...',
        }));

        // Fetch citation data
        const citation = await getCitation(ruleType);

        // Guard: popover may have been dismissed while loading
        if (this._currentRuleType !== ruleType) return;

        if (!citation || citation.error) {
            body.innerHTML = '';
            body.appendChild(createElement('div', {
                className: 'cea-suggestion-error',
                textContent: citation?.error || 'Citation not available',
            }));
            return;
        }

        // Render citation content
        this._renderCitationContent(loadingPopover, citation);
    }

    /**
     * Create the popover element and position it near the anchor.
     */
    _createPopover(anchorEl) {
        const popover = createElement('div', {
            className: 'cea-citation-popover',
            role: 'tooltip',
            'aria-live': 'polite',
        });

        // Close button
        const closeBtn = createElement('button', {
            className: 'cea-citation-popover__close',
            'aria-label': 'Close citation',
            innerHTML: '<i class="fas fa-xmark"></i>',
            onClick: () => this.hide(),
        });
        popover.appendChild(closeBtn);

        // Header
        popover.appendChild(createElement('div', { className: 'cea-citation-popover__header' }));

        // Body
        popover.appendChild(createElement('div', { className: 'cea-citation-popover__body' }));

        // Footer
        popover.appendChild(createElement('div', { className: 'cea-citation-popover__footer' }));

        document.body.appendChild(popover);
        this._popoverEl = popover;

        // Position near anchor
        this._positionPopover(anchorEl);

        // Show with animation
        requestAnimationFrame(() => {
            popover.classList.add('cea-citation-popover--visible');
        });

        // Click outside to dismiss
        this._clickOutsideHandler = (e) => {
            if (!popover.contains(e.target) && e.target !== anchorEl && !anchorEl.contains(e.target)) {
                this.hide();
            }
        };
        setTimeout(() => {
            document.addEventListener('click', this._clickOutsideHandler);
        }, 0);

        return popover;
    }

    /**
     * Position the popover below the anchor element.
     */
    _positionPopover(anchorEl) {
        if (!this._popoverEl || !anchorEl) return;

        const anchorRect = anchorEl.getBoundingClientRect();
        const scrollTop = window.scrollY || document.documentElement.scrollTop;
        const scrollLeft = window.scrollX || document.documentElement.scrollLeft;

        let top = anchorRect.bottom + scrollTop + 8;
        let left = anchorRect.left + scrollLeft;

        // Ensure it doesn't overflow the right edge
        const viewportWidth = document.documentElement.clientWidth;
        if (left + 400 > viewportWidth + scrollLeft) {
            left = viewportWidth + scrollLeft - 420;
        }

        // Ensure it doesn't go off-screen to the left
        if (left < scrollLeft + 8) {
            left = scrollLeft + 8;
        }

        this._popoverEl.style.top = `${top}px`;
        this._popoverEl.style.left = `${left}px`;
    }

    /**
     * Render the citation content in the popover.
     */
    _renderCitationContent(popover, citation) {
        // Header
        const header = popover.querySelector('.cea-citation-popover__header');
        header.innerHTML = '';
        if (citation.guide_name) {
            header.appendChild(createElement('span', {
                className: 'cea-citation-popover__guide-name',
                textContent: citation.guide_name,
            }));
        }
        if (citation.topic) {
            header.appendChild(createElement('span', {
                className: 'cea-citation-popover__topic',
                textContent: citation.topic,
            }));
        }

        // Body — excerpt text
        const body = popover.querySelector('.cea-citation-popover__body');
        body.innerHTML = '';
        if (citation.excerpt) {
            const excerptEl = createElement('div', {
                className: 'cea-citation-popover__excerpt',
            });
            excerptEl.textContent = citation.excerpt;
            body.appendChild(excerptEl);
        } else {
            body.appendChild(createElement('div', {
                className: 'cea-citation-popover__excerpt',
                textContent: 'No excerpt available for this rule.',
            }));
        }

        // Footer — page numbers
        const footer = popover.querySelector('.cea-citation-popover__footer');
        footer.innerHTML = '';
        if (citation.pages) {
            const pageBadge = createElement('span', {
                className: 'cea-citation-popover__page-badge',
            });
            pageBadge.innerHTML = `<i class="fas fa-file-lines"></i> p. ${escapeHtml(String(citation.pages))}`;
            footer.appendChild(pageBadge);
        }
    }

    /**
     * Hide and remove the popover.
     */
    hide() {
        if (this._popoverEl) {
            this._popoverEl.classList.remove('cea-citation-popover--visible');
            setTimeout(() => {
                if (this._popoverEl) {
                    this._popoverEl.remove();
                    this._popoverEl = null;
                }
            }, 250);
        }

        if (this._clickOutsideHandler) {
            document.removeEventListener('click', this._clickOutsideHandler);
            this._clickOutsideHandler = null;
        }

        this._currentRuleType = null;
    }
}
