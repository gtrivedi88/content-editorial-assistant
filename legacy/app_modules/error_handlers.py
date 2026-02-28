"""
Error Handlers Module
Contains error handlers for HTTP errors and application exceptions.
Provides user-friendly error pages and JSON error responses.
"""

import logging
from flask import render_template, jsonify, request

logger = logging.getLogger(__name__)


def setup_error_handlers(app):
    """Setup error handlers for the Flask application."""
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        try:
            if request.is_json:
                return jsonify({
                    'error': 'Resource not found',
                    'status_code': 404,
                    'message': 'The requested resource was not found on this server.'
                }), 404
            else:
                try:
                    return render_template('error.html', 
                                         error_code=404,
                                         error_message="Page not found"), 404
                except Exception as template_error:
                    logger.error(f"Template error in 404 handler: {template_error}")
                    return "<h1>404 Not Found</h1><p>The requested page was not found.</p>", 404
        except Exception as e:
            logger.error(f"Error in 404 handler: {e}")
            return "Page not found", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error."""
        try:
            logger.error(f"Internal server error: {error}")
            
            if request.is_json:
                return jsonify({
                    'error': 'Internal server error',
                    'status_code': 500,
                    'message': 'An internal error occurred. Please try again later.'
                }), 500
            else:
                try:
                    return render_template('error.html',
                                         error_code=500,
                                         error_message="Internal server error. Please try again later."), 500
                except Exception as template_error:
                    logger.error(f"Template error in 500 handler: {template_error}")
                    return "<h1>500 Internal Server Error</h1><p>An internal error occurred. Please try again later.</p>", 500
        except Exception as e:
            logger.error(f"Error in 500 handler: {e}")
            return "Internal server error", 500
    
    @app.errorhandler(413)
    def file_too_large(error):
        """Handle 413 Request Entity Too Large."""
        try:
            if request.is_json:
                return jsonify({
                    'error': 'File too large',
                    'status_code': 413,
                    'message': 'The uploaded file is too large. Please try a smaller file.'
                }), 413
            else:
                return render_template('error.html',
                                     error_code=413,
                                     error_message="File too large. Please try a smaller file."), 413
        except Exception as e:
            logger.error(f"Error in 413 handler: {e}")
            return "File too large", 413
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        try:
            if request.is_json:
                return jsonify({
                    'error': 'Bad request',
                    'status_code': 400,
                    'message': 'The request was invalid or cannot be served.'
                }), 400
            else:
                return render_template('error.html',
                                     error_code=400,
                                     error_message="Bad request. Please check your input."), 400
        except Exception as e:
            logger.error(f"Error in 400 handler: {e}")
            return "Bad request", 400
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests."""
        try:
            if request.is_json:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'status_code': 429,
                    'message': 'Too many requests. Please slow down and try again later.'
                }), 429
            else:
                return render_template('error.html',
                                     error_code=429,
                                     error_message="Too many requests. Please try again later."), 429
        except Exception as e:
            logger.error(f"Error in 429 handler: {e}")
            return "Rate limit exceeded", 429
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Handle unexpected exceptions."""
        try:
            logger.error(f"Unexpected error: {error}", exc_info=True)
            
            if request.is_json:
                return jsonify({
                    'error': 'Unexpected error',
                    'status_code': 500,
                    'message': 'An unexpected error occurred. Please try again later.'
                }), 500
            else:
                try:
                    return render_template('error.html',
                                         error_code=500,
                                         error_message="An unexpected error occurred. Please try again later."), 500
                except Exception as template_error:
                    logger.error(f"Template error in exception handler: {template_error}")
                    return "<h1>Unexpected Error</h1><p>An unexpected error occurred. Please try again later.</p>", 500
        except Exception as e:
            logger.error(f"Error in exception handler: {e}")
            return "An unexpected error occurred", 500 