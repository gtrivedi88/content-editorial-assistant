"""
Style Guide Application - Main Entry Point (Modular Version)
A clean, modular Flask application for content analysis and AI-powered rewriting.
Uses the application factory pattern for better organization and maintainability.
"""

import os
from app_modules.app_factory import create_app, configure_upload_folder
from config import Config

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
        
        print("🚀 Starting Content Editorial Assistant Application...")
        print(f"📱 Access the application at: http://{host}:{port}")
        print("📊 Real-time progress tracking enabled via WebSocket")
        print("🤖 AI rewriting with Ollama integration ready")
        print("")
        print("🔍 DEBUG MODE ENABLED:")
        print("   📊 API Route /rewrite-block: Comprehensive debug logging")
        print("   🏭 Assembly Line Rewriter: Debug output enabled")
        print("   🎯 Progress Tracker: WorldClassProgressTracker debug")
        print("   📡 WebSocket Handlers: Progress update tracking")
        print("   🌐 Frontend Console: Real-time progress debug")
        print("")
        print("👀 When you click 'Improve Issue', watch for debug output here!")
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