/**
 * CEA Application Entry Point
 *
 * Initializes all modules based on the current page.
 * Uses ES6 modules — loaded via <script type="module"> in base.html.
 */

import { themeManager } from './shared/theme-manager.js';
import { store } from './state/store.js';
import { initSocketClient } from './services/socket-client.js';
import { EditorController } from './editor/editor-controller.js';
import { IssuePanel } from './issues/issue-panel.js';
import { ReportPanel } from './report/report-panel.js';
import { FileHandler } from './file/file-handler.js';
import { CitationPopover } from './citations/popover.js';
import { SuggestionPanel } from './suggestions/panel.js';

document.addEventListener('DOMContentLoaded', () => {
    // Theme (all pages)
    themeManager.init();

    // Socket (all pages — enables health checks, session persistence)
    initSocketClient(store);

    // Review page modules
    const editorEl = document.getElementById('cea-editor');
    if (editorEl) {
        const editor = new EditorController(editorEl, store);
        const issuePanel = new IssuePanel(
            document.getElementById('cea-issue-panel'),
            store,
            editor
        );
        const reportPanel = new ReportPanel(
            document.getElementById('cea-report-slideover'),
            store
        );
        const fileHandler = new FileHandler(store, editor);

        // Initialize citation popover and suggestion panel
        const citationPopover = new CitationPopover();
        const suggestionPanel = new SuggestionPanel(editor);

        // Content type badge — shows auto-detected type after analysis
        const contentTypeBadge = document.getElementById('cea-content-type-badge');
        if (contentTypeBadge) {
            store.subscribe('detectedContentType', (type) => {
                if (type) {
                    contentTypeBadge.textContent = type.charAt(0).toUpperCase() + type.slice(1);
                    contentTypeBadge.style.display = '';
                } else {
                    contentTypeBadge.style.display = 'none';
                }
            });
        }

        // Wire up toolbar buttons
        const uploadBtn = document.getElementById('cea-upload-btn');
        if (uploadBtn) {
            uploadBtn.addEventListener('click', () => fileHandler.openFilePicker());
        }

        const resetBtn = document.getElementById('cea-reset-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => editor.reset());
        }

        const reportBtn = document.getElementById('cea-report-btn');
        if (reportBtn) {
            reportBtn.addEventListener('click', () => reportPanel.open());
        }

        const reportCloseBtn = document.getElementById('cea-report-close');
        const reportBackBtn = document.getElementById('cea-report-back');
        const reportOverlay = document.getElementById('cea-report-overlay');
        if (reportCloseBtn) reportCloseBtn.addEventListener('click', () => reportPanel.close());
        if (reportBackBtn) reportBackBtn.addEventListener('click', () => reportPanel.close());
        if (reportOverlay) reportOverlay.addEventListener('click', () => reportPanel.close());

        // Escape key closes report and citation popover
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                reportPanel.close();
                citationPopover.hide();
            }
        });
    }

});
