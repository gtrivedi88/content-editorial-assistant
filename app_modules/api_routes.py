"""
API Routes Module
Contains all Flask route handlers for the web application.
Handles file uploads, text analysis, AI rewriting, and health checks.
"""

import os
import time
import logging
from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from io import BytesIO

from config import Config
from .websocket_handlers import emit_progress, emit_completion

logger = logging.getLogger(__name__)


def setup_routes(app, document_processor, style_analyzer, ai_rewriter):
    """Setup all API routes for the Flask application."""
    
    # Add request logging middleware
    @app.before_request
    def log_request_info():
        """Log all incoming requests for debugging."""
        print(f"\n📥 INCOMING REQUEST: {request.method} {request.path}")
        if request.method == 'POST':
            print(f"   📋 Content-Type: {request.content_type}")
            print(f"   📋 Content-Length: {request.content_length}")
            if request.is_json:
                print(f"   📋 JSON Data Keys: {list(request.json.keys()) if request.json else 'None'}")
        print("")
    
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
        """Analyze text content for style issues with confidence data and real-time progress."""
        start_time = time.time()  # Track processing time
        try:
            data = request.get_json()
            content = data.get('content', '')
            format_hint = data.get('format_hint', 'auto')
            content_type = data.get('content_type', 'concept')  # NEW: Add content type
            session_id = data.get('session_id', '') if data else ''
        
            # Enhanced: Support confidence threshold parameter
            confidence_threshold = data.get('confidence_threshold', None)
            include_confidence_details = data.get('include_confidence_details', True)
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # Validate content_type
            valid_content_types = ['concept', 'procedure', 'reference']
            if content_type not in valid_content_types:
                return jsonify({'error': f'Invalid content_type. Must be one of: {valid_content_types}'}), 400
                
            # If no session_id provided, generate one for this request
            if not session_id or not session_id.strip():
                import uuid
                session_id = str(uuid.uuid4())
            
            # Start analysis with progress updates
            logger.info(f"Starting analysis for session {session_id} with content_type={content_type} and confidence_threshold={confidence_threshold}")
            emit_progress(session_id, 'analysis_start', 'Initializing analysis...', 'Setting up analysis pipeline', 10)
            
            # Enhanced: Configure analyzer with confidence threshold if provided
            if confidence_threshold is not None:
                # Temporarily adjust the confidence threshold for this request
                original_threshold = style_analyzer.structural_analyzer.confidence_threshold
                style_analyzer.structural_analyzer.confidence_threshold = confidence_threshold
                style_analyzer.structural_analyzer.rules_registry.set_confidence_threshold(confidence_threshold)
            
            # Analyze with structural blocks AND modular compliance
            emit_progress(session_id, 'style_analysis', 'Running style analysis...', 'Checking grammar and style rules', 40)
            analysis_result = style_analyzer.analyze_with_blocks(content, format_hint, content_type=content_type)
            analysis = analysis_result.get('analysis', {})
            structural_blocks = analysis_result.get('structural_blocks', [])
            
            # Check if modular compliance was included in results
            if 'modular_compliance' in analysis_result:
                emit_progress(session_id, 'compliance_check', 'Modular compliance analyzed', f'Validated {content_type} module requirements', 70)
                analysis['modular_compliance'] = analysis_result['modular_compliance']
            
            # Enhanced: Restore original threshold if it was modified
            if confidence_threshold is not None:
                style_analyzer.structural_analyzer.confidence_threshold = original_threshold
                style_analyzer.structural_analyzer.rules_registry.set_confidence_threshold(original_threshold)
            
            emit_progress(session_id, 'analysis_complete', 'Analysis complete!', f'Analysis completed successfully', 100)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            analysis['processing_time'] = processing_time
            analysis['content_type'] = content_type  # Include content type in results
            
            logger.info(f"Analysis completed in {processing_time:.2f}s for session {session_id}")
            
            # Enhanced: Prepare confidence metadata
            confidence_metadata = {
                'confidence_threshold_used': confidence_threshold or analysis.get('confidence_threshold', 0.43),
                'enhanced_validation_enabled': analysis.get('enhanced_validation_enabled', False),
                'confidence_filtering_applied': confidence_threshold is not None,
                'content_type': content_type  # Include content type in metadata
            }
            
            # Enhanced: Add validation performance if available
            if analysis.get('validation_performance'):
                confidence_metadata['validation_performance'] = analysis.get('validation_performance')
            
            # Enhanced: Add enhanced error statistics if available
            if analysis.get('enhanced_error_stats'):
                confidence_metadata['enhanced_error_stats'] = analysis.get('enhanced_error_stats')
            
            # Return enhanced results with modular compliance data
            response_data = {
                'success': True,
                'analysis': analysis,
                'processing_time': processing_time,
                'session_id': session_id,
                'content_type': content_type,  # Include content type in response
                'confidence_metadata': confidence_metadata,
                'api_version': '2.0'  # Indicate enhanced API version
            }
            
            # Include detailed confidence information if requested
            if include_confidence_details:
                response_data['confidence_details'] = {
                    'confidence_system_available': True,
                    'threshold_range': {'min': 0.0, 'max': 1.0, 'default': 0.43},
                    'confidence_levels': {
                        'HIGH': {'threshold': 0.7, 'description': 'High confidence errors - very likely to be correct'},
                        'MEDIUM': {'threshold': 0.5, 'description': 'Medium confidence errors - likely to be correct'},
                        'LOW': {'threshold': 0.0, 'description': 'Low confidence errors - may need review'}
                    }
                }
            
            # Include structural blocks if available
            if structural_blocks:
                response_data['structural_blocks'] = structural_blocks
                
            # Enhanced: Add backward compatibility flag
            response_data['backward_compatible'] = True
            
            emit_completion(session_id, True, response_data)
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Analysis error for session {session_id}: {str(e)}")
            error_response = {
                'success': False,
                'error': f'Analysis failed: {str(e)}',
                'session_id': session_id
            }
            emit_completion(session_id, False, error_response)
            return jsonify(error_response), 500
    
    @app.route('/generate-pdf-report', methods=['POST'])
    def generate_pdf_report():
        """Generate a comprehensive PDF report of the writing analysis."""
        try:
            data = request.get_json()
            
            # Extract required data
            analysis_data = data.get('analysis', {})
            content = data.get('content', '')
            structural_blocks = data.get('structural_blocks', [])
            
            if not analysis_data:
                return jsonify({'error': 'No analysis data provided'}), 400
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # Import PDF generator (lazy import to avoid startup delays)
            try:
                from .pdf_report_generator import PDFReportGenerator
            except ImportError as e:
                logger.error(f"Failed to import PDF generator: {e}")
                return jsonify({'error': 'PDF generation not available - missing dependencies'}), 500
            
            # Generate PDF report
            logger.info("Generating PDF report...")
            pdf_generator = PDFReportGenerator()
            
            pdf_bytes = pdf_generator.generate_report(
                analysis_data=analysis_data,
                content=content,
                structural_blocks=structural_blocks if structural_blocks else None
            )
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"writing_analytics_report_{timestamp}.pdf"
            
            # Return PDF as downloadable file
            pdf_buffer = BytesIO(pdf_bytes)
            pdf_buffer.seek(0)
            
            logger.info(f"PDF report generated successfully ({len(pdf_bytes)} bytes)")
            
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}")
            return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
    
    @app.route('/rewrite-block', methods=['POST'])
    def rewrite_block():
        """AI-powered single block rewriting."""
        start_time = time.time()
        try:
            data = request.get_json()
            block_content = data.get('block_content', '')
            block_errors = data.get('block_errors', [])
            block_type = data.get('block_type', 'paragraph')
            block_id = data.get('block_id', '')
            session_id = data.get('session_id', '')
            
            print(f"\n🔍 DEBUG API ROUTE: /rewrite-block")
            print(f"   📋 Block ID: {block_id}")
            print(f"   📋 Session ID: {session_id}")
            print(f"   📋 Block Type: {block_type}")
            print(f"   📋 Content Length: {len(block_content)}")
            print(f"   📋 Errors Count: {len(block_errors)}")
            print(f"   📋 Content Preview: {repr(block_content[:100])}")
            
            # Validate required inputs
            if not block_content or not block_content.strip():
                print(f"   ❌ No block content provided")
                return jsonify({'error': 'No block content provided'}), 400
            
            if not block_id:
                print(f"   ❌ Block ID is required")
                return jsonify({'error': 'Block ID is required'}), 400
            
            if not block_errors:
                print(f"   ⚠️  No errors provided - returning original content")
            
            logger.info(f"Starting block rewrite for session {session_id}, block {block_id}, type: {block_type}")
            
            # Emit progress start via WebSocket
            print(f"   📡 Emitting initial progress update...")
            if session_id:
                emit_progress(session_id, 'block_processing_start', 
                            f'Starting rewrite for {block_type}', 
                            f'Processing block {block_id}', 0)
                print(f"   ✅ Initial progress update emitted to session: {session_id}")
            else:
                # If no session_id provided, broadcast to all connected clients
                emit_progress('', 'block_processing_start', 
                            f'Starting rewrite for {block_type}', 
                            f'Processing block {block_id}', 0)
                print(f"   ✅ Initial progress update broadcasted to all sessions")
            
            # Debug: Check ai_rewriter structure
            print(f"   🔍 DEBUG AI Rewriter Structure:")
            print(f"      ai_rewriter type: {type(ai_rewriter)}")
            print(f"      hasattr(ai_rewriter, 'ai_rewriter'): {hasattr(ai_rewriter, 'ai_rewriter')}")
            if hasattr(ai_rewriter, 'ai_rewriter'):
                print(f"      ai_rewriter.ai_rewriter type: {type(ai_rewriter.ai_rewriter)}")
                print(f"      hasattr(ai_rewriter.ai_rewriter, 'assembly_line'): {hasattr(ai_rewriter.ai_rewriter, 'assembly_line')}")
                if hasattr(ai_rewriter.ai_rewriter, 'assembly_line'):
                    print(f"      assembly_line type: {type(ai_rewriter.ai_rewriter.assembly_line)}")
                    print(f"      assembly_line progress_callback: {getattr(ai_rewriter.ai_rewriter.assembly_line, 'progress_callback', 'NOT_FOUND')}")
            print(f"      hasattr(ai_rewriter, 'assembly_line'): {hasattr(ai_rewriter, 'assembly_line')}")
            
            # Process single block through assembly line
            if hasattr(ai_rewriter, 'ai_rewriter') and hasattr(ai_rewriter.ai_rewriter, 'assembly_line'):
                print(f"   🏭 Using DocumentRewriter -> AIRewriter -> AssemblyLine path")
                # Full DocumentRewriter with assembly line support - PASS session_id and block_id for live updates
                result = ai_rewriter.ai_rewriter.assembly_line.apply_block_level_assembly_line_fixes(
                    block_content, block_errors, block_type, session_id=session_id, block_id=block_id
                )
                print(f"   ✅ Assembly line processing completed")
            elif hasattr(ai_rewriter, 'assembly_line'):
                print(f"   🏭 Using Direct AIRewriter -> AssemblyLine path")
                # Direct AIRewriter with assembly line support - PASS session_id and block_id for live updates
                result = ai_rewriter.assembly_line.apply_block_level_assembly_line_fixes(
                    block_content, block_errors, block_type, session_id=session_id, block_id=block_id
                )
                print(f"   ✅ Assembly line processing completed")
            else:
                print(f"   ⚠️  Using fallback SimpleAIRewriter path")
                # Fallback SimpleAIRewriter - use basic rewrite method
                result = ai_rewriter.rewrite(block_content, block_errors, block_type)
                # Add missing fields for consistency
                result.update({
                    'applicable_stations': ['fallback'],
                    'block_type': block_type,
                    'assembly_line_used': False
                })
                print(f"   ✅ Fallback processing completed")
            
            # Add request metadata
            processing_time = time.time() - start_time
            result.update({
                'block_id': block_id,
                'session_id': session_id,
                'processing_time': processing_time,
                'success': 'error' not in result
            })
            
            # Emit completion via WebSocket
            if session_id:
                emit_completion(session_id, 'block_processing_complete', result)
            
            logger.info(f"Block rewrite completed in {processing_time:.2f}s - {result.get('errors_fixed', 0)} errors fixed")
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Block rewrite error: {str(e)}")
            error_result = {
                'error': f'Block rewrite failed: {str(e)}',
                'success': False,
                'block_id': data.get('block_id', '') if 'data' in locals() else '',
                'session_id': data.get('session_id', '') if 'data' in locals() else ''
            }
            return jsonify(error_result), 500


    
    @app.route('/refine', methods=['POST'])
    def refine_content():
        """AI-powered content refinement (Pass 2)."""
        start_time = time.time()
        try:
            data = request.get_json()
            first_pass_result = data.get('first_pass_result', '')
            original_errors = data.get('original_errors', [])
            session_id = data.get('session_id', '')
            
            if not first_pass_result:
                return jsonify({'error': 'No first pass result provided'}), 400
            
            logger.info(f"Starting refinement for session {session_id}")
            
            result = ai_rewriter.refine_content(first_pass_result, original_errors)
            
            processing_time = time.time() - start_time
            result['processing_time'] = processing_time
            
            logger.info(f"Refinement completed in {processing_time:.2f}s")
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Refinement error: {str(e)}")
            return jsonify({'error': f'Refinement failed: {str(e)}'}), 500
    
    @app.route('/create-blogs')
    def create_blogs():
        """Blog creation page with form-driven UI."""
        try:
            return render_template('create_blogs.html')
        except Exception as e:
            logger.error(f"Error rendering create blogs page: {e}")
            try:
                return render_template('error.html', error_message="Failed to load blog creation page"), 500
            except Exception as e2:
                logger.error(f"Error rendering error page: {e2}")
                return f"<h1>Application Error</h1><p>Failed to load blog creation page: {e}</p><p>Template error: {e2}</p>", 500
    
    @app.route('/api/feedback', methods=['POST'])
    def submit_feedback():
        """Submit user feedback on error accuracy."""
        try:
            from .feedback_storage import feedback_storage
            
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Extract request metadata
            user_agent = request.headers.get('User-Agent')
            ip_address = request.remote_addr
            
            # Store feedback
            success, message, feedback_id = feedback_storage.store_feedback(
                data, user_agent=user_agent, ip_address=ip_address
            )
            
            if success:
                response_data = {
                    'success': True,
                    'message': message,
                    'feedback_id': feedback_id,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"Feedback submitted successfully: {feedback_id}")
                return jsonify(response_data), 201
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Feedback submission error: {str(e)}")
            return jsonify({'error': f'Feedback submission failed: {str(e)}'}), 500
    
    @app.route('/api/feedback/stats', methods=['GET'])
    def get_feedback_stats():
        """Get feedback statistics."""
        try:
            from .feedback_storage import feedback_storage
            
            # Get query parameters
            session_id = request.args.get('session_id')
            days_back = request.args.get('days_back', default=7, type=int)
            
            # Validate days_back parameter
            if days_back < 1 or days_back > 365:
                return jsonify({'error': 'days_back must be between 1 and 365'}), 400
            
            # Get statistics
            stats = feedback_storage.get_feedback_stats(session_id=session_id, days_back=days_back)
            
            response_data = {
                'success': True,
                'statistics': stats,
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Feedback stats error: {str(e)}")
            return jsonify({'error': f'Failed to retrieve feedback stats: {str(e)}'}), 500
    
    @app.route('/api/feedback/insights', methods=['GET'])
    def get_feedback_insights():
        """Get aggregated feedback insights and analytics."""
        try:
            from .feedback_storage import feedback_storage
            
            # Get query parameters
            days_back = request.args.get('days_back', default=30, type=int)
            
            # Validate days_back parameter
            if days_back < 1 or days_back > 365:
                return jsonify({'error': 'days_back must be between 1 and 365'}), 400
            
            # Get insights
            insights = feedback_storage.aggregate_feedback_insights(days_back=days_back)
            
            response_data = {
                'success': True,
                'insights': insights,
                'timestamp': datetime.now().isoformat(),
                'api_version': '2.0'
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"Feedback insights error: {str(e)}")
            return jsonify({'error': f'Failed to retrieve feedback insights: {str(e)}'}), 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'document_processor': document_processor is not None,
                'style_analyzer': style_analyzer is not None,
                'ai_rewriter': ai_rewriter is not None,
                'feedback_storage': True  # Feedback storage is always available
            }
        })
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        try:
            return render_template('error.html', error_message="Page not found"), 404
        except:
            return "<h1>404 - Page Not Found</h1>", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        try:
            return render_template('error.html', error_message="Internal server error"), 500
        except:
            return "<h1>500 - Internal Server Error</h1>", 500
    
    @app.errorhandler(RequestEntityTooLarge)
    def too_large_error(error):
        """Handle file too large errors."""
        return jsonify({'error': 'File too large'}), 413 