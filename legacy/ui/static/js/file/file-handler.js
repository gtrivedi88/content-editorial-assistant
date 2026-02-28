/**
 * File Handler — upload via /upload, drag-drop, file picker.
 */

import { uploadFile } from '../state/actions.js';

const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.md', '.adoc', '.dita', '.xml', '.txt'];
const MAX_SIZE = 16 * 1024 * 1024; // 16MB

export class FileHandler {
    constructor(store, editorController) {
        this._store = store;
        this._editor = editorController;
        this._fileInput = document.getElementById('cea-file-input');

        this._bindEvents();
    }

    _bindEvents() {
        // File input change
        if (this._fileInput) {
            this._fileInput.addEventListener('change', (e) => {
                const file = e.target.files?.[0];
                if (file) this._handleFile(file);
                this._fileInput.value = ''; // reset for re-upload
            });
        }

        // Listen for drag-drop events from editor
        window.addEventListener('cea:file-drop', (e) => {
            const file = e.detail?.file;
            if (file) this._handleFile(file);
        });
    }

    openFilePicker() {
        if (this._fileInput) this._fileInput.click();
    }

    async _handleFile(file) {
        // Validate extension
        const ext = '.' + file.name.split('.').pop().toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
            alert(`Unsupported file type: ${ext}\nAllowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
            return;
        }

        // Validate size
        if (file.size > MAX_SIZE) {
            alert(`File too large: ${(file.size / 1024 / 1024).toFixed(1)}MB\nMaximum: 16MB`);
            return;
        }

        const result = await uploadFile(file);
        if (result?.content) {
            this._editor.setContent(result.content);
        }
    }
}
