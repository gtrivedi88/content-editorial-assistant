"""
API Routes Module
Contains all Flask route handlers for the web application.
Handles file uploads, text analysis, and health checks.
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

# Template constants
ERROR_TEMPLATE = 'error.html'

# Error message constants
DB_SERVICE_UNAVAILABLE = 'Database service unavailable'
DB_SERVICE_NOT_AVAILABLE = 'Database service not available'


def setup_routes(app, document_processor, style_analyzer, database_service=None):
    """Setup all API routes for the Flask application with database integration."""
    
    @app.before_request
    def ensure_db_session():
        """Ensure database session exists for data persistence."""
        if request.path in ['/health', '/health/detailed']:
            return

        if database_service and 'db_session_id' not in session:
            try:
                db_session_id = database_service.create_user_session(
                    user_agent=request.headers.get('User-Agent'),
                    ip_address=request.remote_addr
                )
                session['db_session_id'] = db_session_id
            except Exception as e:
                logger.warning(f"Failed to create database session: {e}")
    
    @app.route('/')
    def index():
        """Home page - What do you want to do?"""
        try:
            return render_template('home.html')
        except Exception as e:
            logger.error(f"Error rendering home page: {e}")
            try:
                return render_template(ERROR_TEMPLATE, error_message="Failed to load home page"), 500
            except Exception as e2:
                logger.error(f"Error rendering error page: {e2}")
                return f"<h1>Application Error</h1><p>Failed to load home page: {e}</p><p>Template error: {e2}</p>", 500
    
    @app.route('/analyze')
    def analyze_page():
        """Analyze content page - text analysis and style checking."""
        try:
            return render_template('review.html')
        except Exception as e:
            logger.error(f"Error rendering analyze content page: {e}")
            try:
                return render_template(ERROR_TEMPLATE, error_message="Failed to load analyze content page"), 500
            except Exception as e2:
                logger.error(f"Error rendering error page: {e2}")
                return f"<h1>Application Error</h1><p>Failed to load analyze content page: {e}</p><p>Template error: {e2}</p>", 500

    @app.route('/help-support')
    def help_support():
        """Help and Support page - feedback and bug reporting."""
        try:
            return render_template('help_support.html')
        except Exception as e:
            logger.error(f"Error rendering help and support page: {e}")
            try:
                return render_template(ERROR_TEMPLATE, error_message="Failed to load help and support page"), 500
            except Exception as e2:
                logger.error(f"Error rendering error page: {e2}")
                return f"<h1>Application Error</h1><p>Failed to load help and support page: {e}</p><p>Template error: {e2}</p>", 500

    @app.route('/upload', methods=['POST'])
    @app.limiter.limit("10 per minute")
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
                detected_format = document_processor.detect_format_from_filename(filename)

                file.seek(0, os.SEEK_END)
                file_size = file.tell()
                file.seek(0)

                content = document_processor.extract_text_from_upload(file)

                if content:
                    from structural_parsing.extractors.content_validator import content_validator
                    validation = content_validator.validate(content)

                    if not validation.is_valid:
                        logger.warning(f"Content rejected: {validation.message}")
                        return jsonify({
                            'error': validation.message,
                            'validation_failed': True,
                            'detected_type': validation.detected_type,
                            'confidence': validation.confidence
                        }), 400

                    file_ext = filename.split('.')[-1].lower() if '.' in filename else 'unknown'

                    result = {
                        'success': True,
                        'content': content,
                        'filename': filename,
                        'file_size': file_size,
                        'file_extension': file_ext,
                        'detected_format': detected_format,
                        'word_count': len(content.split()),
                        'char_count': len(content),
                        'message': 'File uploaded successfully. Please select content type and click Analyze.'
                    }

                    if validation.detected_type == "mixed_content":
                        result['warning'] = validation.message
                        result['message'] = f'File uploaded with warning: {validation.message}'

                    logger.info(f"Upload successful: {filename} ({file_size} bytes, format: {detected_format})")
                    return jsonify(result)
                else:
                    return jsonify({'error': 'Failed to extract text from file'}), 400
            else:
                return jsonify({'error': 'File type not supported'}), 400

        except RequestEntityTooLarge:
            return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413
        except Exception as e:
            logger.error(f"Upload error: {str(e)}", exc_info=True)
            return jsonify({'error': f'Upload failed: {str(e)}'}), 500
    
    @app.route('/analyze', methods=['POST'])
    @app.limiter.limit("5 per minute")  # Strict limit for heavy analysis endpoint
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
            
            # Validate content is technical writing (for direct text input)
            # Skip if content was already validated during file upload
            skip_validation = data.get('skip_content_validation', False)
            if not skip_validation:
                from structural_parsing.extractors.content_validator import content_validator
                validation = content_validator.validate(content)
                logger.debug(f"Content validation: valid={validation.is_valid}, type={validation.detected_type}")
                
                if not validation.is_valid:
                    return jsonify({
                        'error': validation.message,
                        'validation_failed': True,
                        'detected_type': validation.detected_type,
                        'confidence': validation.confidence
                    }), 400
            
            # Validate content_type
            valid_content_types = ['concept', 'procedure', 'reference', 'assembly']
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
                    logger.debug(f"Created database document: {document_id}, analysis: {analysis_id}")
                except Exception as e:
                    logger.warning(f"Failed to create database document: {e}")
            
            # Start analysis in database
            if database_service and analysis_id:
                try:
                    database_service.start_analysis(analysis_id)
                except Exception as e:
                    logger.warning(f"Failed to update analysis status: {e}")
            
            logger.info(f"Starting analysis: session={session_id}, type={content_type}, format={format_hint}, length={len(content)}")

            emit_progress(session_id, 'analysis_start', 'Initializing analysis...', 'Setting up analysis pipeline', 10)

            if confidence_threshold is not None:
                # Temporarily adjust the confidence threshold for this request
                original_threshold = style_analyzer.structural_analyzer.confidence_threshold
                style_analyzer.structural_analyzer.confidence_threshold = confidence_threshold
                style_analyzer.structural_analyzer.rules_registry.set_confidence_threshold(confidence_threshold)
            
            # Create progress callback that emits WebSocket updates
            def progress_callback(step, status, detail, percent):
                emit_progress(session_id, step, status, detail, percent)
            
            analysis_result = style_analyzer.analyze_with_blocks(
                content, format_hint, content_type=content_type, progress_callback=progress_callback
            )
            
            emit_progress(session_id, 'style_analysis', 'Style analysis complete', 'Processed all grammar and style rules', 90)
            
            analysis = analysis_result.get('analysis', {})
            structural_blocks = analysis_result.get('structural_blocks', [])
            
            # Emit compliance check progress (always emit, regardless of result)
            emit_progress(session_id, 'compliance_check', 'Validating compliance', f'Checking {content_type} module requirements', 70)
            
            # Check if modular compliance was included in results
            if 'modular_compliance' in analysis_result:
                analysis['modular_compliance'] = analysis_result['modular_compliance']
            
            # Enhanced: Restore original threshold if it was modified
            if confidence_threshold is not None:
                style_analyzer.structural_analyzer.confidence_threshold = original_threshold
                style_analyzer.structural_analyzer.rules_registry.set_confidence_threshold(original_threshold)
            
            # Calculate processing time (moved before emit to include accurate time)
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
                'confidence_threshold_used': confidence_threshold or analysis.get('confidence_threshold', 0.65),
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

            # Include code block ranges for editor visual styling
            code_block_ranges = analysis_result.get('code_block_ranges', [])
            if code_block_ranges:
                response_data['code_block_ranges'] = code_block_ranges

            # Enhanced: Add backward compatibility flag
            response_data['backward_compatible'] = True
            
            # Emit progress completion AFTER response is fully prepared (moved from line 308)
            emit_progress(session_id, 'analysis_complete', 'Analysis complete!', f'Analysis completed in {processing_time:.2f}s', 100)

            emit_completion(session_id, 'analysis_complete', response_data)

            return jsonify(response_data)

        except Exception as e:
            logger.error(f"Analysis error for session {session_id}: {str(e)}")
            error_response = {
                'success': False,
                'error': f'Analysis failed: {str(e)}',
                'session_id': session_id
            }
            emit_completion(session_id, 'analysis_error', error_response)
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
            report_type = data.get('report_type', 'full')  # 'full' or 'summary'
            
            if not analysis_data:
                return jsonify({'error': 'No analysis data provided'}), 400
            
            if not content:
                return jsonify({'error': 'No content provided'}), 400
            
            # Import PDF generator from root pdf_reports package
            try:
                from pdf_reports import PDFReportGenerator
                logger.info("Using modular PDF report generator v2.0")
            except ImportError as e:
                logger.error(f"Failed to import PDF generator: {e}")
                return jsonify({'error': 'PDF generation not available - missing dependencies'}), 500
            
            # Generate PDF report
            logger.info(f"Generating {report_type} PDF report...")
            pdf_generator = PDFReportGenerator()
            
            if report_type == 'summary':
                pdf_bytes = pdf_generator.generate_summary_report(
                    analysis_data=analysis_data,
                    content=content
                )
            else:
                pdf_bytes = pdf_generator.generate_report(
                    analysis_data=analysis_data,
                    content=content,
                    structural_blocks=structural_blocks if structural_blocks else None
                )
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_suffix = '_summary' if report_type == 'summary' else ''
            filename = f"writing_analytics_report{report_suffix}_{timestamp}.pdf"
            
            # Return PDF as downloadable file
            pdf_buffer = BytesIO(pdf_bytes)
            pdf_buffer.seek(0)
            
            logger.info(f"PDF report generated successfully ({len(pdf_bytes):,} bytes)")
            
            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/pdf'
            )
            
        except Exception as e:
            logger.error(f"PDF generation error: {str(e)}", exc_info=True)
            return jsonify({'error': f'PDF generation failed: {str(e)}'}), 500
    
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
            
            # Database storage with file-based fallback
            if not database_service:
                # Fallback to file-based storage (for production without database)
                logger.warning("Database service unavailable - using file-based feedback storage")
                
                from app_modules.feedback_storage import FeedbackStorage
                # Use environment variable for storage path, fallback to PVC mount point
                feedback_storage_dir = os.environ.get('FEEDBACK_STORAGE_DIR', '/opt/app-root/src/feedback_data')
                file_storage = FeedbackStorage(storage_dir=feedback_storage_dir)
                
                success, message, feedback_id = file_storage.store_feedback(
                    feedback_data={
                        'session_id': data.get('session_id', 'unknown'),
                        'error_id': violation_id,
                        'error_type': data['error_type'],
                        'error_message': data['error_message'],
                        'error_text': data.get('error_text', ''),
                        'context_before': data.get('context_before'),
                        'context_after': data.get('context_after'),
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
                        'message': 'Feedback stored to file (database unavailable)',
                        'feedback_id': feedback_id,
                        'violation_id': violation_id,
                        'timestamp': datetime.now().isoformat(),
                        'storage_type': 'file_fallback'
                    }
                    logger.info(f"📁 File-based feedback stored: {feedback_id}")
                    return jsonify(response_data), 201
                else:
                    logger.error(f"❌ File-based feedback storage failed: {message}")
                    # Check if this is a validation error (should return 400) vs storage error (500)
                    validation_errors = ['must be', 'Invalid', 'Missing required field']
                    is_validation_error = any(err in message for err in validation_errors)
                    status_code = 400 if is_validation_error else 500
                    return jsonify({'error': message}), status_code
                
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
                        'user_reason': data.get('user_reason'),
                        # Content fields for rule improvement
                        'error_text': data.get('error_text'),
                        'context_before': data.get('context_before'),
                        'context_after': data.get('context_after'),
                        'suggestion': data.get('suggestion'),
                        'rule_id': data.get('rule_id')
                    }
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
                    
                    logger.info(f"PostgreSQL feedback submitted: {feedback_id}")

                    # Live feedback loop: refresh reliability adjustments after each submission
                    try:
                        report = database_service.get_rule_accuracy_report()
                        if report and report.get('rules'):
                            feedback_stats = {}
                            for rule_entry in report['rules']:
                                rid = rule_entry.get('rule_id')
                                if rid:
                                    feedback_stats[rid] = {
                                        'correct': rule_entry.get('correct', 0),
                                        'incorrect': rule_entry.get('incorrect', 0),
                                        'total': rule_entry.get('total_feedback', 0)
                                    }
                            if feedback_stats:
                                logger.debug(f"Feedback stats collected for {len(feedback_stats)} rules")
                    except Exception as fb_err:
                        logger.debug(f"Feedback loop refresh skipped: {fb_err}")

                    return jsonify(response_data), 201
                else:
                    logger.error(f"❌ PostgreSQL feedback storage failed: {feedback_id}")
                    return jsonify({'error': 'Failed to store feedback in PostgreSQL'}), 500
                    
            except Exception as e:
                logger.error(f"❌ PostgreSQL feedback error: {e}")
                return jsonify({'error': f'PostgreSQL storage failed: {str(e)}'}), 500
                
        except Exception as e:
            logger.error(f"Feedback submission error: {str(e)}")
            # Preserve HTTP error codes from werkzeug exceptions
            if hasattr(e, 'code') and isinstance(e.code, int):
                return jsonify({'error': str(e)}), e.code
            return jsonify({'error': f'Feedback submission failed: {str(e)}'}), 500
    
    @app.route('/api/feedback/stats', methods=['GET'])
    def get_feedback_stats():
        """Get feedback statistics from PostgreSQL."""
        try:
            if not database_service:
                return jsonify({'error': DB_SERVICE_UNAVAILABLE}), 503
            
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
                return jsonify({'error': DB_SERVICE_NOT_AVAILABLE}), 503
            
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
                return jsonify({'error': DB_SERVICE_NOT_AVAILABLE}), 503
            
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
    
    @app.route('/api/analytics/rule-accuracy', methods=['GET'])
    def get_rule_accuracy():
        """Get per-rule accuracy report with false positive rates.

        Returns rules sorted by false positive rate (worst first),
        flagging any rule exceeding the 5% false positive threshold.
        """
        try:
            if not database_service:
                return jsonify({'error': DB_SERVICE_NOT_AVAILABLE}), 503

            report = database_service.get_rule_accuracy_report()
            return jsonify(report)

        except Exception as e:
            logger.error(f"Rule accuracy report error: {str(e)}")
            return jsonify({'error': f'Failed to retrieve rule accuracy report: {str(e)}'}), 500

    @app.route('/api/analytics/model-usage', methods=['GET'])
    def get_model_usage_analytics():
        """Get AI model usage statistics."""
        try:
            if not database_service:
                return jsonify({'error': DB_SERVICE_NOT_AVAILABLE}), 503
            
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
    @app.limiter.exempt  # Exempt from rate limiting to prevent pod restarts
    def health_check():
        """Simple health check endpoint for Kubernetes/OpenShift probes."""
        # Simple check - just return OK if the app is running
        return jsonify({'status': 'ok'}), 200
    
    @app.route('/health/detailed')
    @app.limiter.exempt  # Exempt from rate limiting
    def health_check_detailed():
        """Detailed health check endpoint with database status."""
        try:
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'services': {
                    'document_processor': document_processor is not None,
                    'style_analyzer': style_analyzer is not None,
                    'feedback_storage': True,
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
    
    @app.route('/health/nltk-diagnostic')
    @app.limiter.exempt  # Exempt from rate limiting
    def nltk_diagnostic():
        """Diagnostic endpoint to test NLTK and textstat configuration."""
        import nltk
        import textstat
        
        results = {
            'nltk_data_paths': nltk.data.path[:3],  # Show first 3 paths
            'nltk_data_env': os.getenv('NLTK_DATA', 'NOT_SET'),
            'tests': {}
        }
        
        # Test 1: Check if NLTK data resources exist
        test_resources = ['punkt', 'stopwords', 'cmudict']
        for resource in test_resources:
            try:
                if resource == 'punkt':
                    nltk.data.find('tokenizers/punkt')
                else:
                    nltk.data.find(f'corpora/{resource}')
                results['tests'][f'nltk_{resource}'] = '✅ Found'
            except LookupError as e:
                results['tests'][f'nltk_{resource}'] = f'❌ Missing: {str(e)[:100]}'
        
        # Test 2: Test textstat on sample text
        sample_text = "This is a simple test sentence. It should produce valid readability scores."
        try:
            flesch = textstat.flesch_reading_ease(sample_text)
            results['tests']['textstat_flesch'] = f'✅ {flesch:.1f}'
        except Exception as e:
            results['tests']['textstat_flesch'] = f'❌ Error: {str(e)[:200]}'
        
        try:
            smog = textstat.smog_index(sample_text)
            results['tests']['textstat_smog'] = f'✅ {smog:.1f}'
        except Exception as e:
            results['tests']['textstat_smog'] = f'❌ Error: {str(e)[:200]}'
        
        try:
            grade = textstat.flesch_kincaid_grade(sample_text)
            results['tests']['textstat_grade'] = f'✅ {grade:.1f}'
        except Exception as e:
            results['tests']['textstat_grade'] = f'❌ Error: {str(e)[:200]}'
        
        # Overall status
        all_passed = all('✅' in str(v) for v in results['tests'].values())
        results['status'] = 'PASS' if all_passed else 'FAIL'
        
        return jsonify(results), 200 if all_passed else 500
    
    @app.route('/api/feedback/existing', methods=['GET'])
    def get_existing_feedback():
        """Get existing feedback for a specific session and violation."""
        try:
            if not database_service:
                return jsonify({'error': DB_SERVICE_UNAVAILABLE}), 503
                
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
                return jsonify({'error': DB_SERVICE_UNAVAILABLE}), 503
                
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
                violation = feedback.violation if hasattr(feedback, 'violation') else None
                
                feedback_data.append({
                    'feedback_id': feedback.feedback_id,
                    'violation_id': feedback.violation_id,
                    'error_type': feedback.error_type,
                    'error_message': feedback.error_message,
                    'error_text': violation.error_text if violation else '',
                    'context_before': violation.context_before if violation else None,
                    'context_after': violation.context_after if violation else None,
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
                return jsonify({'error': DB_SERVICE_UNAVAILABLE}), 503
                
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
            return render_template(ERROR_TEMPLATE, error_message="Page not found"), 404
        except Exception:
            return "<h1>404 - Page Not Found</h1>", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        try:
            return render_template(ERROR_TEMPLATE, error_message="Internal server error"), 500
        except Exception:
            return "<h1>500 - Internal Server Error</h1>", 500
    
    @app.errorhandler(RequestEntityTooLarge)
    def too_large_error(error):
        """Handle file too large errors."""
        return jsonify({'error': 'File too large'}), 413 