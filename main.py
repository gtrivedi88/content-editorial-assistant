"""
Style Guide Application - Main Entry Point (Simplified Setup)
A clean, modular Flask application for content analysis and AI-powered rewriting.
Auto-initializes all dependencies on first run - no separate setup required!
"""

import os
import sys
import subprocess
import platform
import logging
import json
from pathlib import Path
import requests
import time
from app_modules.app_factory import create_app, configure_upload_folder
from config import Config

# Setup logging for initialization
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def ensure_setup_complete():
    """Auto-initialize application on first run or when dependencies are missing."""
    
    # Check if setup marker exists
    setup_marker = Path('.setup_complete')
    
    if setup_marker.exists() and check_critical_dependencies():
        return True  # Setup already complete and dependencies available
    
    logger.info("🔧 First-time setup or missing dependencies detected...")
    logger.info("🚀 Auto-initializing application...")
    
    if not run_auto_setup():
        logger.error("❌ Auto-setup failed. Some features may not work.")
        return False
    
    # Create setup marker
    setup_marker.touch()
    logger.info("✅ Setup completed successfully!")
    return True

def check_critical_dependencies():
    """Quick check for critical dependencies."""
    try:
        import spacy
        import nltk
        import textstat
        
        # Check if SpaCy model is available
        try:
            nlp = spacy.load("en_core_web_sm")
            return True
        except OSError:
            return False  # SpaCy model missing
            
    except ImportError:
        return False  # Critical packages missing

def run_command(command, description="Running command", timeout=300):
    """Run a command and handle errors gracefully."""
    try:
        logger.info(f"  {description}...")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout)
        return True
    except subprocess.TimeoutExpired:
        logger.warning(f"  ⚠️ Command timed out: {description}")
        return False
    except subprocess.CalledProcessError as e:
        logger.warning(f"  ⚠️ Command failed: {description}")
        return False

def setup_spacy():
    """Download SpaCy language models."""
    logger.info("📥 Setting up SpaCy language models...")
    
    # Try small model first (faster)
    models = ["en_core_web_sm", "en_core_web_md"]
    
    for model in models:
        if run_command(f"{sys.executable} -m spacy download {model}", f"Downloading {model}", timeout=300):
            return True
    
    logger.warning("⚠️ Could not install SpaCy models. Basic text processing will still work.")
    return True  # Don't fail the entire setup

def setup_nltk():
    """Download required NLTK data."""
    logger.info("📥 Setting up NLTK data...")
    
    try:
        import nltk
        
        # Download required datasets quietly
        datasets = ['punkt', 'stopwords', 'averaged_perceptron_tagger', 'wordnet', 'omw-1.4']
        
        for dataset in datasets:
            try:
                nltk.download(dataset, quiet=True)
            except Exception:
                pass  # Continue if individual dataset fails
        
        return True
                
    except ImportError:
        logger.warning("⚠️ NLTK not available. Some text analysis features may be limited.")
        return True  # Don't fail setup

def create_directories():
    """Create necessary application directories."""
    logger.info("📁 Creating application directories...")
    
    directories = ["uploads", "logs", "instance", "temp"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    return True

def check_ollama():
    """Check Ollama installation and provide guidance."""
    logger.info("🤖 Checking Ollama installation...")
    
    try:
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("  ✅ Ollama is installed")
            
            # Check if service is running and models are available
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    if models:
                        model_names = [m['name'] for m in models]
                        logger.info(f"  ✅ Available models: {', '.join(model_names[:3])}...")
                    else:
                        logger.info("  💡 To enable AI rewriting, install a model:")
                        logger.info("     ollama pull llama3:8b")
                else:
                    logger.info("  💡 Start Ollama service: ollama serve")
            except requests.exceptions.RequestException:
                logger.info("  💡 Start Ollama service: ollama serve")
                
        else:
            logger.info("  ⚠️ Ollama not found. AI rewriting features will be limited.")
            logger.info("  💡 Install from: https://ollama.com")
            
    except Exception:
        logger.info("  ⚠️ Could not check Ollama installation.")
    
    return True  # Always succeed - Ollama is optional

def run_auto_setup():
    """Run automatic setup process."""
    
    setup_steps = [
        ("Setting up SpaCy models", setup_spacy),
        ("Setting up NLTK data", setup_nltk), 
        ("Creating directories", create_directories),
        ("Checking Ollama", check_ollama)
    ]
    
    failed_count = 0
    
    for step_name, step_function in setup_steps:
        try:
            if not step_function():
                failed_count += 1
        except Exception as e:
            logger.warning(f"  ⚠️ {step_name} failed: {e}")
            failed_count += 1
    
    # Success if most steps passed
    return failed_count < len(setup_steps) // 2

# Auto-setup check
ensure_setup_complete()

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