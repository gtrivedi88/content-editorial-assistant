"""
API Routes Module
Contains all Flask route handlers for the web application.
Handles file uploads, text analysis, AI rewriting, and health checks.
"""

import os
import time
import logging
from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from src.config import Config
from .websocket_handlers import emit_progress, emit_completion

logger = logging.getLogger(__name__)


def setup_routes(app, document_processor, style_analyzer, ai_rewriter):
    """Setup all API routes for the Flask application."""
    
    @app.route('/')
    def index():
        """Main application page."""
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error rendering index page: {e}")
            try:
                return render_template('error.html', error_message="Failed to load application"), 500
            except Exception as e2:
                logger.error(f"Error rendering error page: {e2}")
                return f"<h1>Application Error</h1><p>Failed to load application: {e}</p><p>Template error: {e2}</p>", 500
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Handle file upload and text extraction."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file selected'}), 400
            
            file = request.files['file']
            if file.filename == '' or file.filename is None:
                return jsonify({'error': 'No file selected'}), 400
            
            if file and document_processor.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Ensure upload directory exists
                upload_folder = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                # Extract text
                content = document_processor.extract_text(filepath)
                
                # Clean up file
                try:
                    os.remove(filepath)
                except:
                    pass  # Don't fail if cleanup fails
                
                if content:
                    return jsonify({
                        'success': True,
                        'content': content,
                        'filename': filename
                    })
                else:
                    return jsonify({'error': 'Failed to extract text from file'}), 400
            else:
                return jsonify({'error': 'File type not supported'}), 400
                
        except RequestEntityTooLarge:
            return jsonify({'error': 'File too large'}), 413
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    @app.route('/analyze', methods=['POST'])
    def analyze_content():
        """Analyze text content for style issues with real-time progress."""
        try:
            data = request.get_json()
            content = data.get('content', '')
            format_hint = data.get('format_hint', 'auto')
            session_id = data.get('session_id', '') if data else ''
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # If no session_id provided, generate one for this request
            if not session_id or not session_id.strip():
                import uuid
                session_id = str(uuid.uuid4())
                logger.info(f"Generated session ID for analysis: {session_id}")
            
            # Send initial progress
            emit_progress(session_id, 'analysis_start', 'Starting text analysis...',
                         'Initializing SpaCy NLP processor', 10)
            
            # Perform block-aware analysis with structural parsing
            emit_progress(session_id, 'structural_parsing', 'Parsing document structure...',
                         'Identifying headings, paragraphs, code blocks, etc.', 20)
            
            emit_progress(session_id, 'spacy_processing', 'Processing with SpaCy NLP...',
                         'Detecting sentence structure and style issues', 40)
            
            emit_progress(session_id, 'block_analysis', 'Analyzing individual blocks...',
                         'Running style analysis on each document element', 60)
            
            # Use the new block-aware analysis method
            analysis_result = style_analyzer.analyze_with_blocks(content, format_hint=format_hint)
            
            analysis = analysis_result['analysis']
            structural_blocks = analysis_result['structural_blocks']
            has_structure = analysis_result['has_structure']
            
            emit_progress(session_id, 'metrics_calculation', 'Calculating readability metrics...',
                         'Computing Flesch, Fog, SMOG, and other scores', 80)
            
            # Add some processing time for metrics
            time.sleep(0.5)  # Small delay to show progress
            
            emit_progress(session_id, 'analysis_complete', 'Analysis completed successfully!',
                         f'Found {len(analysis.get("errors", []))} style issues', 100)
            
            response_data = {
                'success': True,
                'analysis': analysis,
                'session_id': session_id,
                'content': content
            }
            
            # Include structural blocks if available
            if structural_blocks:
                response_data['structural_blocks'] = structural_blocks
            response_data['has_structure'] = has_structure
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            session_id = locals().get('session_id', '')
            emit_completion(session_id, False, error=f'Analysis failed: {str(e)}')
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500
    
    @app.route('/rewrite', methods=['POST'])
    def rewrite_content():
        """Generate AI-powered rewrite suggestions (Pass 1)."""
        try:
            data = request.get_json()
            content = data.get('content', '')
            errors = data.get('errors', [])
            context = data.get('context', 'sentence')
            session_id = data.get('session_id', '') if data else ''
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # If no session_id provided, generate one for this request
            if not session_id or not session_id.strip():
                import uuid
                session_id = str(uuid.uuid4())
                logger.info(f"Generated session ID for rewrite: {session_id}")
            
            # Send initial progress
            emit_progress(session_id, 'rewrite_start', 'Starting AI rewrite process...',
                         f'Processing {len(errors)} detected issues', 5)
            
            # Create progress callback function
            def progress_callback(step, status, detail, progress):
                emit_progress(session_id, step, status, detail, progress)
            
            # Check if we have the structural rewriter
            if hasattr(ai_rewriter, 'rewrite_document_with_structure_preservation'):
                # Use structural rewriter for better document handling
                emit_progress(session_id, 'structural_rewrite', 'Using structural document rewriter...',
                             'Preserving document format and structure', 10)
                
                # Detect format from content
                format_hint = 'asciidoc' if content.strip().startswith('=') else 'auto'
                
                rewrite_result = ai_rewriter.rewrite_document_with_structure_preservation(
                    content=content,
                    format_hint=format_hint,
                    session_id=session_id,
                    pass_number=1
                )
                
                if rewrite_result.get('error'):
                    emit_completion(session_id, False, error=rewrite_result['error'])
                    return jsonify({'error': rewrite_result['error']}), 500
                
                # Map structural rewriter results to expected format
                response_data = {
                    'success': True,
                    'original': content,
                    'rewritten': rewrite_result.get('rewritten_text', ''),
                    'rewritten_text': rewrite_result.get('rewritten_text', ''),
                    'improvements': rewrite_result.get('improvements', []),
                    'confidence': rewrite_result.get('confidence', 0.0),
                    'model_used': f"structural_{rewrite_result.get('parsing_method', 'unknown')}",
                    'pass_number': 1,
                    'can_refine': True,
                    'original_errors': errors,
                    'session_id': session_id,
                    'errors_fixed': rewrite_result.get('errors_fixed', 0),
                    'original_errors': rewrite_result.get('original_errors', len(errors)),
                    'passes_completed': rewrite_result.get('passes_completed', 1),
                    'assembly_line_used': rewrite_result.get('assembly_line_used', True),
                    'structural_parsing_used': True
                }
            else:
                # Fallback to simple rewriter
                emit_progress(session_id, 'fallback_rewrite', 'Using fallback rewriter...',
                             'Simple text-based rewriting', 10)
                
                # Get system info for AI rewriter configuration
                system_info = ai_rewriter.get_system_info()
                model_info = system_info.get('model_info', {})
                
                rewrite_result = ai_rewriter.rewrite(content, errors, context)
                
                # Add pass number and refinement capability
                rewrite_result['pass_number'] = 1
                rewrite_result['can_refine'] = True
                
                response_data = {
                    'success': True,
                    'original': content,
                    'rewritten': rewrite_result.get('rewritten_text', ''),
                    'rewritten_text': rewrite_result.get('rewritten_text', ''),
                    'improvements': rewrite_result.get('improvements', []),
                    'confidence': rewrite_result.get('confidence', 0.0),
                    'model_used': rewrite_result.get('model_used', 'unknown'),
                    'pass_number': rewrite_result.get('pass_number', 1),
                    'can_refine': rewrite_result.get('can_refine', False),
                    'original_errors': errors,
                    'errors_fixed': rewrite_result.get('errors_fixed', 0),
                    'passes_completed': rewrite_result.get('passes_completed', 1), 
                    'assembly_line_used': rewrite_result.get('assembly_line_used', True),
                    'session_id': session_id,
                    'structural_parsing_used': False
                }
            
            emit_completion(session_id, True, data=response_data)
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Rewrite error: {str(e)}")
            session_id = locals().get('session_id', '')
            emit_completion(session_id, False, error=f'Rewrite failed: {str(e)}')
            return jsonify({'error': f'Rewrite failed: {str(e)}'}), 500
    
    @app.route('/refine', methods=['POST'])
    def refine_content():
        """Generate AI-powered refinement (Pass 2)."""
        try:
            data = request.get_json()
            first_pass_result = data.get('first_pass_result', '')
            original_errors = data.get('original_errors', [])
            context = data.get('context', 'sentence')
            session_id = data.get('session_id', '') if data else ''
            
            if not first_pass_result:
                return jsonify({'error': 'No first pass result provided'}), 400
            
            # If no session_id provided, generate one for this request
            if not session_id or not session_id.strip():
                import uuid
                session_id = str(uuid.uuid4())
                logger.info(f"Generated session ID for refine: {session_id}")
            
            # Send initial progress
            emit_progress(session_id, 'refine_start', 'Starting AI refinement process...',
                         'AI reviewing and polishing the first pass result', 5)
            
            # Create progress callback function
            def progress_callback(step, status, detail, progress):
                emit_progress(session_id, step, status, detail, progress)
            
            # Perform Pass 2 refinement
            refinement_result = ai_rewriter.refine_text(first_pass_result, original_errors, context)
            
            return jsonify({
                'success': True,
                'first_pass': first_pass_result,
                'refined': refinement_result.get('rewritten_text', ''),
                'rewritten_text': refinement_result.get('rewritten_text', ''),
                'improvements': refinement_result.get('improvements', []),
                'confidence': refinement_result.get('confidence', 0.0),
                'model_used': refinement_result.get('model_used', 'unknown'),
                'pass_number': refinement_result.get('pass_number', 2),
                'can_refine': refinement_result.get('can_refine', False),
                'session_id': session_id  # Return session_id to frontend
            })
            
        except Exception as e:
            logger.error(f"Refinement error: {str(e)}")
            session_id = locals().get('session_id', '')
            emit_completion(session_id, False, error=f'Refinement failed: {str(e)}')
            return jsonify({'error': f'Refinement failed: {str(e)}'}), 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint to verify service status."""
        try:
            # Check if Ollama is available when configured
            ollama_status = "not_configured"
            if Config.is_ollama_enabled():
                try:
                    import requests
                    response = requests.get(f"{Config.OLLAMA_BASE_URL}/api/tags", timeout=5)
                    if response.status_code == 200:
                        models = response.json().get('models', [])
                        model_names = [m['name'] for m in models]
                        ollama_status = "available" if Config.OLLAMA_MODEL in model_names else "model_not_found"
                    else:
                        ollama_status = "service_unavailable"
                except:
                    ollama_status = "connection_failed"
            
            # Check service availability
            document_processor_status = 'ready' if hasattr(document_processor, 'extract_text') else 'fallback'
            style_analyzer_status = 'ready' if hasattr(style_analyzer, 'analyze') else 'fallback'
            ai_rewriter_status = 'ready' if hasattr(ai_rewriter, 'rewrite') else 'fallback'
            
            return jsonify({
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'ai_model_type': getattr(Config, 'AI_MODEL_TYPE', 'unknown'),
                'ollama_status': ollama_status,
                'ollama_model': getattr(Config, 'OLLAMA_MODEL', None) if Config.is_ollama_enabled() else None,
                'services': {
                    'document_processor': document_processor_status,
                    'style_analyzer': style_analyzer_status,
                    'ai_rewriter': ai_rewriter_status,
                    'ollama': ollama_status
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500 