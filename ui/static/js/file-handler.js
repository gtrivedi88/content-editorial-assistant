// Enhanced file upload handling with PatternFly components
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

// Enhanced file upload progress with PatternFly components
function showFileUploadProgress(elementId, file) {
    const element = document.getElementById(elementId);
    if (!element) return;

    const fileSize = (file.size / 1024).toFixed(1);
    const fileType = file.type || 'Unknown';
    const fileExtension = file.name.split('.').pop().toUpperCase();
    
    element.innerHTML = `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h2 class="pf-v5-c-title pf-m-xl">
                        <i class="fas fa-upload pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                        Processing Document
                    </h2>
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-blue">
                        <span class="pf-v5-c-label__content">
                            <i class="fas fa-spinner fa-spin pf-v5-c-label__icon"></i>
                            Uploading
                        </span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <!-- Progress Center -->
                <div class="pf-v5-c-empty-state pf-m-lg">
                    <div class="pf-v5-c-empty-state__content">
                        <div class="pf-v5-c-empty-state__icon">
                            <span class="pf-v5-c-spinner pf-m-xl pulse" role="status" aria-label="Processing">
                                <span class="pf-v5-c-spinner__clipper"></span>
                                <span class="pf-v5-c-spinner__lead-ball"></span>
                                <span class="pf-v5-c-spinner__tail-ball"></span>
                            </span>
                        </div>
                        <h2 class="pf-v5-c-title pf-m-lg">Extracting text from your document</h2>
                        <div class="pf-v5-c-empty-state__body">
                            <p class="pf-v5-u-mb-lg">Please wait while we process your ${fileExtension} file...</p>
                        </div>
                    </div>
                </div>
                
                <!-- File Information Grid -->
                <div class="pf-v5-l-grid pf-m-gutter pf-v5-u-mt-lg">
                    <div class="pf-v5-l-grid__item pf-m-6-col">
                        <div class="pf-v5-c-card pf-m-plain pf-m-bordered">
                            <div class="pf-v5-c-card__header">
                                <div class="pf-v5-c-card__header-main">
                                    <h3 class="pf-v5-c-title pf-m-md">
                                        <i class="fas fa-file pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                                        File Information
                                    </h3>
                                </div>
                            </div>
                            <div class="pf-v5-c-card__body">
                                <dl class="pf-v5-c-description-list pf-m-horizontal">
                                    <div class="pf-v5-c-description-list__group">
                                        <dt class="pf-v5-c-description-list__term">
                                            <span class="pf-v5-c-description-list__text">Name</span>
                                        </dt>
                                        <dd class="pf-v5-c-description-list__description">
                                            <div class="pf-v5-c-description-list__text">${file.name}</div>
                                        </dd>
                                    </div>
                                    <div class="pf-v5-c-description-list__group">
                                        <dt class="pf-v5-c-description-list__term">
                                            <span class="pf-v5-c-description-list__text">Size</span>
                                        </dt>
                                        <dd class="pf-v5-c-description-list__description">
                                            <div class="pf-v5-c-description-list__text">${fileSize} KB</div>
                                        </dd>
                                    </div>
                                    <div class="pf-v5-c-description-list__group">
                                        <dt class="pf-v5-c-description-list__term">
                                            <span class="pf-v5-c-description-list__text">Type</span>
                                        </dt>
                                        <dd class="pf-v5-c-description-list__description">
                                            <div class="pf-v5-c-description-list__text">${fileExtension}</div>
                                        </dd>
                                    </div>
                                </dl>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-l-grid__item pf-m-6-col">
                        <div class="pf-v5-c-card pf-m-plain pf-m-bordered">
                            <div class="pf-v5-c-card__header">
                                <div class="pf-v5-c-card__header-main">
                                    <h3 class="pf-v5-c-title pf-m-md">
                                        <i class="fas fa-cogs pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                        Processing Steps
                                    </h3>
                                </div>
                            </div>
                            <div class="pf-v5-c-card__body">
                                <div class="pf-v5-l-stack pf-m-gutter">
                                    <div class="pf-v5-l-stack__item">
                                        <div class="pf-v5-l-flex pf-m-align-items-center">
                                            <div class="pf-v5-l-flex__item">
                                                <i class="fas fa-check" style="color: var(--app-success-color);"></i>
                                            </div>
                                            <div class="pf-v5-l-flex__item pf-v5-u-ml-sm">
                                                <span class="pf-v5-u-font-size-sm">File validation</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="pf-v5-l-stack__item">
                                        <div class="pf-v5-l-flex pf-m-align-items-center">
                                            <div class="pf-v5-l-flex__item">
                                                <span class="pf-v5-c-spinner pf-m-sm" role="status">
                                                    <span class="pf-v5-c-spinner__clipper"></span>
                                                    <span class="pf-v5-c-spinner__lead-ball"></span>
                                                    <span class="pf-v5-c-spinner__tail-ball"></span>
                                                </span>
                                            </div>
                                            <div class="pf-v5-l-flex__item pf-v5-u-ml-sm">
                                                <span class="pf-v5-u-font-size-sm" style="color: var(--app-primary-color);">Text extraction</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="pf-v5-l-stack__item">
                                        <div class="pf-v5-l-flex pf-m-align-items-center">
                                            <div class="pf-v5-l-flex__item">
                                                <i class="fas fa-circle" style="color: var(--pf-v5-global--Color--200);"></i>
                                            </div>
                                            <div class="pf-v5-l-flex__item pf-v5-u-ml-sm">
                                                <span class="pf-v5-u-font-size-sm pf-v5-u-color-200">Content analysis</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div class="pf-v5-l-stack__item">
                                        <div class="pf-v5-l-flex pf-m-align-items-center">
                                            <div class="pf-v5-l-flex__item">
                                                <i class="fas fa-circle" style="color: var(--pf-v5-global--Color--200);"></i>
                                            </div>
                                            <div class="pf-v5-l-flex__item pf-v5-u-ml-sm">
                                                <span class="pf-v5-u-font-size-sm pf-v5-u-color-200">Results display</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Privacy Notice -->
                <div class="pf-v5-u-mt-lg">
                    <div class="pf-v5-c-alert pf-m-info pf-m-inline">
                        <div class="pf-v5-c-alert__icon">
                            <i class="fas fa-shield-alt"></i>
                        </div>
                        <h4 class="pf-v5-c-alert__title">Privacy Protected</h4>
                        <div class="pf-v5-c-alert__description">
                            Your document is processed securely and never stored on our servers. All analysis happens in real-time.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Enhanced content analysis with better progress tracking
function analyzeContent(content, formatHint = 'auto') {
    const analysisStartTime = performance.now(); // Track client-side timing
    
    showLoading('analysis-results', 'Starting comprehensive analysis...');

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
            const analysisEndTime = performance.now();
            const clientProcessingTime = (analysisEndTime - analysisStartTime) / 1000; // Convert to seconds
            
            // Store analysis data globally
            currentAnalysis = data.analysis;
            
            // Add timing information to currentAnalysis
            currentAnalysis.client_processing_time = clientProcessingTime;
            currentAnalysis.server_processing_time = data.processing_time || data.analysis.processing_time;
            currentAnalysis.total_round_trip_time = clientProcessingTime;
            
            // Display results
            const structuralBlocks = data.structural_blocks || null;
            displayAnalysisResults(data.analysis, content, structuralBlocks);
            
            // Log performance metrics for debugging
            console.log('Analysis Performance:', {
                server_time: currentAnalysis.server_processing_time,
                client_time: clientProcessingTime,
                total_time: clientProcessingTime
            });
        } else {
            showError('analysis-results', data.error || 'Analysis failed');
        }
    })
    .catch(error => {
        console.error('Analysis error:', error);
        showError('analysis-results', 'Analysis failed: ' + error.message);
    });
} 