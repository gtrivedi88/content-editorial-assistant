/**
 * Selection Tracker — tracks cursor position in the contenteditable editor.
 */

export class SelectionTracker {
    constructor(editorEl) {
        this._editor = editorEl;
        this._savedRange = null;
    }

    /**
     * Save the current selection/cursor position.
     */
    save() {
        const sel = window.getSelection();
        if (sel.rangeCount > 0 && this._editor.contains(sel.anchorNode)) {
            this._savedRange = sel.getRangeAt(0).cloneRange();
        }
    }

    /**
     * Restore the previously saved selection.
     */
    restore() {
        if (this._savedRange) {
            const sel = window.getSelection();
            sel.removeAllRanges();
            try {
                sel.addRange(this._savedRange);
            } catch (e) {
                // Range may be invalid if DOM changed
            }
        }
    }

    /**
     * Get the current cursor character offset in plain text.
     */
    getCursorOffset() {
        const sel = window.getSelection();
        if (!sel.rangeCount || !this._editor.contains(sel.anchorNode)) return -1;

        const range = document.createRange();
        range.selectNodeContents(this._editor);
        range.setEnd(sel.anchorNode, sel.anchorOffset);
        return range.toString().length;
    }
}
