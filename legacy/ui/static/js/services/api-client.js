/**
 * REST API Client — fetch wrappers for all backend endpoints.
 */

/**
 * POST /analyze — analyze content.
 */
export async function postAnalyze(content, formatHint, contentType, sessionId) {
    const resp = await fetch('/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            content,
            format_hint: formatHint || 'auto',
            content_type: contentType || 'concept',
            session_id: sessionId || '',
            include_confidence_details: true,
            skip_content_validation: true,
        }),
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * POST /upload — upload a file for text extraction.
 */
export async function postUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const resp = await fetch('/upload', {
        method: 'POST',
        body: formData,
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * POST /generate-pdf-report — generate and download a PDF report.
 */
export async function downloadPdfReport(analysis, content, structuralBlocks) {
    const resp = await fetch('/generate-pdf-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            analysis,
            content,
            structural_blocks: structuralBlocks,
            report_type: 'full',
        }),
    });

    if (!resp.ok) {
        throw new Error(`PDF generation failed: HTTP ${resp.status}`);
    }

    // Download the PDF blob
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cea_report_${new Date().toISOString().slice(0, 10)}.pdf`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * POST /api/feedback — submit user feedback.
 */
export async function postFeedback(data) {
    const resp = await fetch('/api/feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });

    if (!resp.ok) {
        const result = await resp.json().catch(() => ({}));
        throw new Error(result.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

