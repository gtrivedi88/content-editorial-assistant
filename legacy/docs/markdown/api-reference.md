# API reference

Note |  **This documentation is for developers** who want to integrate with the Content Editorial Assistant API or build automation workflows.  
---|---  
  
## Overview

Content Editorial Assistant provides both REST API and WebSocket interfaces for document analysis, AI-powered rewriting, and real-time communication. This reference covers all available endpoints, request formats, and response structures.

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible with automatic session management.

## Base configuration

### Base URL
[code] 
    http://localhost:5000
[/code]

### Content types

  * **Request** : `multipart/form-data` for file uploads, `application/json` for JSON data

  * **Response** : `application/json`

### Common headers
[code] 
    Content-Type: application/json
    Accept: application/json
[/code]

## Document processing

### Upload document

Upload and extract text from various document formats.
[code] 
    POST /upload
[/code]

#### Request parameters

Parameter | Type | Required | Description  
---|---|---|---  
file | File | Yes | Document file (PDF, DOCX, Markdown, AsciiDoc, DITA, TXT)  
format_hint | String | No | Override auto-detection: `pdf`, `docx`, `markdown`, `asciidoc`, `dita`, `txt`  
  
#### Example request
[code] 
    curl -X POST \
      -F "file=@document.pdf" \
      -F "format_hint=pdf" \
      http://localhost:5000/upload
[/code]

#### Response
[code] 
    {
      "success": true,
      "filename": "document.pdf",
      "text": "Extracted document content...",
      "format": "pdf",
      "size": 1048576,
      "pages": 5,
      "extraction_time": 1.25,
      "document_id": "doc_12345",
      "analysis_id": "analysis_67890"
    }
[/code]

## Content Analysis

### Analyze Content

Perform comprehensive style analysis on text content.
[code] 
    POST /analyze
[/code]

#### Request Body
[code] 
    {
      "content": "Your text content to analyze...",
      "format_hint": "auto",
      "content_type": "concept",
      "session_id": "session_12345",
      "confidence_threshold": 0.5,
      "include_confidence_details": true,
      "document_id": "doc_12345",
      "analysis_id": "analysis_67890"
    }
[/code]

#### Request parameters

Parameter | Type | Required | Description  
---|---|---|---  
content | String | Yes | Text content to analyze  
format_hint | String | No | Document format hint: `auto`, `markdown`, `asciidoc` (default: `auto`)  
content_type | String | No | Content classification: `concept`, `procedure`, `reference` (default: `concept`)  
session_id | String | No | Session identifier for WebSocket progress updates  
confidence_threshold | Number | No | Error confidence threshold (0.0-1.0)  
include_confidence_details | Boolean | No | Include detailed confidence information (default: `true`)  
document_id | String | No | Database document identifier  
analysis_id | String | No | Database analysis identifier  
  
#### Response
[code] 
    {
      "success": true,
      "analysis": {
        "errors": [
          {
            "type": "passive_voice",
            "message": "Consider using active voice",
            "text": "The system was configured",
            "suggestion": "We configured the system",
            "start": 45,
            "end": 67,
            "confidence": 0.85,
            "severity": "medium",
            "category": "style"
          }
        ],
        "statistics": {
          "word_count": 250,
          "sentence_count": 15,
          "avg_sentence_length": 16.7,
          "readability_scores": {
            "flesch_reading_ease": 65.2,
            "flesch_kincaid_grade": 9.5,
            "gunning_fog": 10.2,
            "coleman_liau": 9.8,
            "automated_readability_index": 9.1
          },
          "total_errors": 12,
          "high_confidence_errors": 8,
          "medium_confidence_errors": 3,
          "low_confidence_errors": 1
        },
        "modular_compliance": {
          "module_type": "concept",
          "compliance_score": 0.85,
          "missing_elements": [],
          "recommendations": []
        },
        "processing_time": 2.34,
        "content_type": "concept"
      },
      "structural_blocks": [
        {
          "id": "block_1",
          "type": "heading",
          "content": "Introduction",
          "level": 1,
          "errors": []
        },
        {
          "id": "block_2",
          "type": "paragraph",
          "content": "This is a paragraph with content...",
          "errors": [
            {
              "type": "sentence_length",
              "message": "Sentence is too long",
              "confidence": 0.75
            }
          ]
        }
      ],
      "confidence_details": {
        "confidence_system_available": true,
        "threshold_range": {
          "min": 0.0,
          "max": 1.0,
          "default": 0.43
        },
        "confidence_levels": {
          "HIGH": {
            "threshold": 0.7,
            "description": "High confidence errors - very likely to be correct"
          },
          "MEDIUM": {
            "threshold": 0.5,
            "description": "Medium confidence errors - likely to be correct"
          },
          "LOW": {
            "threshold": 0.0,
            "description": "Low confidence errors - may need review"
          }
        }
      },
      "backward_compatible": true,
      "session_id": "session_12345"
    }
[/code]

## AI Rewriting

### Rewrite Block

AI-powered rewriting of individual content blocks.
[code] 
    POST /rewrite-block
[/code]

#### Request Body
[code] 
    {
      "block_content": "Content to be rewritten...",
      "block_errors": [
        {
          "type": "passive_voice",
          "message": "Consider using active voice",
          "confidence": 0.85
        }
      ],
      "block_type": "paragraph",
      "block_id": "block_2",
      "session_id": "session_12345"
    }
[/code]

#### Response
[code] 
    {
      "success": true,
      "original_content": "Original block content...",
      "rewritten_content": "Improved block content...",
      "errors_fixed": 3,
      "improvements_made": [
        {
          "type": "passive_voice",
          "description": "Converted to active voice"
        },
        {
          "type": "sentence_structure",
          "description": "Simplified complex sentences"
        }
      ],
      "confidence_score": 0.89,
      "applicable_stations": ["grammar", "clarity", "conciseness"],
      "block_type": "paragraph",
      "assembly_line_used": true,
      "block_id": "block_2",
      "session_id": "session_12345",
      "processing_time": 3.45
    }
[/code]

### Refine Content

Second-pass AI refinement for enhanced content quality.
[code] 
    POST /refine
[/code]

#### Request Body
[code] 
    {
      "content": "First-pass rewritten content...",
      "original_errors": [
        {
          "type": "clarity",
          "message": "Content needs clarification"
        }
      ],
      "first_pass_result": {
        "rewritten_content": "First pass result...",
        "improvements_made": []
      }
    }
[/code]

#### Response
[code] 
    {
      "success": true,
      "original_content": "First-pass content...",
      "refined_content": "Final refined content...",
      "total_improvements": 5,
      "refinement_quality": 0.92,
      "processing_time": 2.67
    }
[/code]

## Report Generation

### Generate PDF Report

Create a comprehensive PDF analysis report.
[code] 
    POST /generate-pdf-report
[/code]

#### Request Body
[code] 
    {
      "analysis": {
        "errors": [],
        "statistics": {},
        "modular_compliance": {}
      },
      "content": "Original document content...",
      "structural_blocks": []
    }
[/code]

#### Response

Returns a downloadable PDF file with comprehensive analysis results.
[code] 
    Content-Type: application/pdf
    Content-Disposition: attachment; filename="writing_analytics_report_20241215_143022.pdf"
[/code]

## User Interface Routes

### Home Page
[code] 
    GET /
[/code]

Main application interface for document upload and analysis.

### Analysis Page
[code] 
    GET /analyze
[/code]

Dedicated analysis interface page.

### Create Blogs
[code] 
    GET /create-blogs
[/code]

Blog creation interface (experimental feature).

## Feedback System

### Submit Feedback
[code] 
    POST /api/feedback
[/code]

#### Request Body
[code] 
    {
      "feedback_type": "rule_accuracy",
      "rule_id": "passive_voice",
      "error_text": "The system was configured",
      "user_rating": 4,
      "user_comment": "Good catch, but suggestion could be better",
      "context": {
        "document_type": "technical",
        "content_length": 250
      }
    }
[/code]

### Get Feedback Statistics
[code] 
    GET /api/feedback/stats
[/code]

#### Response
[code] 
    {
      "total_feedback": 1250,
      "average_rating": 4.2,
      "rule_performance": {
        "passive_voice": {
          "total": 300,
          "average_rating": 4.5
        }
      }
    }
[/code]

### Get Feedback Insights
[code] 
    GET /api/feedback/insights
[/code]

Returns actionable insights from user feedback data.

## Analytics

### Session Analytics
[code] 
    GET /api/analytics/session?session_id=session_12345
[/code]

Detailed analytics for a specific session.

### Rule Analytics
[code] 
    GET /api/analytics/rules
[/code]

Performance metrics for all style rules.

### Model Usage Analytics
[code] 
    GET /api/analytics/model-usage
[/code]

AI model usage statistics and performance metrics.

## Health Check

### Application Health
[code] 
    GET /health
[/code]

#### Response
[code] 
    {
      "status": "healthy",
      "services": {
        "document_processor": "available",
        "style_analyzer": "available",
        "ai_rewriter": "available",
        "ollama": "available",
        "database": "available"
      },
      "version": "1.0.0",
      "uptime": 3600,
      "timestamp": "2024-01-15T10:30:00Z"
    }
[/code]

## WebSocket API

### Connection

Connect to the WebSocket endpoint for real-time updates.
[code] 
    const socket = io('http://localhost:5000');
[/code]

### Events

#### Client to Server

**join_session**
[code] 
    socket.emit('join_session', {
      session_id: 'session_12345'
    });
[/code]

**start_analysis**
[code] 
    socket.emit('start_analysis', {
      content: 'Text to analyze...',
      options: {
        content_type: 'concept',
        confidence_threshold: 0.5
      }
    });
[/code]

#### Server to Client

**progress**
[code] 
    socket.on('progress', (data) => {
      console.log('Progress:', data.progress);
      console.log('Stage:', data.stage);
      console.log('Message:', data.message);
    });
[/code]

**completion**
[code] 
    socket.on('completion', (data) => {
      console.log('Task completed:', data.success);
      console.log('Results:', data.data);
    });
[/code]

**block_processing_start**
[code] 
    socket.on('block_processing_start', (data) => {
      console.log('Block processing started:', data.block_id);
    });
[/code]

**block_processing_complete**
[code] 
    socket.on('block_processing_complete', (data) => {
      console.log('Block processing complete:', data.block_id);
      console.log('Improvements:', data.improvements_made);
    });
[/code]

## Error Handling

### Error Response Format
[code] 
    {
      "success": false,
      "error": "Error description",
      "details": {
        "error_code": "INVALID_FORMAT",
        "additional_info": {}
      },
      "timestamp": "2024-01-15T10:30:00Z"
    }
[/code]

### Common Error Codes

Code | HTTP Status | Description  
---|---|---  
INVALID_FILE_FORMAT | 400 | Unsupported file format  
FILE_TOO_LARGE | 413 | File exceeds 16MB limit  
NO_CONTENT_PROVIDED | 400 | Required content parameter missing  
INVALID_CONTENT_TYPE | 400 | Content type must be: concept, procedure, reference  
BLOCK_ID_REQUIRED | 400 | Block ID required for block operations  
ANALYSIS_FAILED | 500 | Internal error during analysis  
AI_REWRITER_UNAVAILABLE | 503 | AI rewriting service unavailable  
OLLAMA_CONNECTION_ERROR | 503 | Local Ollama service not accessible  
DATABASE_ERROR | 500 | Database operation failed  
  
## Rate Limiting

  * **File uploads** : 50 requests per minute per IP

  * **API calls** : 200 requests per minute per IP

  * **AI rewriting** : 10 requests per minute per IP

  * **WebSocket connections** : 10 concurrent connections per IP

## Integration Examples

### Complete Analysis Workflow
[code] 
    // 1. Upload document
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    const uploadResponse = await fetch('/upload', {
      method: 'POST',
      body: formData
    });
    
    const uploadResult = await uploadResponse.json();
    
    // 2. Analyze content with real-time progress
    const socket = io();
    const sessionId = 'session_' + Date.now();
    
    socket.emit('join_session', { session_id: sessionId });
    
    socket.on('progress', (data) => {
      updateProgressBar(data.progress);
    });
    
    const analysisResponse = await fetch('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: uploadResult.text,
        session_id: sessionId,
        content_type: 'concept',
        confidence_threshold: 0.5
      })
    });
    
    const analysisResult = await analysisResponse.json();
    
    // 3. Rewrite problematic blocks
    for (const block of analysisResult.structural_blocks) {
      if (block.errors.length > 0) {
        const rewriteResponse = await fetch('/rewrite-block', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            block_content: block.content,
            block_errors: block.errors,
            block_type: block.type,
            block_id: block.id,
            session_id: sessionId
          })
        });
    
        const rewriteResult = await rewriteResponse.json();
        // Handle rewrite result...
      }
    }
    
    // 4. Generate comprehensive report
    const reportResponse = await fetch('/generate-pdf-report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        analysis: analysisResult.analysis,
        content: uploadResult.text,
        structural_blocks: analysisResult.structural_blocks
      })
    });
    
    // Download PDF report
    const blob = await reportResponse.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'analysis_report.pdf';
    a.click();
[/code]

### Python Integration Example
[code] 
    import requests
    import json
    
    # Upload and analyze document
    with open('document.pdf', 'rb') as f:
        upload_response = requests.post(
            'http://localhost:5000/upload',
            files={'file': f}
        )
    
    upload_data = upload_response.json()
    
    # Analyze content
    analysis_response = requests.post(
        'http://localhost:5000/analyze',
        json={
            'content': upload_data['text'],
            'content_type': 'procedure',
            'confidence_threshold': 0.7
        }
    )
    
    analysis_data = analysis_response.json()
    
    print(f"Found {len(analysis_data['analysis']['errors'])} issues")
    print(f"Readability score: {analysis_data['analysis']['statistics']['readability_scores']['flesch_reading_ease']}")
    
    # Rewrite blocks with errors
    for block in analysis_data['structural_blocks']:
        if block['errors']:
            rewrite_response = requests.post(
                'http://localhost:5000/rewrite-block',
                json={
                    'block_content': block['content'],
                    'block_errors': block['errors'],
                    'block_type': block['type'],
                    'block_id': block['id']
                }
            )
    
            rewrite_data = rewrite_response.json()
            if rewrite_data['success']:
                print(f"Block {block['id']} improved: {rewrite_data['errors_fixed']} errors fixed")
[/code]

## Changelog

### v1.0.0 (Current)

  * **Core Features** :

    * Multi-format document processing (PDF, DOCX, Markdown, AsciiDoc, DITA, TXT)

    * Comprehensive style analysis with 45+ rules

    * AI-powered block-level rewriting with assembly line processing

    * Real-time WebSocket progress updates

    * Confidence-based error filtering

    * PDF report generation

    * Database integration for session and feedback management

  * **AI Capabilities** :

    * Local Ollama integration for privacy-first AI

    * Two-pass iterative improvement system

    * Block-level contextual rewriting

    * Confidence scoring for AI improvements

  * **Analysis Features** :

    * Multiple readability metrics (Flesch, Gunning Fog, SMOG, etc.)

    * Structural document parsing with format awareness

    * Ambiguity detection system

    * Modular compliance checking

    * Content type classification (concept, procedure, reference)

  * **Developer Features** :

    * Comprehensive REST API with WebSocket support

    * Session-based progress tracking

    * Feedback system for continuous improvement

    * Analytics endpoints for performance monitoring

    * Health check endpoints for monitoring

### Upcoming Features

  * Custom rule creation API

  * Batch document processing

  * Webhook notifications for long-running operations

  * Enhanced ambiguity resolution suggestions

  * Integration with external style guides

  * Multi-language support

  * Advanced caching for improved performance

Last updated 2025-11-25 17:06:03 +0530 
