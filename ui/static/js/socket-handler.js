// Initialize Socket.IO connection
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
    });
    
    socket.on('session_id', function(data) {
        sessionId = data.session_id;
        console.log('Session ID received:', sessionId);
    });
    
    socket.on('progress_update', function(data) {
        handleProgressUpdate(data);
    });
    
    socket.on('process_complete', function(data) {
        handleProcessComplete(data);
    });
    
    // BLOCK-LEVEL REWRITING WEBSOCKET HANDLERS
    socket.on('block_processing_start', function(data) {
        handleBlockProcessingStart(data);
    });
    
    socket.on('station_progress_update', function(data) {
        handleStationProgressUpdate(data);
    });
    
    socket.on('block_processing_complete', function(data) {
        handleBlockProcessingComplete(data);
    });
    
    socket.on('block_processing_error', function(data) {
        handleBlockProcessingError(data);
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
}

// Handle real-time progress updates with PatternFly components
function handleProgressUpdate(data) {
    console.log('Progress update:', data);
    
    const statusElement = document.getElementById('current-status');
    const detailElement = document.getElementById('status-detail');
    
    if (statusElement && detailElement) {
        statusElement.textContent = data.status;
        detailElement.textContent = data.detail;
    }
    
    // Update step indicators based on actual progress
    updateStepIndicators(data.step, data.progress);
}

// Update step indicators using PatternFly progress components
function updateStepIndicators(currentStep, progress) {
    const stepMapping = {
        'analysis_start': 'step-analysis',
        'structural_parsing': 'step-analysis',
        'spacy_processing': 'step-analysis',
        'block_mapping': 'step-analysis',
        'metrics_calculation': 'step-analysis',
        'analysis_complete': 'step-analysis',
        'rewrite_start': 'step-analysis',
        'pass1_start': 'step-pass1',
        'pass1_processing': 'step-pass1',
        'pass1_complete': 'step-pass1',
        'pass2_start': 'step-pass2',
        'pass2_processing': 'step-pass2',
        'validation': 'step-complete',
        'rewrite_complete': 'step-complete'
    };
    
    const targetStepId = stepMapping[currentStep];
    if (!targetStepId) return;
    
    // Mark previous steps as complete
    const allSteps = document.querySelectorAll('.step-item');
    let foundTarget = false;
    
    allSteps.forEach((step) => {
        const stepId = step.id;
        
        if (stepId === targetStepId) {
            foundTarget = true;
            // Mark current step as active
            step.classList.remove('completed', 'pf-m-success');
            step.classList.add('active', 'pf-m-info');
            const icon = step.querySelector('.step-icon');
            if (currentStep.includes('complete')) {
                // Step is complete
                step.classList.remove('active', 'pf-m-info');
                step.classList.add('completed', 'pf-m-success');
                icon.innerHTML = '<i class="fas fa-check-circle" style="color: var(--app-success-color);"></i>';
            } else {
                // Step is in progress
                icon.innerHTML = `
                    <span class="pf-v5-c-spinner pf-m-sm" role="status">
                        <span class="pf-v5-c-spinner__clipper"></span>
                        <span class="pf-v5-c-spinner__lead-ball"></span>
                        <span class="pf-v5-c-spinner__tail-ball"></span>
                    </span>
                `;
            }
        } else if (!foundTarget) {
            // Mark previous steps as complete
            step.classList.remove('active', 'pf-m-info');
            step.classList.add('completed', 'pf-m-success');
            const icon = step.querySelector('.step-icon');
            icon.innerHTML = '<i class="fas fa-check-circle" style="color: var(--app-success-color);"></i>';
        } else {
            // Mark future steps as pending
            step.classList.remove('active', 'completed', 'pf-m-info', 'pf-m-success');
            const icon = step.querySelector('.step-icon');
            icon.innerHTML = '<i class="fas fa-circle" style="color: var(--pf-v5-global--Color--200);"></i>';
        }
    });
}

// Handle process completion
function handleProcessComplete(data) {
    console.log('Process complete:', data);
    
    if (data.success && data.data) {
        // Display results based on the type of process
        if (data.data.analysis) {
            // Analysis completed
            currentAnalysis = data.data.analysis;
            const structuralBlocks = data.data.structural_blocks || null;
            displayAnalysisResults(data.data.analysis, currentContent, structuralBlocks);
        } else if (data.data.rewritten_text) {
            // Rewrite completed
            displayRewriteResults(data.data);
        }
    } else {
        // Show error
        showError('analysis-results', data.error || 'Process failed');
    }
}

// Create enhanced progress tracking display with PatternFly
function createProgressTracker(steps = []) {
    const defaultSteps = [
        { id: 'step-analysis', title: 'Content Analysis', description: 'Analyzing text structure and style' },
        { id: 'step-pass1', title: 'AI Processing', description: 'Generating improvements' },
        { id: 'step-pass2', title: 'Refinement', description: 'Polishing results' },
        { id: 'step-complete', title: 'Complete', description: 'Ready for review' }
    ];
    
    const stepsToUse = steps.length > 0 ? steps : defaultSteps;
    
    return `
        <div class="pf-v5-c-card app-card">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <h3 class="pf-v5-c-title pf-m-lg">
                        <i class="fas fa-tasks pf-v5-u-mr-sm" style="color: var(--app-primary-color);"></i>
                        Processing Progress
                    </h3>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-l-stack pf-m-gutter">
                    ${stepsToUse.map((step, index) => `
                        <div class="pf-v5-l-stack__item">
                            <div class="step-item pf-v5-c-card pf-m-plain pf-m-bordered" id="${step.id}">
                                <div class="pf-v5-c-card__body">
                                    <div class="pf-v5-l-flex pf-m-align-items-center">
                                        <div class="pf-v5-l-flex__item">
                                            <div class="step-icon" style="
                                                width: 40px;
                                                height: 40px;
                                                display: flex;
                                                align-items: center;
                                                justify-content: center;
                                                border-radius: var(--pf-v5-global--BorderRadius--lg);
                                                background: var(--pf-v5-global--BackgroundColor--200);
                                            ">
                                                <i class="fas fa-circle" style="color: var(--pf-v5-global--Color--200);"></i>
                                            </div>
                                        </div>
                                        <div class="pf-v5-l-flex__item pf-v5-u-ml-md">
                                            <h4 class="pf-v5-c-title pf-m-md pf-v5-u-mb-xs">${step.title}</h4>
                                            <p class="pf-v5-u-font-size-sm pf-v5-u-color-200 pf-v5-u-mb-0">${step.description}</p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
}

// Show real-time status updates with PatternFly alerts
function showStatusUpdate(message, type = 'info') {
    const statusContainer = document.getElementById('status-container');
    if (!statusContainer) return;
    
    const alert = document.createElement('div');
    alert.className = `pf-v5-c-alert pf-m-${type} pf-m-inline fade-in`;
    alert.style.marginBottom = '1rem';
    
    alert.innerHTML = `
        <div class="pf-v5-c-alert__icon">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        </div>
        <h4 class="pf-v5-c-alert__title">Processing Update</h4>
        <div class="pf-v5-c-alert__description">${message}</div>
    `;
    
    statusContainer.appendChild(alert);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (alert.parentNode) {
            alert.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => alert.remove(), 300);
        }
    }, 3000);
}

// BLOCK-LEVEL REWRITING WEBSOCKET HANDLERS

/**
 * Handle block processing start event
 */
function handleBlockProcessingStart(data) {
    console.log('🚀 Block processing started:', data);
    
    const { block_id, block_type, applicable_stations } = data;
    
    // Initialize assembly line progress for this block
    initializeBlockAssemblyLineProgress(block_id, applicable_stations);
    
    // Update any global state if needed
    if (window.blockRewriteState) {
        window.blockRewriteState.currentlyProcessingBlock = block_id;
    }
}

/**
 * Handle station progress update
 */
function handleStationProgressUpdate(data) {
    console.log('🏭 Station progress update:', data);
    
    const { block_id, station, status, preview_text } = data;
    
    // Update specific station status in the assembly line UI
    updateStationStatus(block_id, station, status, preview_text);
    
    // Update overall assembly line progress
    updateBlockAssemblyLineProgress(block_id, data.overall_progress || 50, data.status_text || 'Processing...');
}

/**
 * Handle block processing completion
 */
function handleBlockProcessingComplete(data) {
    console.log('✅ Block processing completed:', data);
    
    const { block_id, result } = data;
    
    // Update global state
    if (window.blockRewriteState) {
        window.blockRewriteState.processedBlocks.add(block_id);
        window.blockRewriteState.blockResults.set(block_id, result);
        window.blockRewriteState.currentlyProcessingBlock = null;
    }
    
    // Complete the assembly line UI
    completeBlockAssemblyLine(block_id);
    
    // The actual results display is handled by the main processing flow
    // This handler just manages the real-time progress UI
}

/**
 * Handle block processing error
 */
function handleBlockProcessingError(data) {
    console.error('❌ Block processing error:', data);
    
    const { block_id, error } = data;
    
    // Show error in assembly line UI
    showAssemblyLineError(block_id, error);
    
    // Update global state
    if (window.blockRewriteState) {
        window.blockRewriteState.currentlyProcessingBlock = null;
    }
}

/**
 * Initialize assembly line progress for a specific block
 */
function initializeBlockAssemblyLineProgress(blockId, stations) {
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"] .assembly-line-stations`);
    if (!assemblyLineElement) return;
    
    // Reset all stations to waiting state
    stations.forEach(station => {
        const stationElement = assemblyLineElement.querySelector(`[data-station="${station}"]`);
        if (stationElement) {
            stationElement.classList.remove('station-processing', 'station-complete', 'station-error');
            stationElement.classList.add('station-waiting');
            
            const statusIcon = stationElement.querySelector('.station-status-icon');
            if (statusIcon) {
                statusIcon.className = 'station-status-icon fas fa-clock';
            }
        }
    });
}

/**
 * Update status of a specific station
 */
function updateStationStatus(blockId, station, status, previewText = null) {
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"] .assembly-line-stations`);
    if (!assemblyLineElement) return;
    
    const stationElement = assemblyLineElement.querySelector(`[data-station="${station}"]`);
    if (!stationElement) return;
    
    // Update station classes
    stationElement.classList.remove('station-waiting', 'station-processing', 'station-complete', 'station-error');
    
    const statusIcon = stationElement.querySelector('.station-status-icon');
    const statusText = stationElement.querySelector('.station-status-text');
    
    switch (status) {
        case 'processing':
            stationElement.classList.add('station-processing');
            if (statusIcon) statusIcon.className = 'station-status-icon fas fa-spinner fa-spin';
            if (statusText) statusText.textContent = 'Processing...';
            break;
        case 'complete':
            stationElement.classList.add('station-complete');
            if (statusIcon) statusIcon.className = 'station-status-icon fas fa-check-circle';
            if (statusText) statusText.textContent = 'Complete';
            break;
        case 'error':
            stationElement.classList.add('station-error');
            if (statusIcon) statusIcon.className = 'station-status-icon fas fa-exclamation-triangle';
            if (statusText) statusText.textContent = 'Error';
            break;
        default:
            stationElement.classList.add('station-waiting');
            if (statusIcon) statusIcon.className = 'station-status-icon fas fa-clock';
            if (statusText) statusText.textContent = 'Waiting';
    }
    
    // Update preview text if provided
    if (previewText) {
        const previewElement = stationElement.querySelector('.station-preview');
        if (previewElement) {
            previewElement.textContent = previewText;
        }
    }
}

/**
 * Update overall assembly line progress
 */
function updateBlockAssemblyLineProgress(blockId, progressPercent, statusText) {
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"] .block-assembly-line`);
    if (!assemblyLineElement) return;
    
    // Update progress bar
    const progressBar = assemblyLineElement.querySelector('.pf-v5-c-progress__bar');
    if (progressBar) {
        progressBar.style.width = `${progressPercent}%`;
    }
    
    // Update progress text
    const progressText = assemblyLineElement.querySelector('.assembly-line-status');
    if (progressText) {
        progressText.textContent = statusText;
    }
    
    // Update progress percentage
    const progressPercentElement = assemblyLineElement.querySelector('.progress-percent');
    if (progressPercentElement) {
        progressPercentElement.textContent = `${Math.round(progressPercent)}%`;
    }
}

/**
 * Complete assembly line processing
 */
function completeBlockAssemblyLine(blockId) {
    updateBlockAssemblyLineProgress(blockId, 100, 'Processing complete');
    
    // Add completion animation
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"] .block-assembly-line`);
    if (assemblyLineElement) {
        assemblyLineElement.classList.add('assembly-line-complete');
        
        // Auto-hide assembly line after showing completion
        setTimeout(() => {
            if (assemblyLineElement.parentNode) {
                assemblyLineElement.style.opacity = '0.7';
            }
        }, 2000);
    }
}

/**
 * Show error in assembly line
 */
function showAssemblyLineError(blockId, errorMessage) {
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"] .block-assembly-line`);
    if (!assemblyLineElement) return;
    
    // Update status to error
    const statusElement = assemblyLineElement.querySelector('.assembly-line-status');
    if (statusElement) {
        statusElement.textContent = `Error: ${errorMessage}`;
        statusElement.classList.add('error-text');
    }
    
    // Add error styling
    assemblyLineElement.classList.add('assembly-line-error');
} 