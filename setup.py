#!/usr/bin/env python3
"""
Complete Setup Script for Peer lens
Handles ALL dependencies and setup in virtual environment.
Run this ONCE after creating your venv and installing requirements.txt
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

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description="Running command", timeout=300):
    """Run a command and handle errors gracefully."""
    try:
        logger.info(f"{description}: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True, timeout=timeout)
        if result.stdout:
            logger.info(result.stdout.strip())
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds: {command}")
        return False
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to {description.lower()}: {e}")
        if e.stderr:
            logger.error(f"Error output: {e.stderr.strip()}")
        return False

def check_virtual_environment():
    """Check if we're running in a virtual environment."""
    in_venv = (
        hasattr(sys, 'real_prefix') or 
        (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) or
        os.environ.get('VIRTUAL_ENV') is not None
    )
    
    if not in_venv:
        logger.error("❌ NOT RUNNING IN VIRTUAL ENVIRONMENT!")
        logger.error("Please create and activate a virtual environment first:")
        logger.error("  python -m venv venv")
        if platform.system() == "Windows":
            logger.error("  venv\\Scripts\\activate")
        else:
            logger.error("  source venv/bin/activate")
        logger.error("Then run this setup script again.")
        return False
    
    logger.info(f"✅ Running in virtual environment: {sys.prefix}")
    return True

def upgrade_pip():
    """Upgrade pip to latest version."""
    logger.info("Upgrading pip to latest version...")
    return run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip")

def install_requirements():
    """Install all packages from requirements.txt."""
    logger.info("Installing packages from requirements.txt...")
    
    requirements_file = Path(__file__).parent / "requirements.txt"
    if not requirements_file.exists():
        logger.error("❌ requirements.txt not found!")
        return False
    
    # Install with specific flags for better compatibility
    cmd = f"{sys.executable} -m pip install -r {requirements_file} --upgrade --no-cache-dir"
    return run_command(cmd, "Installing Python packages", timeout=600)

def setup_spacy():
    """Download and setup SpaCy language models."""
    logger.info("Setting up SpaCy language models...")
    
    # Try to install the small model first (faster download)
    models_to_try = [
        ("en_core_web_sm", "Small English model (50MB)"),
        ("en_core_web_md", "Medium English model (50MB)")
    ]
    
    for model, description in models_to_try:
        logger.info(f"Downloading SpaCy model: {model} - {description}")
        
        # Method 1: Using spacy download command
        if run_command(f"{sys.executable} -m spacy download {model}", f"Downloading {model}", timeout=300):
            logger.info(f"✅ Successfully installed {model}")
            return True
            
        # Method 2: Using pip install (fallback)
        logger.info(f"Trying alternative download method for {model}...")
        pip_cmd = f"{sys.executable} -m pip install https://github.com/explosion/spacy-models/releases/download/{model}-3.7.1/{model}-3.7.1-py3-none-any.whl"
        if run_command(pip_cmd, f"Installing {model} via pip", timeout=300):
            logger.info(f"✅ Successfully installed {model} via pip")
            return True
    
    logger.warning("⚠️ Could not install any SpaCy models. The app will use fallback text processing.")
    return True  # Don't fail the entire setup

def setup_nltk():
    """Download required NLTK data."""
    logger.info("Setting up NLTK data...")
    
    try:
        import nltk
        
        # Create NLTK data directory if it doesn't exist
        nltk_data_dir = Path.home() / "nltk_data"
        nltk_data_dir.mkdir(exist_ok=True)
        
        # Download required NLTK data
        nltk_datasets = [
            ('punkt', 'Punkt tokenizer'),
            ('stopwords', 'Stop words corpus'),
            ('averaged_perceptron_tagger', 'POS tagger'),
            ('wordnet', 'WordNet lexical database'),
            ('omw-1.4', 'Open Multilingual Wordnet')
        ]
        
        for dataset, description in nltk_datasets:
            try:
                logger.info(f"Downloading NLTK data: {dataset} - {description}")
                nltk.download(dataset, quiet=True)
                logger.info(f"✅ Downloaded {dataset}")
            except Exception as e:
                logger.warning(f"⚠️ Could not download NLTK data '{dataset}': {e}")
                
        return True
                
    except ImportError:
        logger.error("❌ NLTK not installed. Please check requirements.txt installation.")
        return False

def create_directories():
    """Create necessary application directories."""
    logger.info("Creating application directories...")
    
    directories = [
        "uploads",
        "logs", 
        "data",
        "cache",
        "temp"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(exist_ok=True)
        logger.info(f"✅ Created directory: {directory}")
        
    return True

def check_ollama_installation():
    """Check if Ollama is installed and provide setup instructions."""
    logger.info("Checking Ollama installation...")
    
    try:
        # Check if Ollama is installed
        result = subprocess.run("ollama --version", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"✅ Ollama is installed: {result.stdout.strip()}")
            
            # Check if Ollama service is running
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    if models:
                        model_names = [m['name'] for m in models]
                        logger.info(f"✅ Ollama is running with models: {', '.join(model_names)}")
                        
                        # Check for recommended models
                        recommended_models = ['llama3:8b', 'llama3.2:3b']
                        available_recommended = [m for m in model_names if any(rec in m for rec in recommended_models)]
                        
                        if available_recommended:
                            logger.info(f"✅ Found recommended models: {', '.join(available_recommended)}")
                        else:
                            logger.info("💡 Consider installing our recommended model:")
                            logger.info("   ollama pull llama3:8b      # Superior quality, 4.7GB ⭐ RECOMMENDED")
                            logger.info("   ollama pull llama3.2:3b    # Good balance, 2GB")
                    else:
                        logger.info("⚠️ Ollama is running but no models installed.")
                        logger.info("Install our recommended model with: ollama pull llama3:8b")
                else:
                    logger.warning("⚠️ Ollama is installed but not responding. Start it with: ollama serve")
            except requests.exceptions.RequestException:
                logger.warning("⚠️ Ollama is installed but not running. Start it with: ollama serve")
                
        else:
            logger.warning("⚠️ Ollama not found. AI rewriting will be limited.")
            logger.info("📥 To install Ollama for AI features:")
            
            system = platform.system().lower()
            if system == "windows":
                logger.info("   1. Download from: https://ollama.com/download/windows")
                logger.info("   2. Run the installer")
                logger.info("   3. Open Command Prompt and run: ollama pull llama3:8b")
            elif system == "darwin":  # macOS
                logger.info("   1. Download from: https://ollama.com/download/mac")
                logger.info("   2. Install the .dmg file")
                logger.info("   3. Open Terminal and run: ollama pull llama3:8b")
            else:  # Linux
                logger.info("   1. Run: curl -fsSL https://ollama.com/install.sh | sh")
                logger.info("   2. Start service: ollama serve")
                logger.info("   3. Install model: ollama pull llama3:8b")
                
    except Exception as e:
        logger.warning(f"⚠️ Could not check Ollama: {e}")
    
    return True  # Don't fail setup if Ollama is not available

def test_installation():
    """Test if the installation was successful."""
    logger.info("Testing installation...")
    
    try:
        # Test critical imports
        logger.info("Testing package imports...")
        
        import flask
        logger.info("✅ Flask imported")
        
        import spacy
        logger.info("✅ SpaCy imported")
        
        import nltk
        logger.info("✅ NLTK imported")
        
        import textstat
        logger.info("✅ TextStat imported")
        
        import pandas
        logger.info("✅ Pandas imported")
        
        import numpy
        logger.info("✅ NumPy imported")
        
        import requests
        logger.info("✅ Requests imported")
        
        # Test SpaCy model
        try:
            nlp = spacy.load("en_core_web_sm")
            test_doc = nlp("This is a test sentence.")
            logger.info("✅ SpaCy model loaded and working")
        except OSError:
            logger.warning("⚠️ SpaCy model not found, but fallback processing will work")
            
        # Test application modules
        try:
            from src.style_analyzer import StyleAnalyzer
            analyzer = StyleAnalyzer()
            test_result = analyzer.analyze("This is a test sentence for analysis.")
            logger.info("✅ Style analyzer working correctly")
        except Exception as e:
            logger.warning(f"⚠️ Style analyzer test failed: {e}")
            
        try:
            from src.ai_rewriter import AIRewriter
            rewriter = AIRewriter()
            logger.info("✅ AI rewriter initialized")
        except Exception as e:
            logger.warning(f"⚠️ AI rewriter test failed: {e}")
            
        # Test Flask app startup (quick test)
        try:
            from app import app
            with app.test_client() as client:
                response = client.get('/health')
                if response.status_code == 200:
                    logger.info("✅ Flask application health check passed")
                else:
                    logger.warning(f"⚠️ Flask health check returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Flask app test failed: {e}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Critical import error: {e}")
        logger.error("Please check that requirements.txt was installed correctly.")
        return False
    except Exception as e:
        logger.error(f"❌ Installation test failed: {e}")
        return False

def print_success_message():
    """Print success message with next steps."""
    logger.info("\n" + "="*60)
    logger.info("🎉 SETUP COMPLETED SUCCESSFULLY!")
    logger.info("="*60)
    logger.info("\n📋 NEXT STEPS:")
    logger.info("1. Make sure your virtual environment is activated")
    logger.info("   (you should see (venv) in your command prompt)")
    logger.info("\n2. Start the application:")
    logger.info("   python app.py")
    logger.info("\n3. Open your browser and visit:")
    logger.info("   http://localhost:5000")
    logger.info("\n💡 TIPS:")
    logger.info("• Always activate venv before running: ")
    
    if platform.system() == "Windows":
        logger.info("  venv\\Scripts\\activate")
    else:
        logger.info("  source venv/bin/activate")
        
    logger.info("• For AI features, install Ollama (see instructions above)")
    logger.info("• Check logs/ directory if you encounter issues")
    logger.info("\n🚀 Happy writing!")

def main():
    """Main setup function."""
    logger.info("🚀 Starting Peer lens Complete Setup...")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    
    # Critical check: Virtual environment
    if not check_virtual_environment():
        return 1
    
    setup_steps = [
        ("Upgrading pip", upgrade_pip),
        ("Installing Python packages", install_requirements),
        ("Setting up SpaCy models", setup_spacy),
        ("Setting up NLTK data", setup_nltk),
        ("Creating directories", create_directories),
        ("Checking Ollama installation", check_ollama_installation),
        ("Testing installation", test_installation)
    ]
    
    failed_steps = []
    
    for step_name, step_function in setup_steps:
        logger.info(f"\n--- {step_name} ---")
        try:
            if not step_function():
                failed_steps.append(step_name)
                logger.error(f"❌ {step_name} failed")
            else:
                logger.info(f"✅ {step_name} completed")
        except Exception as e:
            logger.error(f"❌ {step_name} failed with exception: {e}")
            failed_steps.append(step_name)
    
    if failed_steps:
        logger.error(f"\n❌ Setup completed with errors in: {', '.join(failed_steps)}")
        logger.error("The application may still work, but some features might be limited.")
        logger.info("\n🔧 Try running the application anyway:")
        logger.info("   python app.py")
        return 1
    else:
        print_success_message()
        return 0

if __name__ == "__main__":
    sys.exit(main())