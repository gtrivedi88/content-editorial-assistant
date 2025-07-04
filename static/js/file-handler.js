// File upload handling
function handleFileUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    showFileUploadProgress('analysis-results', file);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentContent = data.content;
            analyzeContent(data.content);
        } else {
            showError('analysis-results', data.error || 'Upload failed');
        }
    })
    .catch(error => {
        console.error('Upload error:', error);
        showError('analysis-results', 'Upload failed: ' + error.message);
    });
}

// Show file upload progress
function showFileUploadProgress(elementId, file) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const fileSize = (file.size / 1024).toFixed(1);
    const fileType = file.type || 'Unknown';
    
    element.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-upload me-2"></i>Processing Document
                    <span class="badge bg-info ms-2">Uploading</span>
                </h5>
            </div>
            <div class="card-body">
                <div class="text-center mb-4">
                    <div class="spinner-border text-info mb-3" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <h6 class="text-info">Extracting text from your document...</h6>
                </div>
                
                <div class="row">
                    <div class="col-md-6">
                        <h6><i class="fas fa-file me-2 text-primary"></i>File Information:</h6>
                        <ul class="list-unstyled small">
                            <li><strong>Name:</strong> ${file.name}</li>
                            <li><strong>Size:</strong> ${fileSize} KB</li>
                            <li><strong>Type:</strong> ${fileType}</li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6><i class="fas fa-cogs me-2 text-success"></i>Processing Steps:</h6>
                        <ul class="list-unstyled small text-muted">
                            <li><i class="fas fa-check text-success me-2"></i>File validation</li>
                            <li><i class="fas fa-spinner fa-spin text-info me-2"></i>Text extraction</li>
                            <li><i class="fas fa-circle text-muted me-2"></i>Content analysis</li>
                            <li><i class="fas fa-circle text-muted me-2"></i>Results display</li>
                        </ul>
                    </div>
                </div>
                
                <div class="alert alert-info mt-3">
                    <small>
                        <i class="fas fa-shield-alt me-2"></i>
                        <strong>Privacy:</strong> Your document is processed locally and never stored on our servers.
                    </small>
                </div>
            </div>
        </div>
    `;
}

// Content analysis
function analyzeContent(content, formatHint = 'auto') {
    showLoading('analysis-results', 'Starting analysis...');

    fetch('/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            content: content,
            format_hint: formatHint,
            session_id: sessionId 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            currentAnalysis = data.analysis;
            const structuralBlocks = data.structural_blocks || null;
            displayAnalysisResults(data.analysis, content, structuralBlocks);
        } else {
            showError('analysis-results', data.error || 'Analysis failed');
        }
    })
    .catch(error => {
        console.error('Analysis error:', error);
        showError('analysis-results', 'Analysis failed: ' + error.message);
    });
} 