"""
API Routes Module
Contains all Flask route handlers for the web application.
Handles file uploads, text analysis, AI rewriting, and health checks.
"""

import os
import time
import logging
from datetime import datetime
from flask import render_template, request, jsonify, flash, redirect, url_for, send_file, session
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from io import BytesIO

from config import Config
from .websocket_handlers import emit_progress, emit_completion

logger = logging.getLogger(__name__)


def setup_routes(app, document_processor, style_analyzer, ai_rewriter, database_service=None):
    """Setup all API routes for the Flask application with database integration."""
    
    # Add request logging and session management middleware
    @app.before_request
    def log_request_info():
        """Log all incoming requests and ensure database session exists."""
        print(f"\n📥 INCOMING REQUEST: {request.method} {request.path}")
        if request.method == 'POST':
            print(f"   📋 Content-Type: {request.content_type}")
            print(f"   📋 Content-Length: {request.content_length}")
            if request.is_json:
                print(f"   📋 JSON Data Keys: {list(request.json.keys()) if request.json else 'None'}")
        
        # Ensure database session exists for data persistence
        if database_service and 'db_session_id' not in session:
            try:
                db_session_id = database_service.create_user_session(
                    user_agent=request.headers.get('User-Agent'),
                    ip_address=request.remote_addr
                )
                session['db_session_id'] = db_session_id
                print(f"   🔐 Created database session: {db_session_id}")
            except Exception as e:
                logger.warning(f"Failed to create database session: {e}")
        
        print("")
    
    @app.route('/')
    def index():
        """Home page - What do you want to do?"""
        try:
            return render_template('home.html')
        except Exception as e:
            logger.error(f"Error rendering home page: {e}")
            try:
                return render_template('error.html', error_message="Failed to load home page"), 500
            except Exception as e2:
                logger.error(f"Error rendering error page: {e2}")
                return f"<h1>Application Error</h1><p>Failed to load home page: {e}</p><p>Template error: {e2}</p>", 500
    
    @app.route('/analyze')
    def analyze_page():
        """Analyze content page - text analysis and style checking."""
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error rendering analyze content page: {e}")
            try:
                return render_template('error.html', error_message="Failed to load analyze content page"), 500
            except Exception as e2:
                logger.error(f"Error rendering error page: {e2}")
                return f"<h1>Application Error</h1><p>Failed to load analyze content page: {e}</p><p>Template error: {e2}</p>", 500
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Handle file upload and text extraction with database storage."""
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file selected'}), 400
            
            file = request.files['file']
            if file.filename == '' or file.filename is None:
                return jsonify({'error': 'No file selected'}), 400
            
            if file and document_processor.allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Extract text without saving to disk (more secure)
                content = document_processor.extract_text_from_upload(file)
                
                if content:
                    result = {
                        'success': True,
                        'content': content,
                        'filename': filename
                    }
                    
                    # Store in database if available
                    if database_service:
                        try:
                            db_session_id = session.get('db_session_id')
                            if db_session_id:
                                # Detect document format from filename
                                doc_format = filename.split('.')[-1].lower() if '.' in filename else 'txt'
                                
                                document_id, analysis_id = database_service.process_document_upload(
                                    session_id=db_session_id,
                                    content=content,
                                    filename=filename,
                                    document_format=doc_format,
                                    content_type='unknown',  # Will be determined during analysis
                                    file_size=len(content.encode('utf-8'))
                                )
                                
                                result.update({
                                    'document_id': document_id,
                                    'analysis_id': analysis_id,
                                    'db_session_id': db_session_id
                                })
                                
                                logger.info(f"📄 Document stored in database: {document_id}")
                        except Exception as e:
                            logger.warning(f"⚠️ Failed to store document in database: {e}")
                            # Continue without database storage
                    
                    return jsonify(result)
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
            
            # Database integration: Get document and analysis IDs from request or create new ones
            document_id = data.get('document_id') if data else None
            analysis_id = data.get('analysis_id') if data else None
            db_session_id = session.get('db_session_id')
        
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
            
            # Database integration: Create document and analysis if not provided
            if database_service and db_session_id and not (document_id and analysis_id):
                try:
                    document_id, analysis_id = database_service.process_document_upload(
                        session_id=db_session_id,
                        content=content,
                        filename="direct_input.txt",
                        document_format=format_hint,
                        content_type=content_type
                    )
                    logger.info(f"📄 Created database document: {document_id}, analysis: {analysis_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to create database document: {e}")
            
            # Start analysis in database
            if database_service and analysis_id:
                try:
                    database_service.start_analysis(analysis_id, analysis_mode="comprehensive", format_hint=format_hint)
                except Exception as e:
                    logger.warning(f"⚠️ Failed to update analysis status: {e}")
            
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
            
            # Database integration: Store analysis results
            if database_service and analysis_id and document_id:
                try:
                    # Convert errors to database format
                    violations = []
                    errors = analysis.get('errors', [])
                    for error in errors:
                        violations.append({
                            'rule_id': error.get('type', 'unknown'),
                            'error_text': error.get('text', ''),
                            'error_message': error.get('message', ''),
                            'error_position': error.get('start', 0),
                            'end_position': error.get('end'),
                            'line_number': error.get('line'),
                            'column_number': error.get('column'),
                            'severity': error.get('severity', 'medium'),
                            'confidence_score': error.get('confidence', 0.5),
                            'suggestion': error.get('suggestion'),
                            'context_before': error.get('context_before'),
                            'context_after': error.get('context_after'),
                            'metadata': error.get('metadata', {})
                        })
                    
                    # Store results in database
                    database_service.store_analysis_results(
                        analysis_id=analysis_id,
                        document_id=document_id,
                        violations=violations,
                        processing_time=processing_time,
                        total_blocks_analyzed=len(structural_blocks)
                    )
                    
                    logger.info(f"📊 Stored {len(violations)} violations in database")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to store analysis results: {e}")
            
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
            
            # Return enhanced results with modular compliance data and database IDs
            response_data = {
                'success': True,
                'analysis': analysis,
                'processing_time': processing_time,
                'session_id': session_id,
                'content_type': content_type,  # Include content type in response
                'confidence_metadata': confidence_metadata,
                'api_version': '2.0'  # Indicate enhanced API version
            }
            
            # Include database IDs if available
            if database_service and db_session_id:
                response_data.update({
                    'db_session_id': db_session_id,
                    'document_id': document_id,
                    'analysis_id': analysis_id
                })
            
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
        """Submit user feedback on error accuracy with database storage."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Validate required fields (handle both error_id and violation_id)
            required_fields = ['error_type', 'error_message', 'feedback_type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400
            
            # Handle both error_id (from frontend) and violation_id (database field)
            violation_id = data.get('violation_id') or data.get('error_id')
            if not violation_id:
                return jsonify({'error': 'Missing required field: violation_id or error_id'}), 400
            
            # Extract request metadata
            user_agent = request.headers.get('User-Agent')
            ip_address = request.remote_addr
            db_session_id = session.get('db_session_id')
            
            # PostgreSQL storage
            if not database_service:
                return jsonify({'error': 'Database service unavailable'}), 503
                
            # Ensure we have a database session ID
            if not db_session_id:
                # Create a new database session if missing
                try:
                    db_session_id = database_service.create_user_session(user_agent=user_agent, ip_address=ip_address)
                    session['db_session_id'] = db_session_id
                    logger.info(f"✅ Created new database session: {db_session_id}")
                except Exception as e:
                    logger.error(f"❌ Failed to create database session: {e}")
                    return jsonify({'error': 'Failed to create database session'}), 500
            
            try:
                success, feedback_id = database_service.store_user_feedback(
                    session_id=db_session_id,
                    violation_id=violation_id,
                    feedback_data={
                        'error_type': data['error_type'],
                        'error_message': data['error_message'],
                        'feedback_type': data['feedback_type'],
                        'confidence_score': data.get('confidence_score', 0.5),
                        'user_reason': data.get('user_reason')
                    },
                    user_agent=user_agent,
                    ip_address=ip_address
                )
                
                if success:
                    response_data = {
                        'success': True,
                        'message': 'Feedback stored successfully in PostgreSQL',
                        'feedback_id': feedback_id,
                        'violation_id': violation_id,  # Include violation_id for frontend tracking
                        'timestamp': datetime.now().isoformat(),
                        'storage_type': 'postgresql'
                    }
                    
                    logger.info(f"🐘 PostgreSQL feedback submitted: {feedback_id}")
                    return jsonify(response_data), 201
                else:
                    logger.error(f"❌ PostgreSQL feedback storage failed: {feedback_id}")
                    return jsonify({'error': 'Failed to store feedback in PostgreSQL'}), 500
                    
            except Exception as e:
                logger.error(f"❌ PostgreSQL feedback error: {e}")
                return jsonify({'error': f'PostgreSQL storage failed: {str(e)}'}), 500
                
        except Exception as e:
            logger.error(f"Feedback submission error: {str(e)}")
            return jsonify({'error': f'Feedback submission failed: {str(e)}'}), 500
    
    @app.route('/api/feedback/stats', methods=['GET'])
    def get_feedback_stats():
        """Get feedback statistics from PostgreSQL."""
        try:
            if not database_service:
                return jsonify({'error': 'Database service unavailable'}), 503
            
            # Get query parameters
            session_id = request.args.get('session_id')
            days_back = request.args.get('days_back', default=7, type=int)
            
            # Validate days_back parameter
            if days_back < 1 or days_back > 365:
                return jsonify({'error': 'days_back must be between 1 and 365'}), 400
            
            # Get statistics from PostgreSQL
            stats = database_service.get_feedback_statistics(session_id=session_id, days_back=days_back)
            
            response_data = {
                'success': True,
                'statistics': stats,
                'timestamp': datetime.now().isoformat(),
                'source': 'postgresql'
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            logger.error(f"PostgreSQL feedback stats error: {str(e)}")
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
    
    # Database-powered analytics endpoints
    @app.route('/api/analytics/session', methods=['GET'])
    def get_session_analytics():
        """Get analytics for current user session."""
        try:
            if not database_service:
                return jsonify({'error': 'Database service not available'}), 503
            
            db_session_id = session.get('db_session_id')
            if not db_session_id:
                return jsonify({'error': 'No database session found'}), 400
            
            analytics = database_service.get_session_analytics(db_session_id)
            return jsonify(analytics)
            
        except Exception as e:
            logger.error(f"Session analytics error: {str(e)}")
            return jsonify({'error': f'Failed to retrieve analytics: {str(e)}'}), 500
    
    @app.route('/api/analytics/rules', methods=['GET'])
    def get_rule_analytics():
        """Get rule performance analytics."""
        try:
            if not database_service:
                return jsonify({'error': 'Database service not available'}), 503
            
            rule_id = request.args.get('rule_id')
            days_back = request.args.get('days_back', default=30, type=int)
            
            if rule_id:
                performance = database_service.get_rule_performance(rule_id, days_back)
            else:
                performance = database_service.get_rule_performance(days_back=days_back)
            
            return jsonify(performance)
            
        except Exception as e:
            logger.error(f"Rule analytics error: {str(e)}")
            return jsonify({'error': f'Failed to retrieve rule analytics: {str(e)}'}), 500
    
    @app.route('/api/analytics/model-usage', methods=['GET'])
    def get_model_usage_analytics():
        """Get AI model usage statistics."""
        try:
            if not database_service:
                return jsonify({'error': 'Database service not available'}), 503
            
            db_session_id = session.get('db_session_id')
            operation_type = request.args.get('operation_type')
            days_back = request.args.get('days_back', default=30, type=int)
            
            stats = database_service.get_model_usage_stats(
                session_id=db_session_id,
                operation_type=operation_type,
                days_back=days_back
            )
            
            return jsonify(stats)
            
        except Exception as e:
            logger.error(f"Model usage analytics error: {str(e)}")
            return jsonify({'error': f'Failed to retrieve model usage: {str(e)}'}), 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint with database status."""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'document_processor': document_processor is not None,
                    'style_analyzer': style_analyzer is not None,
                    'ai_rewriter': ai_rewriter is not None,
                    'feedback_storage': True,  # File-based fallback always available
                    'database': database_service is not None
                }
            }
            
            # Add database health check
            if database_service:
                try:
                    db_health = database_service.get_system_health()
                    health_status['database_health'] = db_health
                except Exception as e:
                    health_status['database_health'] = {'status': 'unhealthy', 'error': str(e)}
                    health_status['status'] = 'degraded'
            
            return jsonify(health_status)
            
        except Exception as e:
            logger.error(f"Health check error: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    @app.route('/api/feedback/existing', methods=['GET'])
    def get_existing_feedback():
        """Get existing feedback for a specific session and violation."""
        try:
            if not database_service:
                return jsonify({'error': 'Database service unavailable'}), 503
                
            session_id = request.args.get('session_id')
            violation_id = request.args.get('violation_id')
            
            if not session_id or not violation_id:
                return jsonify({'error': 'Missing required parameters: session_id and violation_id'}), 400
            
            success, feedback_data = database_service.get_existing_feedback(session_id, violation_id)
            
            if success:
                if feedback_data:
                    return jsonify({
                        'success': True,
                        'feedback': feedback_data
                    }), 200
                else:
                    return jsonify({
                        'success': True,
                        'feedback': None,
                        'message': 'No existing feedback found'
                    }), 200
            else:
                return jsonify({'error': 'Failed to retrieve existing feedback'}), 500
                
        except Exception as e:
            logger.error(f"Get existing feedback error: {str(e)}")
            return jsonify({'error': f'Failed to get existing feedback: {str(e)}'}), 500
    
    @app.route('/api/feedback/session', methods=['GET'])
    def get_session_feedback():
        """Get all feedback for the current session."""
        try:
            if not database_service:
                return jsonify({'error': 'Database service unavailable'}), 503
                
            db_session_id = session.get('db_session_id')
            if not db_session_id:
                return jsonify({
                    'success': True,
                    'feedback': [],
                    'message': 'No active session'
                }), 200
            
            feedback_list = database_service.feedback_dao.get_session_feedback(db_session_id)
            
            # Convert feedback to dict format
            feedback_data = []
            for feedback in feedback_list:
                feedback_data.append({
                    'feedback_id': feedback.feedback_id,
                    'violation_id': feedback.violation_id,
                    'error_type': feedback.error_type,
                    'error_message': feedback.error_message,
                    'feedback_type': feedback.feedback_type.value,
                    'confidence_score': feedback.confidence_score,
                    'user_reason': feedback.user_reason,
                    'timestamp': feedback.timestamp.isoformat()
                })
            
            return jsonify({
                'success': True,
                'feedback': feedback_data,
                'session_id': db_session_id
            }), 200
                
        except Exception as e:
            logger.error(f"Get session feedback error: {str(e)}")
            return jsonify({'error': f'Failed to get session feedback: {str(e)}'}), 500
    
    @app.route('/api/feedback', methods=['DELETE'])
    def delete_feedback():
        """Delete user feedback for a specific violation."""
        try:
            if not database_service:
                return jsonify({'error': 'Database service unavailable'}), 503
                
            data = request.get_json()
            if not data:
                return jsonify({'error': 'No JSON data provided'}), 400
            
            # Handle both violation_id (from database) and error_id (frontend generated)
            violation_id = data.get('violation_id')
            error_id = data.get('error_id')
            feedback_id = data.get('feedback_id')  # Direct feedback ID if available
            
            db_session_id = session.get('db_session_id')
            if not db_session_id:
                return jsonify({'error': 'No active session'}), 400
            
            logger.info(f"[DELETE] Session: {db_session_id}, violation_id: {violation_id}, error_id: {error_id}, feedback_id: {feedback_id}")
            
            success = False
            message = "No feedback found to delete"
            
            # Try different approaches to find and delete the feedback
            if feedback_id:
                # Direct deletion by feedback_id
                logger.info(f"[DELETE] Attempting deletion by feedback_id: {feedback_id}")
                try:
                    feedback = database_service.feedback_dao.get_session_feedback(db_session_id)
                    target_feedback = None
                    for fb in feedback:
                        if fb.feedback_id == feedback_id:
                            target_feedback = fb
                            break
                    
                    if target_feedback:
                        success = database_service.feedback_dao.delete_feedback(db_session_id, target_feedback.violation_id)
                        message = "Feedback deleted successfully" if success else "Failed to delete feedback"
                except Exception as e:
                    logger.error(f"[DELETE] Error deleting by feedback_id: {e}")
            
            elif violation_id:
                # Deletion by violation_id
                logger.info(f"[DELETE] Attempting deletion by violation_id: {violation_id}")
                success, message = database_service.delete_user_feedback(db_session_id, violation_id)
            
            elif error_id:
                # Find by error_id (frontend generated ID) - need to match against all feedback for session
                logger.info(f"[DELETE] Attempting to find feedback by error_id: {error_id}")
                try:
                    all_feedback = database_service.feedback_dao.get_session_feedback(db_session_id)
                    for feedback in all_feedback:
                        # Try to reconstruct the error object and generate the same error_id
                        reconstructed_error = {
                            'type': feedback.error_type,
                            'message': feedback.error_message
                        }
                        
                        # This is a simplified check - in practice, you'd want to implement 
                        # the same generateErrorId logic or store the original error_id
                        if feedback.violation_id == error_id:  # Simple fallback
                            success = database_service.feedback_dao.delete_feedback(db_session_id, feedback.violation_id)
                            message = "Feedback deleted successfully" if success else "Failed to delete feedback"
                            break
                except Exception as e:
                    logger.error(f"[DELETE] Error finding feedback by error_id: {e}")
            
            if success:
                logger.info(f"[DELETE] Successfully deleted feedback for session: {db_session_id}")
                return jsonify({
                    'success': True,
                    'message': message
                }), 200
            else:
                logger.warning(f"[DELETE] No feedback found to delete: {message}")
                return jsonify({'error': message}), 404
                
        except Exception as e:
            logger.error(f"Delete feedback error: {str(e)}")
            return jsonify({'error': f'Failed to delete feedback: {str(e)}'}), 500

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