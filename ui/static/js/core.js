// Global variables
let currentAnalysis = null;
let currentContent = null;
let socket = null;
let sessionId = null;

// Initialize application when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSocket();
    initializeTooltips();
    initializeFileHandlers();
    initializeInteractivity();
});

// Initialize tooltips
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize file upload handlers
function initializeFileHandlers() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    const textInput = document.getElementById('text-input');

    if (uploadArea && fileInput) {
        // Drag and drop functionality
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
                hideSampleSection();
            }
        });

        // File input change handler
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
                hideSampleSection();
            }
        });

        // Clear text input when file is selected
        fileInput.addEventListener('change', () => {
            if (textInput) textInput.value = '';
        });
    }

    if (textInput) {
        // Clear file input when text is entered
        textInput.addEventListener('input', () => {
            if (fileInput) fileInput.value = '';
        });

        // Auto-resize textarea
        textInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = this.scrollHeight + 'px';
        });
    }
}

// Initialize interactive elements
function initializeInteractivity() {
    // Add hover effects to cards
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

// Direct text analysis
function analyzeDirectText() {
    const textInput = document.getElementById('text-input');
    if (!textInput) return;

    const text = textInput.value.trim();
    if (!text) {
        alert('Please enter some text to analyze');
        return;
    }

    currentContent = text;
    analyzeContent(text);
    hideSampleSection();
}

// Sample text analysis
function analyzeSampleText() {
    const sampleText = `The implementation of the new system was facilitated by the team in order to optimize performance metrics. Due to the fact that the previous system was inefficient, a large number of users were experiencing difficulties. The decision was made by management to utilize advanced technologies for the purpose of enhancing user experience and improving overall system reliability.`;
    
    currentContent = sampleText;
    analyzeContent(sampleText);
    hideSampleSection();
}

// Hide sample section when analysis starts
function hideSampleSection() {
    const sampleSection = document.getElementById('sample-section');
    if (sampleSection) {
        sampleSection.style.display = 'none';
    }
}

// Enhanced rewrite content function with assembly line support
function rewriteContent() {
    if (!currentContent || !currentAnalysis) {
        alert('Please analyze content first');
        return;
    }

    // Initialize progressive rewrite UI
    initializeProgressiveRewriteUI();
    
    fetch('/rewrite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            content: currentContent,
            errors: currentAnalysis.errors || [],
            session_id: sessionId,
            use_assembly_line: true  // Request assembly line processing
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.assembly_line_used) {
                displayAssemblyLineResults(data);
            } else {
                displayRewriteResults(data);
            }
        } else {
            showError('rewrite-results', data.error || 'Rewrite failed');
        }
    })
    .catch(error => {
        console.error('Rewrite error:', error);
        showError('rewrite-results', 'Rewrite failed: ' + error.message);
    });
}

function initializeProgressiveRewriteUI() {
    const rewriteContainer = document.getElementById('rewrite-results');
    if (!rewriteContainer) return;
    
    // Show assembly line progress interface
    rewriteContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-c-card app-card">
                    <div class="pf-v5-c-card__header">
                        <div class="pf-v5-c-card__header-main">
                            <h2 class="pf-v5-c-title pf-m-xl">
                                <i class="fas fa-industry pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                                Assembly Line AI Rewriting
                            </h2>
                        </div>
                        <div class="pf-v5-c-card__actions">
                            <span class="pf-v5-c-label pf-m-blue">
                                <span class="pf-v5-c-label__content">
                                    <i class="fas fa-cogs pf-v5-c-label__icon"></i>
                                    Processing
                                </span>
                            </span>
                        </div>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <div class="assembly-line-progress">
                            <div class="progress-header">
                                <div class="progress-info">
                                    <span class="pass-indicator">Starting assembly line...</span>
                                    <span class="errors-indicator">${currentAnalysis.errors.length} errors to fix</span>
                                </div>
                                <div class="progress-bar-container">
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: 5%"></div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="assembly-stations" id="assembly-stations">
                                <div class="station pending" data-priority="urgent">
                                    <div class="station-header">
                                        <i class="fas fa-exclamation-triangle station-icon"></i>
                                        <span class="station-name">Critical/Legal Pass</span>
                                        <span class="station-status">Pending</span>
                                    </div>
                                    <div class="station-details">
                                        <span class="error-count">Checking for critical issues...</span>
                                    </div>
                                </div>
                                
                                <div class="station pending" data-priority="high">
                                    <div class="station-header">
                                        <i class="fas fa-building station-icon"></i>
                                        <span class="station-name">Structural Pass</span>
                                        <span class="station-status">Pending</span>
                                    </div>
                                    <div class="station-details">
                                        <span class="error-count">Waiting for structure fixes...</span>
                                    </div>
                                </div>
                                
                                <div class="station pending" data-priority="medium">
                                    <div class="station-header">
                                        <i class="fas fa-spell-check station-icon"></i>
                                        <span class="station-name">Grammar Pass</span>
                                        <span class="station-status">Pending</span>
                                    </div>
                                    <div class="station-details">
                                        <span class="error-count">Waiting for grammar fixes...</span>
                                    </div>
                                </div>
                                
                                <div class="station pending" data-priority="low">
                                    <div class="station-header">
                                        <i class="fas fa-paint-brush station-icon"></i>
                                        <span class="station-name">Style Pass</span>
                                        <span class="station-status">Pending</span>
                                    </div>
                                    <div class="station-details">
                                        <span class="error-count">Waiting for style improvements...</span>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="content-preview" id="content-preview">
                                <h4>Content Being Processed</h4>
                                <div class="preview-text" id="preview-text">
                                    ${escapeHtml(currentContent.substring(0, 200))}${currentContent.length > 200 ? '...' : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function displayAssemblyLineResults(data) {
    const rewriteContainer = document.getElementById('rewrite-results');
    if (!rewriteContainer) return;
    
    // Store the rewritten content globally for copying
    window.currentRewrittenContent = data.rewritten_text || data.rewritten || '';
    
    const errorsFixed = data.errors_fixed || 0;
    const totalErrors = data.original_errors || 0;
    const improvements = data.improvements || [];
    
    rewriteContainer.innerHTML = `
        <div class="pf-v5-l-grid pf-m-gutter">
            <div class="pf-v5-l-grid__item pf-m-12-col">
                <div class="pf-v5-c-card app-card">
                    <div class="pf-v5-c-card__header">
                        <div class="pf-v5-c-card__header-main">
                            <h2 class="pf-v5-c-title pf-m-xl">
                                <i class="fas fa-industry pf-v5-u-mr-sm" style="color: var(--app-success-color);"></i>
                                Assembly Line Results
                            </h2>
                        </div>
                        <div class="pf-v5-c-card__actions">
                            <div class="pf-v5-l-flex pf-m-space-items-sm">
                                <div class="pf-v5-l-flex__item">
                                    <span class="pf-v5-c-label pf-m-green">
                                        <span class="pf-v5-c-label__content">
                                            <i class="fas fa-check-circle pf-v5-c-label__icon"></i>
                                            ${errorsFixed}/${totalErrors} Fixed
                                        </span>
                                    </span>
                                </div>
                                <div class="pf-v5-l-flex__item">
                                    <button class="pf-v5-c-button pf-m-secondary" type="button" onclick="refineContent()">
                                        <i class="fas fa-star pf-v5-u-mr-xs"></i>
                                        Refine Further
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div class="pf-v5-c-card__body">
                        <!-- Assembly Line Statistics -->
                        <div class="assembly-summary pf-v5-u-mb-lg">
                            <div class="pf-v5-l-flex pf-m-space-items-md pf-m-justify-content-space-between">
                                <div class="stat-item">
                                    <span class="stat-label">Passes Completed</span>
                                    <span class="stat-value">${data.passes_completed || 0}</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Precision Rate</span>
                                    <span class="stat-value">${Math.round((errorsFixed / Math.max(1, totalErrors)) * 100)}%</span>
                                </div>
                                <div class="stat-item">
                                    <span class="stat-label">Confidence</span>
                                    <span class="stat-value">${Math.round((data.confidence || 0) * 100)}%</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Improved Content -->
                        <div class="pf-v5-c-code-block">
                            <div class="pf-v5-c-code-block__header">
                                <div class="pf-v5-c-code-block__header-main">
                                    <span class="pf-v5-c-code-block__title">Assembly Line Improved Content</span>
                                </div>
                                <div class="pf-v5-c-code-block__actions">
                                    <button class="pf-v5-c-button pf-m-plain pf-m-small" type="button" onclick="copyRewrittenContent()">
                                        <i class="fas fa-copy" aria-hidden="true"></i>
                                    </button>
                                </div>
                            </div>
                            <div class="pf-v5-c-code-block__content">
                                <pre class="pf-v5-c-code-block__pre" style="white-space: pre-wrap; word-wrap: break-word;"><code class="pf-v5-c-code-block__code">${escapeHtml(window.currentRewrittenContent)}</code></pre>
                            </div>
                        </div>
                        
                        <!-- Assembly Line Improvements -->
                        ${improvements.length > 0 ? `
                            <div class="pf-v5-u-mt-lg">
                                <h3 class="pf-v5-c-title pf-m-lg pf-v5-u-mb-sm">Assembly Line Improvements</h3>
                                <div class="pf-v5-l-stack pf-m-gutter">
                                    ${improvements.map(improvement => `
                                        <div class="pf-v5-l-stack__item">
                                            <div class="pf-v5-c-alert pf-m-success pf-m-inline">
                                                <div class="pf-v5-c-alert__icon">
                                                    <i class="fas fa-cogs"></i>
                                                </div>
                                                <div class="pf-v5-c-alert__title">
                                                    ${improvement}
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;

    rewriteContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    
    // Show success notification
    showNotification(`Assembly line processing complete! Fixed ${errorsFixed} out of ${totalErrors} errors with surgical precision.`, 'success');
}

// Handle assembly line progress updates via WebSocket
function handleAssemblyLineProgress(data) {
    const stationElement = document.querySelector(`[data-priority="${data.priority}"]`);
    if (!stationElement) return;
    
    // Update station status
    stationElement.classList.remove('pending', 'processing', 'completed');
    stationElement.classList.add(data.status);
    
    const statusElement = stationElement.querySelector('.station-status');
    const detailsElement = stationElement.querySelector('.error-count');
    
    if (data.status === 'processing') {
        statusElement.textContent = 'Processing...';
        detailsElement.textContent = data.detail || 'Working on fixes...';
        stationElement.querySelector('.station-icon').classList.add('fa-spin');
    } else if (data.status === 'completed') {
        statusElement.textContent = 'Completed';
        detailsElement.textContent = data.result || 'Pass completed successfully';
        stationElement.querySelector('.station-icon').classList.remove('fa-spin');
    }
    
    // Update overall progress
    updateAssemblyLineProgress(data.progress || 0);
}

function updateAssemblyLineProgress(progress) {
    const progressFill = document.querySelector('.progress-fill');
    const progressInfo = document.querySelector('.pass-indicator');
    
    if (progressFill) {
        progressFill.style.width = `${progress}%`;
    }
    
    if (progressInfo) {
        if (progress < 25) {
            progressInfo.textContent = 'Critical/Legal Pass in progress...';
        } else if (progress < 50) {
            progressInfo.textContent = 'Structural Pass in progress...';
        } else if (progress < 75) {
            progressInfo.textContent = 'Grammar Pass in progress...';
        } else if (progress < 100) {
            progressInfo.textContent = 'Style Pass in progress...';
        } else {
            progressInfo.textContent = 'Assembly line complete!';
        }
    }
}

// Refine content function (Pass 2)
function refineContent(firstPassResult) {
    // Use the global currentRewrittenContent if no parameter provided
    const contentToRefine = firstPassResult || window.currentRewrittenContent;
    
    if (!contentToRefine || !currentAnalysis) {
        alert('No first pass result available');
        return;
    }

    showLoading('rewrite-results', 'Refining with AI Pass 2...');

    fetch('/refine', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            first_pass_result: contentToRefine,
            original_errors: currentAnalysis.errors || [],
            session_id: sessionId 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayRefinementResults(data);
        } else {
            showError('rewrite-results', data.error || 'Refinement failed');
        }
    })
    .catch(error => {
        console.error('Refinement error:', error);
        showError('rewrite-results', 'Refinement failed: ' + error.message);
    });
} 