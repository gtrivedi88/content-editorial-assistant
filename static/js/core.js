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

// Rewrite content function
function rewriteContent() {
    if (!currentContent || !currentAnalysis) {
        alert('Please analyze content first');
        return;
    }

    showLoading('rewrite-results', 'Generating AI rewrite...');

    fetch('/rewrite', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            content: currentContent,
            errors: currentAnalysis.errors || [],
            session_id: sessionId 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayRewriteResults(data);
        } else {
            showError('rewrite-results', data.error || 'Rewrite failed');
        }
    })
    .catch(error => {
        console.error('Rewrite error:', error);
        showError('rewrite-results', 'Rewrite failed: ' + error.message);
    });
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