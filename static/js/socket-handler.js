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
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
    });
}

// Handle real-time progress updates
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

// Update step indicators based on real progress
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
            step.classList.remove('completed');
            step.classList.add('active');
            const icon = step.querySelector('.step-icon');
            if (currentStep.includes('complete')) {
                // Step is complete
                step.classList.remove('active');
                step.classList.add('completed');
                icon.innerHTML = '<i class="fas fa-check-circle text-success"></i>';
            } else {
                // Step is in progress
                icon.innerHTML = '<div class="spinner-border spinner-border-sm text-primary" role="status"></div>';
            }
        } else if (!foundTarget) {
            // Mark previous steps as complete
            step.classList.remove('active');
            step.classList.add('completed');
            const icon = step.querySelector('.step-icon');
            icon.innerHTML = '<i class="fas fa-check-circle text-success"></i>';
        } else {
            // Mark future steps as pending
            step.classList.remove('active', 'completed');
            const icon = step.querySelector('.step-icon');
            icon.innerHTML = '<i class="fas fa-circle text-muted"></i>';
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