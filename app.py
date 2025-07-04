"""
Style Guide Application - Main Entry Point (Modular Version)
A clean, modular Flask application for content analysis and AI-powered rewriting.
Uses the application factory pattern for better organization and maintainability.
"""

import os
from app_modules.app_factory import create_app, configure_upload_folder
from src.config import Config

# Create application using factory pattern
app, socketio = create_app(Config)

# Configure upload settings
configure_upload_folder(app)

if __name__ == '__main__':
    """Run the application in development mode."""
    try:
        # Development configuration
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        port = int(os.getenv('PORT', 5000))
        host = os.getenv('HOST', '127.0.0.1')
        
        print("🚀 Starting Style Guide AI Application...")
        print(f"📱 Access the application at: http://{host}:{port}")
        print("📊 Real-time progress tracking enabled via WebSocket")
        print("🤖 AI rewriting with Ollama integration ready")
        print("=" * 60)
        
        # Run with SocketIO support
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug_mode,
            allow_unsafe_werkzeug=True  # For development only
        )
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        exit(1) 