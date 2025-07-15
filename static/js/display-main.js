/**
 * Main Display Module - Entry Points and Orchestration
 * Contains the main functions called by other modules and orchestrates the display
 */

// Main entry point - called from file-handler.js and socket-handler.js
function displayAnalysisResults(analysis, content, structuralBlocks = null) {
    const resultsContainer = document.getElementById('analysis-results');
    if (!resultsContainer) return;
    
    let html = `
        <div class="row">
            <div class="col-md-8">
                <div class="card border-0" style="
                    border-radius: 20px;
                    overflow: hidden;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08);
                    background: white;
                ">
                    <div class="card-header border-0 d-flex justify-content-between align-items-center" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 24px;
                    ">
                        <div class="d-flex align-items-center">
                            <div class="me-3 d-flex align-items-center justify-content-center" style="
                                width: 48px;
                                height: 48px;
                                background: rgba(255, 255, 255, 0.15);
                                border-radius: 16px;
                                backdrop-filter: blur(10px);
                            ">
                                <i class="fas fa-file-alt" style="font-size: 20px;"></i>
                            </div>
                            <div>
                                <h5 class="mb-1 fw-bold" style="font-size: 18px; letter-spacing: 0.5px;">Content Analysis</h5>
                                <small class="opacity-90" style="font-size: 14px;">Structural document review and style assessment</small>
                            </div>
                        </div>
                        <div class="d-flex align-items-center">
                            <div class="text-end me-3">
                                <div class="small opacity-75" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Quality Score</div>
                                <div class="fw-bold" style="font-size: 24px;">${analysis.overall_score.toFixed(1)}%</div>
                            </div>
                            <div class="badge" style="
                                background: ${analysis.overall_score >= 80 ? 'rgba(34, 197, 94, 0.9)' : analysis.overall_score >= 60 ? 'rgba(245, 158, 11, 0.9)' : 'rgba(239, 68, 68, 0.9)'};
                                color: white;
                                padding: 8px 16px;
                                border-radius: 12px;
                                font-size: 12px;
                                font-weight: 600;
                                letter-spacing: 0.5px;
                            ">
                                ${analysis.overall_score >= 80 ? 'EXCELLENT' : analysis.overall_score >= 60 ? 'GOOD' : 'NEEDS WORK'}
                            </div>
                        </div>
                    </div>
                    <div class="card-body" style="padding: 32px;">
                        ${structuralBlocks ? (displayStructuralBlocks(structuralBlocks) || displayFlatContent(content, analysis.errors)) : displayFlatContent(content, analysis.errors)}
                        
                        ${analysis.errors.length > 0 ? `
                        <div class="text-center mt-4">
                            <button class="btn btn-primary btn-lg" onclick="rewriteContent()">
                                <i class="fas fa-magic me-2"></i>Rewrite with AI
                            </button>
                        </div>
                        ` : ''}
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                ${generateStatisticsCard(analysis)}
            </div>
        </div>
    `;
    
    resultsContainer.innerHTML = html;
}

// Display structural blocks (ideal UI)
function displayStructuralBlocks(blocks) {
    if (!blocks || blocks.length === 0) {
        return null;
    }
    
    return `
        <div class="mb-4">
            <div class="d-flex align-items-center mb-4" style="
                padding: 20px;
                background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
                border-radius: 16px;
                border: 1px solid #e2e8f0;
            ">
                <div class="me-3 d-flex align-items-center justify-content-center" style="
                    width: 40px;
                    height: 40px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 12px;
                ">
                    <i class="fas fa-sitemap" style="color: white; font-size: 16px;"></i>
                </div>
                <div>
                    <h6 class="mb-1 fw-bold" style="color: #1e293b; font-size: 16px; letter-spacing: 0.5px;">Document Structure Analysis</h6>
                    <small style="color: #64748b; font-size: 13px;">Content organized by structural elements with context-aware style checking</small>
                </div>
                <div class="ms-auto">
                    <div class="badge" style="
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        padding: 6px 12px;
                        border-radius: 8px;
                        font-size: 11px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    ">
                        ${blocks.length} BLOCKS
                    </div>
                </div>
            </div>
            <div class="structural-blocks">
                ${(() => {
                    let displayIndex = 0;
                    return blocks.map(block => {
                        const html = createStructuralBlock(block, displayIndex);
                        if (html !== '') {
                            displayIndex++;
                        }
                        return html;
                    }).filter(html => html !== '').join('');
                })()}
            </div>
        </div>
    `;
}

// Display flat content (fallback)
function displayFlatContent(content, errors) {
    return `
        <div class="mb-3">
            <h6>Original Content:</h6>
            <div class="border rounded p-3 bg-light">
                ${highlightErrors(content, errors)}
            </div>
        </div>
        
        ${errors.length > 0 ? `
        <div class="mb-3">
            <h6>Detected Issues (${errors.length}):</h6>
            <div class="analysis-container">
                ${errors.map(error => createErrorCard(error)).join('')}
            </div>
        </div>
        ` : '<div class="alert alert-success"><i class="fas fa-check-circle me-2"></i>No issues detected!</div>'}
    `;
} 