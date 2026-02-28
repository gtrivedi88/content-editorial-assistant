/**
 * REST API Client — fetch wrappers for all /api/v1/ backend endpoints.
 * Includes AbortController for request cancellation on re-analysis.
 */

let currentAnalyzeController = null;

/**
 * POST /api/v1/analyze — analyze content.
 * Aborts any in-flight analysis request before starting a new one.
 */
export async function postAnalyze(content, formatHint, contentType, sessionId) {
    if (currentAnalyzeController) {
        currentAnalyzeController.abort();
    }
    currentAnalyzeController = new AbortController();

    const resp = await fetch('/api/v1/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            text: content,
            content_type: contentType || 'concept',
            format_hint: formatHint || 'auto',
            session_id: sessionId || '',
        }),
        signal: currentAnalyzeController.signal,
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * POST /api/v1/upload — upload a file for text extraction.
 */
export async function postUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const resp = await fetch('/api/v1/upload', {
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
 * POST /api/v1/suggestions — get an LLM rewrite suggestion for an issue.
 */
export async function fetchSuggestion(sessionId, issueId) {
    const resp = await fetch('/api/v1/suggestions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            issue_id: issueId,
        }),
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * GET /api/v1/citations/<ruleType> — get style guide citation excerpt.
 */
export async function fetchCitation(ruleType) {
    const resp = await fetch(`/api/v1/citations/${encodeURIComponent(ruleType)}`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * POST /api/v1/issues/<issueId>/feedback — submit user feedback.
 */
export async function submitFeedback(sessionId, issueId, ruleType, thumbsUp, comment) {
    const resp = await fetch(`/api/v1/issues/${encodeURIComponent(issueId)}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
            issue_id: issueId,
            rule_type: ruleType,
            thumbs_up: thumbsUp,
            comment: comment || '',
        }),
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * POST /api/v1/issues/<issueId>/accept — accept an issue fix.
 */
export async function acceptIssue(sessionId, issueId) {
    const resp = await fetch(`/api/v1/issues/${encodeURIComponent(issueId)}/accept`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
        }),
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * POST /api/v1/issues/<issueId>/dismiss — dismiss an issue.
 */
export async function dismissIssue(sessionId, issueId) {
    const resp = await fetch(`/api/v1/issues/${encodeURIComponent(issueId)}/dismiss`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            session_id: sessionId,
        }),
    });

    if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data.error || `HTTP ${resp.status}`);
    }

    return resp.json();
}

/**
 * POST /api/v1/report/pdf — generate and download a PDF report.
 */
export async function downloadPdfReport(analysis, content, structuralBlocks) {
    const resp = await fetch('/api/v1/report/pdf', {
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
