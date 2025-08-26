# Block-Level AI Rewrite Implementation Plan
## Simplified, Production-Ready Approach

## Overview
Transform document-level AI rewrite to granular block-level processing with zero technical debt. Each phase is production-ready and fully tested.

---

## Phase 1: Backend Core Implementation
**Goal:** Block-level rewriting foundation  
**Duration:** 3-4 days  
**Production Ready:** Yes

### Files to Edit

#### 1.1 `rewriter/assembly_line_rewriter.py`
**Changes:**
- **REMOVE:** `apply_sentence_level_assembly_line_fixes()` method
- **ADD:** `apply_block_level_assembly_line_fixes(block_content, block_errors, block_type)`
- **UPDATE:** `_sort_errors_by_priority()` to work with block-scoped errors

```python
def apply_block_level_assembly_line_fixes(self, block_content: str, block_errors: List[Dict], block_type: str) -> Dict[str, Any]:
    """Apply assembly line fixes to a single structural block."""
    # Same logic as sentence-level, but scoped to block content
    # block_type helps provide context (paragraph, heading, list, etc.)
```

#### 1.2 `app_modules/api_routes.py`
**Changes:**
- **REMOVE:** `/rewrite` endpoint and `rewrite_content()` function  
- **ADD:** `/rewrite-block` endpoint
- **UPDATE:** Error handling for block-specific failures

```python
@app.route('/rewrite-block', methods=['POST'])
def rewrite_block():
    """AI-powered single block rewriting."""
    data = request.get_json()
    block_content = data.get('block_content', '')
    block_errors = data.get('block_errors', [])
    block_type = data.get('block_type', 'paragraph')
    block_id = data.get('block_id', '')
    session_id = data.get('session_id', '')
    
    # Process single block through assembly line
    result = ai_rewriter.assembly_line.apply_block_level_assembly_line_fixes(
        block_content, block_errors, block_type
    )
    result['block_id'] = block_id
    return jsonify(result)
```

#### 1.3 `app_modules/websocket_handlers.py`
**Changes:**
- **UPDATE:** Progress events to include `block_id` and `block_type`
- **ADD:** Block-specific progress tracking

### End-to-End Testing Phase 1

**Test Cases:**
1. **Single block processing:** Send paragraph block with 3 errors → expect improved text
2. **Different block types:** Test paragraph, heading, list blocks → verify context awareness
3. **Error-free blocks:** Send clean block → expect no changes, high confidence
4. **API error handling:** Send malformed request → expect proper error response
5. **WebSocket events:** Verify block-specific progress updates

**Test Command:**
```bash
# Run backend tests
pytest tests/test_block_rewriting.py -v

# Manual API test
curl -X POST http://localhost:5000/rewrite-block \
  -H "Content-Type: application/json" \
  -d '{"block_content": "The implementation was done by the team.", "block_errors": [{"type": "passive_voice"}], "block_type": "paragraph"}'
```

**Expected Results:**
- ✅ Block processing completes in <30 seconds
- ✅ Assembly line stations show only for relevant error types
- ✅ WebSocket progress events include block context
- ✅ API returns improved text with confidence score

---

## Phase 2: Frontend Core Implementation  
**Goal:** Block-level UI with dynamic assembly lines  
**Duration:** 4-5 days  
**Production Ready:** Yes

### Files to Edit

#### 2.1 `ui/static/js/display-main.js`
**Changes:**
- **UPDATE:** `displayStructuralBlocks()` to include "Rewrite This Block" buttons
- **ADD:** `generateBlockRewriteButton(block)` function
- **ADD:** Block priority indicators (red/yellow/green based on error severity)

```javascript
function displayStructuralBlocks(blocks) {
    // Existing logic...
    // Add per-block rewrite button:
    if (block.errors && block.errors.length > 0) {
        html += `<button class="pf-v5-c-button pf-m-primary" onclick="rewriteBlock('${block.id}')">
                   🤖 Fix ${block.errors.length} Issue${block.errors.length > 1 ? 's' : ''}
                 </button>`;
    }
}
```

#### 2.2 `ui/static/js/core.js`
**Changes:**
- **REMOVE:** `rewriteContent()`, `initializeProgressiveRewriteUI()`, `displayAssemblyLineResults()`
- **ADD:** `rewriteBlock(blockId)` function
- **ADD:** `displayBlockAssemblyLine(blockId, errors)` function
- **ADD:** `displayBlockResults(blockId, result)` function

```javascript
function rewriteBlock(blockId) {
    const block = findBlockById(blockId);
    if (!block || !block.errors.length) return;
    
    // Show dynamic assembly line based on block errors
    displayBlockAssemblyLine(blockId, block.errors);
    
    // Call new API endpoint
    fetch('/rewrite-block', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            block_content: block.content,
            block_errors: block.errors,
            block_type: block.type,
            block_id: blockId,
            session_id: sessionId
        })
    })
    .then(response => response.json())
    .then(data => displayBlockResults(blockId, data));
}
```

#### 2.3 `ui/static/js/socket-handler.js`
**Changes:**
- **UPDATE:** `handleProgressUpdate()` to support block-specific progress
- **UPDATE:** Progress tracking to work with dynamic station counts
- **REMOVE:** Document-level progress handlers

### Files to Create

#### 2.4 `ui/static/js/block-assembly.js` (NEW)
**Purpose:** Dynamic assembly line visualization for blocks
**Size:** ~150 lines

```javascript
// Create assembly line UI based on actual block errors
function createDynamicAssemblyLine(blockId, errors) {
    const stations = getApplicableStations(errors);
    // Build UI showing only relevant stations
    // Real-time progress updates per station
}

function getApplicableStations(errors) {
    const stationMap = {
        'passive_voice': 'Grammar Station',
        'contractions': 'Style Station', 
        'legal_claims': 'Legal Station'
    };
    return errors.map(error => stationMap[error.type]).filter(Boolean);
}
```

### End-to-End Testing Phase 2

**Test Cases:**
1. **Block button generation:** Verify "Rewrite This Block" buttons appear on error blocks only
2. **Dynamic assembly line:** Click rewrite → verify only relevant stations show
3. **Real-time progress:** Monitor WebSocket updates during block processing
4. **Results display:** Verify improved text appears with copy button
5. **Multiple blocks:** Process 3 different blocks sequentially

**Test Commands:**
```bash
# Frontend integration tests
npm test -- --grep "block rewrite"

# Manual browser testing
# 1. Upload document with 3 blocks
# 2. Click "Rewrite This Block" on block with passive voice errors  
# 3. Verify only Grammar Station appears
# 4. Verify copy button works on result
```

**Expected Results:**
- ✅ Only error blocks show rewrite buttons
- ✅ Assembly line shows dynamic stations (not fixed 4)
- ✅ Progress tracks through applicable stations only
- ✅ Results display with one-click copy functionality

---

## Phase 3: Integration & Legacy Cleanup
**Goal:** Remove all legacy code, ensure clean system  
**Duration:** 2-3 days  
**Production Ready:** Yes

### Files to Delete
**NONE** - All files are being refactored, not deleted

### Methods/Functions to Remove

#### 3.1 Backend Methods to Remove
- `rewriter/assembly_line_rewriter.py`:
  - `apply_sentence_level_assembly_line_fixes()`
- `app_modules/api_routes.py`:
  - `rewrite_content()` function
  - `/rewrite` endpoint handler

#### 3.2 Frontend Functions to Remove  
- `ui/static/js/core.js`:
  - `rewriteContent()`
  - `initializeProgressiveRewriteUI()`
  - `displayAssemblyLineResults()`
  - `handleAssemblyLineProgress()`
  - `updateAssemblyLineProgress()`

#### 3.3 CSS Classes to Remove
- `.assembly-line-progress` (document-level)
- `.assembly-stations` (fixed station layout)
- `.content-preview` (document-level preview)

### Configuration Updates

#### 3.4 `rewriter/assembly_line_config.yaml`
**Changes:**
- **ADD:** Dynamic station configuration
- **UPDATE:** Station display names to be contextual

```yaml
stations:
  grammar:
    display_name: "Grammar Station"
    error_types: ["passive_voice", "contractions", "verbs"]
  style:
    display_name: "Style Station" 
    error_types: ["word_usage", "sentence_length"]
  legal:
    display_name: "Legal Station"
    error_types: ["claims", "personal_info"]
```

### End-to-End Testing Phase 3

**Test Cases:**
1. **Legacy endpoint removal:** Verify `/rewrite` endpoint returns 404
2. **Function cleanup:** Verify removed functions don't exist in codebase
3. **CSS cleanup:** Verify legacy classes removed from stylesheets
4. **Configuration loading:** Test new assembly line config loads properly
5. **Complete workflow:** Full document → block analysis → block rewrite → copy result

**Test Commands:**
```bash
# Verify legacy code removal
grep -r "rewriteContent\|apply_sentence_level" . --exclude-dir=node_modules
# Should return no results

# Full system test
python -m pytest tests/ -v
npm test

# Load testing
curl http://localhost:5000/rewrite  # Should return 404
```

**Expected Results:**
- ✅ No legacy code remains in codebase
- ✅ All tests pass with new block-level system
- ✅ Configuration loads without errors
- ✅ Complete workflow works end-to-end

---

## Phase 4: Production Optimization & Monitoring
**Goal:** Production-ready performance and monitoring  
**Duration:** 2 days  
**Production Ready:** Yes

### Files to Edit

#### 4.1 `config.py`
**Changes:**
- **ADD:** Block processing timeout configuration
- **ADD:** Performance monitoring flags

#### 4.2 `app_modules/websocket_handlers.py`  
**Changes:**
- **ADD:** Block processing metrics collection
- **ADD:** Error rate monitoring

### Files to Create

#### 4.3 `tests/test_block_rewrite_e2e.py` (NEW)
**Purpose:** Comprehensive end-to-end testing
**Size:** ~100 lines

```python
def test_complete_block_workflow():
    """Test full workflow: upload → analyze → rewrite block → copy result"""
    # Upload document
    # Verify blocks detected
    # Rewrite one block
    # Verify improved result
    # Test copy functionality

def test_performance_benchmarks():
    """Ensure block processing meets performance requirements"""
    # Block processing < 30 seconds
    # UI response < 100ms
    # WebSocket reliability > 99%
```

### End-to-End Testing Phase 4

**Performance Tests:**
1. **Processing speed:** Block rewrite completes in <30 seconds
2. **UI responsiveness:** Button clicks respond in <100ms  
3. **Memory usage:** No memory leaks during multiple block processing
4. **WebSocket reliability:** Connection stable during long processing
5. **Concurrent users:** System handles 10 simultaneous block rewrites

**Load Testing:**
```bash
# Performance testing
python scripts/load_test_blocks.py

# Memory profiling  
python -m memory_profiler app.py

# WebSocket stability
python scripts/websocket_stress_test.py
```

**Expected Results:**
- ✅ Average block processing: <25 seconds
- ✅ UI response time: <50ms
- ✅ Memory usage: Stable during extended use
- ✅ WebSocket uptime: >99.5%
- ✅ Concurrent user support: 10+ users

---

## Complete File Summary

### Files to Edit (6 files)
1. `rewriter/assembly_line_rewriter.py` - Core block processing logic
2. `app_modules/api_routes.py` - New block rewrite endpoint  
3. `app_modules/websocket_handlers.py` - Block-specific progress events
4. `ui/static/js/display-main.js` - Block rewrite buttons
5. `ui/static/js/core.js` - Block processing functions
6. `ui/static/js/socket-handler.js` - Block progress handling

### Files to Create (2 files)  
1. `ui/static/js/block-assembly.js` - Dynamic assembly line UI
2. `tests/test_block_rewrite_e2e.py` - End-to-end testing

### Files to Delete
**NONE** - Clean refactoring approach

### Functions/Methods to Remove (8 items)
1. `apply_sentence_level_assembly_line_fixes()` - Backend
2. `rewrite_content()` - API endpoint  
3. `rewriteContent()` - Frontend
4. `initializeProgressiveRewriteUI()` - Frontend
5. `displayAssemblyLineResults()` - Frontend
6. `handleAssemblyLineProgress()` - Frontend  
7. `updateAssemblyLineProgress()` - Frontend
8. Legacy CSS classes (3 classes)

---

## Success Metrics

**User Experience:**
- Time to first block improvement: <30 seconds
- Copy success rate: >98%
- User workflow completion: >95%

**Technical Performance:**  
- Block processing time: <25 seconds average
- UI response time: <50ms
- WebSocket reliability: >99.5%

**Quality Metrics:**
- AI confidence: >90% average
- Error reduction: >85% of flagged issues
- Zero technical debt: 100% legacy code removed

---

## Risk Mitigation

**Technical Risks:**
- Block processing timeout → 30 second hard limit with fallback
- WebSocket failure → Automatic reconnection with polling fallback  
- UI complexity → Progressive enhancement, core functionality works without JS

**User Experience Risks:**
- Learning curve → Intuitive block buttons with clear CTAs
- Workflow confusion → Visual priority indicators guide user flow
- Copy/paste issues → Multiple copy methods (button + keyboard shortcuts)

This simplified plan eliminates over-engineering while ensuring production-ready quality at each phase with comprehensive testing.

---

## Additional Implementation Details for Future Reference

### Error Priority Mapping Reference
```javascript
// Complete mapping from assembly_line_config.yaml for frontend use
const ERROR_PRIORITY_MAP = {
    // URGENT (Red priority)
    'legal_claims': 'urgent',
    'legal_company_names': 'urgent', 
    'legal_personal_information': 'urgent',
    'inclusive_language': 'urgent',
    'second_person': 'urgent',
    
    // HIGH (Yellow priority)
    'passive_voice': 'high',
    'sentence_length': 'high',
    'subjunctive_mood': 'high',
    'verbs': 'high',
    'headings': 'high',
    
    // MEDIUM (Yellow priority)
    'word_usage_a': 'medium', 'word_usage_b': 'medium', // ... all word_usage_*
    'contractions': 'medium',
    'spelling': 'medium',
    'terminology': 'medium',
    'anthropomorphism': 'medium',
    'capitalization': 'medium',
    'prefixes': 'medium',
    'plurals': 'medium',
    'abbreviations': 'medium',
    
    // LOW (Green priority - may not need processing)
    'punctuation_commas': 'low',
    'punctuation_periods': 'low', // ... all punctuation_*
    'tone': 'low',
    'citations': 'low',
    'ambiguity': 'low',
    'currency': 'low'
};

function getErrorPriority(errorType) {
    // Handle wildcard patterns
    if (errorType.startsWith('word_usage_')) return 'medium';
    if (errorType.startsWith('punctuation_')) return 'low';
    if (errorType.startsWith('technical_')) return 'medium';
    if (errorType.startsWith('references_')) return 'low';
    
    return ERROR_PRIORITY_MAP[errorType] || 'medium';
}
```

### Key UI State Management
```javascript
// Global state for block-level rewriting
window.blockRewriteState = {
    currentlyProcessingBlock: null,
    processedBlocks: new Set(),
    blockResults: new Map(), // blockId -> result object
    sessionId: null
};

// Block processing workflow
function rewriteSingleBlock(blockId) {
    // 1. Update UI to show processing state
    updateBlockCardToProcessing(blockId);
    
    // 2. Get block data
    const block = getBlockById(blockId);
    const applicableStations = getDynamicStations(block.errors);
    
    // 3. Initialize assembly line UI
    showBlockAssemblyLine(blockId, applicableStations);
    
    // 4. Send API request
    fetch('/rewrite-block', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            block_id: blockId,
            block_content: block.content,
            block_errors: block.errors,
            block_type: block.type,
            session_id: window.sessionId
        })
    });
    
    // 5. WebSocket will handle progress updates
}
```

### WebSocket Event Handling Details
```javascript
// Block-specific WebSocket event handlers
socket.on('block_processing_start', (data) => {
    window.blockRewriteState.currentlyProcessingBlock = data.block_id;
    updateAssemblyLineProgress(data.block_id, 0, 'Starting...');
});

socket.on('station_progress_update', (data) => {
    updateStationStatus(data.station, data.status, data.preview_text);
    updateAssemblyLineProgress(data.block_id, data.overall_progress, data.status_text);
});

socket.on('block_processing_complete', (data) => {
    window.blockRewriteState.processedBlocks.add(data.block_id);
    window.blockRewriteState.blockResults.set(data.block_id, data.result);
    window.blockRewriteState.currentlyProcessingBlock = null;
    
    displayBlockResults(data.block_id, data.result);
    updateBlockCardToComplete(data.block_id, data.result.errors_fixed);
});
```

### Critical CSS Classes for New UI
```css
/* Block-level rewrite UI classes */
.block-rewrite-button {
    /* Prominent rewrite button per block */
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.block-priority-red { border-left: 4px solid #dc3545; }
.block-priority-yellow { border-left: 4px solid #ffc107; }
.block-priority-green { border-left: 4px solid #28a745; }

.block-assembly-line {
    /* Dynamic assembly line container */
    background: #f8f9fa;
    border-radius: 8px;
    padding: 20px;
    margin: 16px 0;
}

.dynamic-station {
    /* Individual station in assembly line */
    display: flex;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #e9ecef;
}

.station-processing { color: #007bff; }
.station-complete { color: #28a745; }
.station-waiting { color: #6c757d; }

.block-results-card {
    /* Results display for completed block */
    background: white;
    border: 2px solid #28a745;
    border-radius: 8px;
    padding: 24px;
    margin: 16px 0;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.copy-text-button {
    /* Primary action button for copying result */
    background: #28a745;
    color: white;
    border: none;
    padding: 12px 24px;
    border-radius: 6px;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    width: 100%;
    max-width: 300px;
    margin: 16px auto;
    display: block;
}
```

### Backend Error Handling Patterns
```python
# rewriter/document_rewriter.py - Error handling for block processing
def rewrite_single_block(self, block_content: str, block_errors: List[Dict], 
                        block_type: str, session_id: str = None) -> Dict[str, Any]:
    try:
        # Validate inputs
        if not block_content or not block_content.strip():
            return self._create_error_response("Empty block content")
        
        if not block_errors:
            return self._create_no_errors_response(block_content)
        
        # Process through assembly line
        result = self.ai_rewriter.rewrite(
            content=block_content,
            errors=block_errors, 
            context=block_type,
            pass_number=1
        )
        
        # Add block-specific metadata
        result.update({
            'block_type': block_type,
            'session_id': session_id,
            'applicable_stations': self.get_applicable_stations(block_errors),
            'processing_timestamp': time.time()
        })
        
        return result
        
    except Exception as e:
        logger.error(f"Block rewrite failed for session {session_id}: {e}")
        return self._create_error_response(f"Processing failed: {str(e)}")

def _create_error_response(self, error_message: str) -> Dict[str, Any]:
    return {
        'rewritten_text': '',
        'confidence': 0.0,
        'improvements': [],
        'errors_fixed': 0,
        'error': error_message,
        'success': False
    }

def _create_no_errors_response(self, content: str) -> Dict[str, Any]:
    return {
        'rewritten_text': content,
        'confidence': 1.0,
        'improvements': ['Block is already clean'],
        'errors_fixed': 0,
        'success': True
    }
```

### Assembly Line Station Detection Logic
```python
# rewriter/assembly_line_rewriter.py - Dynamic station detection
def get_applicable_stations(self, block_errors: List[Dict]) -> List[str]:
    """Return only assembly line stations needed for this block's errors."""
    
    stations_needed = set()
    
    for error in block_errors:
        error_type = error.get('type', '')
        
        # Map error types to assembly line stations
        if error_type in ['legal_claims', 'legal_company_names', 'inclusive_language', 'second_person']:
            stations_needed.add('urgent')
        elif error_type in ['passive_voice', 'sentence_length', 'subjunctive_mood', 'verbs', 'headings']:
            stations_needed.add('high')
        elif error_type.startswith('word_usage_') or error_type in ['contractions', 'spelling', 'terminology']:
            stations_needed.add('medium')
        elif error_type.startswith('punctuation_') or error_type in ['tone', 'citations', 'ambiguity']:
            stations_needed.add('low')
    
    # Return in priority order
    priority_order = ['urgent', 'high', 'medium', 'low']
    return [station for station in priority_order if station in stations_needed]

def get_station_display_name(self, station: str) -> str:
    """Get user-friendly display name for assembly line station."""
    
    station_names = {
        'urgent': 'Critical/Legal Pass',
        'high': 'Structural Pass', 
        'medium': 'Grammar Pass',
        'low': 'Style Pass'
    }
    
    return station_names.get(station, 'Processing Pass')
```

### Frontend Block Detection and UI Updates
```javascript
// ui/static/js/display-main.js - Enhanced block display logic
function createStructuralBlock(block, displayIndex, allBlocks = []) {
    // Get priority level for this block
    const priority = getBlockPriority(block.errors);
    const priorityClass = `block-priority-${priority}`;
    const priorityIcon = getPriorityIcon(priority);
    
    // Count errors by type for better context
    const errorSummary = summarizeBlockErrors(block.errors);
    
    // Generate contextual rewrite button
    const rewriteButton = block.errors && block.errors.length > 0 
        ? generateContextualRewriteButton(block, priority)
        : '';
    
    return `
        <div class="pf-v5-c-card pf-m-compact pf-m-bordered-top ${priorityClass}" id="block-${displayIndex}">
            <div class="pf-v5-c-card__header">
                <div class="pf-v5-c-card__header-main">
                    <i class="${getBlockIcon(block.block_type)} pf-v5-u-mr-sm"></i>
                    <span class="pf-v5-u-font-weight-bold">BLOCK ${displayIndex + 1}:</span>
                    <span class="pf-v5-u-ml-sm">${getBlockTypeDisplayName(block.block_type)}</span>
                    ${priorityIcon}
                </div>
                <div class="pf-v5-c-card__actions">
                    <span class="pf-v5-c-label pf-m-outline pf-m-${getStatusColor(block.errors)}">
                        <span class="pf-v5-c-label__content">${getStatusText(block.errors)}</span>
                    </span>
                </div>
            </div>
            <div class="pf-v5-c-card__body">
                <div class="pf-v5-u-p-md pf-v5-u-background-color-200" style="white-space: pre-wrap; word-wrap: break-word;">
                    ${escapeHtml(block.content)}
                </div>
                
                ${errorSummary ? `
                <div class="error-summary pf-v5-u-mt-md">
                    <strong>Issues found:</strong> ${errorSummary}
                </div>
                ` : ''}
                
                ${rewriteButton}
            </div>
        </div>
    `;
}

function getBlockPriority(errors) {
    if (!errors || errors.length === 0) return 'green';
    
    const priorities = errors.map(error => getErrorPriority(error.type));
    
    if (priorities.includes('urgent')) return 'red';
    if (priorities.includes('high')) return 'yellow';
    if (priorities.includes('medium')) return 'yellow';
    return 'green';
}

function generateContextualRewriteButton(block, priority) {
    const buttonText = priority === 'red' 
        ? `🚨 Fix ${block.errors.length} Critical Issue${block.errors.length > 1 ? 's' : ''}`
        : `🤖 Improve ${block.errors.length} Issue${block.errors.length > 1 ? 's' : ''}`;
    
    const estimatedTime = estimateBlockProcessingTime(block.errors);
    
    return `
        <div class="pf-v5-u-mt-md">
            <button class="block-rewrite-button" onclick="rewriteSingleBlock('block-${displayIndex}')">
                ${buttonText}
            </button>
            <small class="pf-v5-u-ml-sm pf-v5-u-color-400">
                ⏱️ ~${estimatedTime} seconds
            </small>
        </div>
    `;
}
```

### Testing Framework Extensions
```python
# tests/test_block_rewrite_e2e.py - Comprehensive testing patterns
import pytest
import json
from app import create_app

class TestBlockRewriting:
    
    @pytest.fixture
    def sample_block_data(self):
        return {
            'block_content': 'The implementation was done by the team and the testing was conducted.',
            'block_errors': [
                {'type': 'passive_voice', 'flagged_text': 'was done'},
                {'type': 'passive_voice', 'flagged_text': 'was conducted'}
            ],
            'block_type': 'paragraph',
            'block_id': 'test-block-1'
        }
    
    def test_block_processing_pipeline(self, client, sample_block_data):
        """Test complete block processing pipeline."""
        response = client.post('/rewrite-block', 
                              data=json.dumps(sample_block_data),
                              content_type='application/json')
        
        assert response.status_code == 200
        result = json.loads(response.data)
        
        # Verify response structure
        assert 'rewritten_text' in result
        assert 'confidence' in result
        assert 'errors_fixed' in result
        assert result['errors_fixed'] > 0
        
        # Verify improved text doesn't contain passive voice
        assert 'was done' not in result['rewritten_text']
        assert 'was conducted' not in result['rewritten_text']
    
    def test_dynamic_station_detection(self, sample_block_data):
        """Test that only relevant assembly line stations are used."""
        from rewriter.assembly_line_rewriter import AssemblyLineRewriter
        
        rewriter = AssemblyLineRewriter(None, None)
        stations = rewriter.get_applicable_stations(sample_block_data['block_errors'])
        
        # Should only include 'high' priority for passive voice
        assert 'high' in stations
        assert 'urgent' not in stations
        assert len(stations) == 1
    
    def test_error_handling(self, client):
        """Test API error handling for invalid block data."""
        # Empty content
        response = client.post('/rewrite-block', 
                              data=json.dumps({'block_content': ''}),
                              content_type='application/json')
        assert response.status_code == 400
        
        # Malformed JSON
        response = client.post('/rewrite-block', 
                              data='invalid json',
                              content_type='application/json')
        assert response.status_code == 400
    
    def test_performance_requirements(self, client, sample_block_data):
        """Test that block processing meets performance requirements."""
        import time
        
        start_time = time.time()
        response = client.post('/rewrite-block', 
                              data=json.dumps(sample_block_data),
                              content_type='application/json')
        processing_time = time.time() - start_time
        
        assert response.status_code == 200
        assert processing_time < 30  # Must complete within 30 seconds
```