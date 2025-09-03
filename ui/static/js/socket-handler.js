// Initialize Socket.IO connection
function initializeSocket() {
    console.log('🔍 DEBUG: Initializing Socket.IO connection...');
    socket = io();
    
    socket.on('connect', function() {
        console.log('✅ Connected to server');
        
        // Check both global variables for session ID
        const currentSessionId = window.sessionId || sessionId;
        if (currentSessionId) {
            console.log(`🔍 DEBUG: Joining session room: ${currentSessionId}`);
            socket.emit('join_session', { session_id: currentSessionId });
        }
    });
    
    socket.on('session_id', function(data) {
        sessionId = data.session_id;
        console.log('✅ Session ID received:', sessionId);
    });
    
    socket.on('session_joined', function(data) {
        console.log('✅ Joined session room:', data.session_id);
    });
    
    socket.on('session_left', function(data) {
        console.log('✅ Left session room:', data.session_id);
    });
    
    socket.on('progress_update', function(data) {
        console.log('📡 WebSocket: progress_update event received');
        handleProgressUpdate(data);
    });
    
    socket.on('process_complete', function(data) {
        console.log('📡 WebSocket: process_complete event received');
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
    console.log('\n🔍 DEBUG FRONTEND PROGRESS UPDATE:');
    console.log('   📊 Received progress data:', data);
    console.log('   📋 Data keys:', Object.keys(data));
    console.log('   📋 Progress value:', data.progress);
    console.log('   📋 Step value:', data.step);
    console.log('   📋 Status value:', data.status);
    console.log('   📋 Detail value:', data.detail);
    
    const statusElement = document.getElementById('current-status');
    const detailElement = document.getElementById('status-detail');
    
    if (statusElement && detailElement) {
        statusElement.textContent = data.status;
        detailElement.textContent = data.detail;
        console.log('   ✅ Updated status elements');
    } else {
        console.log('   ⚠️  Status elements not found');
    }
    
    // Update step indicators based on actual progress
    console.log('   🔄 Updating step indicators...');
    updateStepIndicators(data.step, data.progress);
    
    // ENHANCED: Also update assembly line progress for block-level processing
    // Check if this is a pass-related update that should update assembly line progress
    if (data.step && (data.step.includes('Pass') || data.step.includes('station') || data.step.includes('Processing'))) {
        console.log('   🏭 This looks like an assembly line update');
        // Try to find the currently processing block and update its assembly line
        const currentProcessingBlock = window.blockRewriteState?.currentlyProcessingBlock;
        console.log('   📋 Current processing block:', currentProcessingBlock);
        if (currentProcessingBlock && data.progress) {
            const progressPercent = parseInt(data.progress) || 0;
            console.log('   📊 Updating assembly line progress:', progressPercent + '%');
            updateBlockAssemblyLineProgress(currentProcessingBlock, progressPercent, data.detail || data.status);
            console.log(`   ✅ Updated assembly line progress for block ${currentProcessingBlock}: ${progressPercent}%`);
        } else {
            console.log('   ⚠️  No current processing block or progress value');
        }
    } else {
        console.log('   ⚠️  This does not look like an assembly line update');
    }
    console.log('   ✅ Progress update handling complete\n');
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
    
    // Calculate overall progress based on completed stations
    const progressPercentage = calculateStationProgress(block_id, station, status);
    const statusText = generateProgressStatusText(station, status, preview_text);
    
    // Update overall assembly line progress
    updateBlockAssemblyLineProgress(block_id, progressPercentage, statusText);
    console.log(`🎯 Assembly line progress updated: ${block_id} = ${progressPercentage}% (${statusText})`);
}

/**
 * Calculate progress percentage based on station completion
 */
function calculateStationProgress(blockId, currentStation, status) {
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"] .assembly-line-stations`);
    if (!assemblyLineElement) return 0;
    
    const allStations = assemblyLineElement.querySelectorAll('[data-station]');
    const totalStations = allStations.length;
    
    if (totalStations === 0) return 100;
    
    let completedStations = 0;
    let currentStationProgress = 0;
    
    allStations.forEach(stationEl => {
        const stationName = stationEl.getAttribute('data-station');
        if (stationEl.classList.contains('station-complete')) {
            completedStations++;
        } else if (stationName === currentStation && status === 'processing') {
            currentStationProgress = 0.5; // 50% for current processing station
        }
    });
    
    // If current station just completed, count it
    if (status === 'complete') {
        completedStations++;
        currentStationProgress = 0;
    }
    
    const progress = ((completedStations + currentStationProgress) / totalStations) * 100;
    return Math.min(100, Math.max(0, progress));
}

/**
 * Generate status text for progress updates
 */
function generateProgressStatusText(station, status, previewText) {
    const stationNames = {
        'urgent': 'Critical/Legal Pass',
        'high': 'Structural Pass',
        'medium': 'Grammar Pass',
        'low': 'Style Pass'
    };
    
    const stationName = stationNames[station] || 'Processing Pass';
    
    if (status === 'processing') {
        return `🔄 ${stationName}: ${previewText || 'Processing...'}`;
    } else if (status === 'complete') {
        return `✅ ${stationName}: ${previewText || 'Complete'}`;
    }
    
    return `⏳ ${stationName}: Waiting...`;
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
    console.log(`🎯 Updating assembly line progress: ${blockId} → ${progressPercent}% → "${statusText}"`);
    
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"].block-assembly-line`);
    if (!assemblyLineElement) {
        console.warn(`⚠️  Assembly line element not found for block: ${blockId}`);
        return;
    }
    
    // Ensure progress is valid
    const validProgress = Math.max(0, Math.min(100, progressPercent || 0));
    
    // Update progress bar
    const progressBar = assemblyLineElement.querySelector('.pf-v5-c-progress__bar');
    if (progressBar) {
        progressBar.style.width = `${validProgress}%`;
        console.log(`📊 Progress bar updated to ${validProgress}%`);
    } else {
        console.warn(`⚠️  Progress bar element not found in assembly line for block: ${blockId}`);
    }
    
    // Update progress text
    const progressText = assemblyLineElement.querySelector('.assembly-line-status');
    if (progressText) {
        progressText.textContent = statusText || 'Processing...';
    }
    
    // Update progress percentage text
    const progressPercentElement = assemblyLineElement.querySelector('.progress-percent');
    if (progressPercentElement) {
        progressPercentElement.textContent = `${Math.round(validProgress)}%`;
        console.log(`🔢 Progress percentage updated to ${Math.round(validProgress)}%`);
    } else {
        console.warn(`⚠️  Progress percent element not found in assembly line for block: ${blockId}`);
    }
}

/**
 * Complete assembly line processing
 */
function completeBlockAssemblyLine(blockId) {
    updateBlockAssemblyLineProgress(blockId, 100, 'Processing complete');
    
    // Add completion animation
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"].block-assembly-line`);
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
    const assemblyLineElement = document.querySelector(`[data-block-id="${blockId}"].block-assembly-line`);
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

/**
 * Join session room dynamically
 */
function joinSessionRoom(sessionId) {
    if (socket && socket.connected && sessionId) {
        console.log(`🔍 DEBUG: Dynamically joining session room: ${sessionId}`);
        socket.emit('join_session', { session_id: sessionId });
        return true;
    } else {
        console.warn(`❌ Cannot join session room: socket=${!!socket}, connected=${socket?.connected}, sessionId=${sessionId}`);
        return false;
    }
}

// Export functions for global use
if (typeof window !== 'undefined') {
    window.joinSessionRoom = joinSessionRoom;
} 