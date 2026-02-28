/**
 * Editor Controller — manages the contenteditable editor lifecycle.
 * Handles paste (with markup auto-detection), auto-analysis on paste,
 * and post-analysis rendering of structural blocks.
 */

import { store } from '../state/store.js';
import { analyzeContent, selectError } from '../state/actions.js';
import { renderUnderlines, clearUnderlines, setActiveUnderline, filterUnderlines } from './underline-renderer.js';
import { getPlainText, charSpanToDomRange } from './span-mapper.js';
import { SelectionTracker } from './selection-tracker.js';
import { MarginLabels } from './margin-labels.js';
import { debounce, escapeHtml } from '../shared/dom-utils.js';
import { detectFormatFromContent } from '../file/format-detector.js';

export class EditorController {
    constructor(editorEl, storeRef) {
        this._editor = editorEl;
        this._store = storeRef;
        this._selection = new SelectionTracker(editorEl);
        this._wordCountEl = document.getElementById('cea-word-count');
        this._rawContent = ''; // stores raw markup for analysis
        this._autoAnalysisTimer = null;

        // Initialize margin labels
        const marginContainer = document.getElementById('cea-margin-labels');
        if (marginContainer) {
            this._marginLabels = new MarginLabels(editorEl, marginContainer, storeRef);
        }

        this._bindEvents();
        this._bindStoreSubscriptions();
    }

    _bindEvents() {
        // Input: update word count and content in store
        this._editor.addEventListener('input', debounce(() => {
            this._updateContent();
        }, 300));

        // Paste: detect markup format, handle accordingly, then auto-analyze
        this._editor.addEventListener('paste', (e) => {
            e.preventDefault();
            const html = e.clipboardData.getData('text/html');
            const text = e.clipboardData.getData('text/plain');

            // Get the raw text content for format detection
            const rawText = text || '';
            const detection = detectFormatFromContent(rawText);

            if (detection && detection.format !== 'plaintext') {
                // Markup detected — paste as plain monospace text (not HTML)
                // Store raw markup for sending to backend
                this._rawContent = rawText;
                this._editor.textContent = rawText;
                this._editor.classList.add('cea-editor-content--markup');
                this._store.setState({
                    formatHint: detection.format,
                    detectedFormat: detection,
                });
            } else if (html) {
                // Regular HTML paste — sanitize and preserve structure
                this._editor.classList.remove('cea-editor-content--markup');
                this._rawContent = '';
                const temp = document.createElement('div');
                temp.innerHTML = html;
                temp.querySelectorAll('script,style,link,meta,iframe,object,embed').forEach(el => el.remove());
                temp.querySelectorAll('*').forEach(el => {
                    const tag = el.tagName.toLowerCase();
                    const allowed = ['p','h1','h2','h3','h4','h5','h6','ul','ol','li','br','strong','b','em','i','code','pre','blockquote','a','span','div','table','tr','td','th','thead','tbody'];
                    if (!allowed.includes(tag)) {
                        el.replaceWith(...el.childNodes);
                    } else {
                        [...el.attributes].forEach(attr => {
                            if (!(tag === 'a' && attr.name === 'href')) {
                                el.removeAttribute(attr.name);
                            }
                        });
                    }
                });
                document.execCommand('insertHTML', false, temp.innerHTML);
                this._store.setState({ formatHint: 'auto', detectedFormat: null });
            } else if (rawText) {
                // Plain text paste — convert to paragraphs
                this._editor.classList.remove('cea-editor-content--markup');
                this._rawContent = '';
                const paragraphs = rawText.split(/\n\s*\n/).filter(p => p.trim());
                if (paragraphs.length > 1) {
                    const pHtml = paragraphs.map(p => `<p>${escapeHtml(p).replace(/\n/g, '<br>')}</p>`).join('');
                    document.execCommand('insertHTML', false, pHtml);
                } else {
                    document.execCommand('insertText', false, rawText);
                }
                this._store.setState({ formatHint: 'auto', detectedFormat: null });
            }

            setTimeout(() => {
                this._updateContent();
                this._scheduleAutoAnalysis();
            }, 50);
        });

        // Click on underlines
        this._editor.addEventListener('click', (e) => {
            const underline = e.target.closest('.cea-underline');
            if (underline) {
                e.stopPropagation();
                selectError(underline.dataset.errorId);
            }
        });

        // Keyboard on underlines
        this._editor.addEventListener('keydown', (e) => {
            if ((e.key === 'Enter' || e.key === ' ') && e.target.classList?.contains('cea-underline')) {
                e.preventDefault();
                selectError(e.target.dataset.errorId);
            }
        });

        // Drag and drop
        const panel = this._editor.closest('.cea-editor-panel');
        const dropzone = document.getElementById('cea-dropzone');

        if (panel && dropzone) {
            panel.addEventListener('dragenter', (e) => {
                e.preventDefault();
                dropzone.classList.add('cea-dropzone--active', 'cea-dropzone--dragover');
            });
            dropzone.addEventListener('dragleave', (e) => {
                if (!dropzone.contains(e.relatedTarget)) {
                    dropzone.classList.remove('cea-dropzone--active', 'cea-dropzone--dragover');
                }
            });
            dropzone.addEventListener('dragover', (e) => e.preventDefault());
            dropzone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropzone.classList.remove('cea-dropzone--active', 'cea-dropzone--dragover');
                const file = e.dataTransfer?.files?.[0];
                if (file) {
                    globalThis.dispatchEvent(new CustomEvent('cea:file-drop', { detail: { file } }));
                }
            });
        }
    }

    /**
     * Schedule auto-analysis after paste with 800ms debounce.
     * Only triggers if there's enough content (5+ words).
     */
    _scheduleAutoAnalysis() {
        if (this._autoAnalysisTimer) clearTimeout(this._autoAnalysisTimer);
        const text = this._rawContent || getPlainText(this._editor);
        if (!text.trim() || text.trim().split(/\s+/).length < 5) return;
        this._autoAnalysisTimer = setTimeout(() => {
            this.triggerAnalysis();
        }, 800);
    }

    _bindStoreSubscriptions() {
        // After analysis completes, apply code block styling then render underlines
        this._store.subscribe('analysisStatus', (status) => {
            if (status === 'complete') {
                // Style code block regions before rendering underlines
                const codeRanges = this._store.get('codeBlockRanges') || [];
                if (codeRanges.length > 0) {
                    this._renderCodeBlockRegions(codeRanges);
                }
                this._editor.contentEditable = 'true';
            } else if (status === 'analyzing') {
                this._editor.contentEditable = 'false';
            } else {
                this._editor.contentEditable = 'true';
            }
        });

        // Render underlines when errors change — editor keeps raw text
        this._store.subscribe('errors', (errors) => {
            if (this._store.get('analysisStatus') === 'complete' && errors.length > 0) {
                clearUnderlines(this._editor);
                renderUnderlines(this._editor, errors);
            }
        });

        // Highlight active underline
        this._store.subscribe('selectedErrorId', (errorId) => {
            const mark = setActiveUnderline(this._editor, errorId);
            if (mark) mark.scrollIntoView({ behavior: 'smooth', block: 'center' });
        });

        // Filter underlines by group
        this._store.subscribe('activeGroup', (group) => {
            filterUnderlines(this._editor, group);
        });
    }

    _updateContent() {
        const text = getPlainText(this._editor);
        this._store.setState({ content: this._rawContent || text });

        const words = text.trim() ? text.trim().split(/\s+/).length : 0;
        const chars = text.length;
        if (this._wordCountEl) {
            this._wordCountEl.textContent = `${words} word${words !== 1 ? 's' : ''} \u00b7 ${chars.toLocaleString()} characters`;
        }
    }

    /**
     * Apply visual styling to code block regions in the raw text editor.
     * Wraps code block character ranges in <span class="cea-code-region">.
     * Applied before underline rendering so underlines don't land inside code blocks.
     */
    _renderCodeBlockRegions(ranges) {
        if (!ranges || ranges.length === 0) return;

        // Remove any existing code regions first
        const existing = this._editor.querySelectorAll('.cea-code-region');
        for (const el of existing) {
            const parent = el.parentNode;
            while (el.firstChild) parent.insertBefore(el.firstChild, el);
            parent.removeChild(el);
            parent.normalize();
        }

        // Apply from last-to-first to preserve offsets
        const sorted = [...ranges].sort((a, b) => b.start_pos - a.start_pos);
        for (const range of sorted) {
            const domRange = charSpanToDomRange(this._editor, range.start_pos, range.end_pos);
            if (!domRange) continue;

            try {
                const span = document.createElement('span');
                span.className = 'cea-code-region';
                domRange.surroundContents(span);
            } catch {
                // surroundContents fails on partial element selections — skip
                try {
                    const span = document.createElement('span');
                    span.className = 'cea-code-region';
                    const fragment = domRange.extractContents();
                    span.appendChild(fragment);
                    domRange.insertNode(span);
                } catch {
                    // Unable to wrap this range
                }
            }
        }
    }

    _renderErrors(errors) {
        this._selection.save();
        clearUnderlines(this._editor);
        if (errors.length > 0) {
            renderUnderlines(this._editor, errors);
        }
        this._selection.restore();
    }

    setContent(text) {
        this._rawContent = '';
        this._editor.textContent = text;
        this._editor.classList.remove('cea-editor-content--markup');
        this._updateContent();
    }

    getContent() {
        return this._rawContent || getPlainText(this._editor);
    }

    triggerAnalysis() {
        const text = this._rawContent || getPlainText(this._editor);
        if (!text.trim()) return;
        this._store.setState({ content: text });
        clearUnderlines(this._editor);
        analyzeContent();
    }

    reset() {
        clearUnderlines(this._editor);
        this._editor.textContent = '';
        this._editor.classList.remove('cea-editor-content--markup');
        this._rawContent = '';
        if (this._autoAnalysisTimer) clearTimeout(this._autoAnalysisTimer);
        this._store.setState({
            content: '',
            formatHint: 'auto',
            detectedFormat: null,
            analysisStatus: 'idle',
            analysisResult: null,
            errors: [],
            filteredErrors: [],
            structuralBlocks: [],
            readability: null,
            statistics: null,
            selectedErrorId: null,
            activeGroup: 'all',
            dismissedErrors: new Set(),
            resolvedErrors: new Set(),
            progressSteps: [],
            progressPercent: 0,
            qualityScore: 0,
            errorMessage: null,
        });
        this._updateContent();
    }

    getEditorElement() {
        return this._editor;
    }
}
