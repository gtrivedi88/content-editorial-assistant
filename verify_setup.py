#!/usr/bin/env python3
"""
Style Guide AI - Setup Verification Script
Automatically checks if all dependencies and requirements are properly installed.
"""

import sys
import subprocess
import importlib.util
import os
import platform
from pathlib import Path

def print_header():
    """Print a nice header for the verification."""
    print("=" * 60)
    print("🔍 Style Guide AI - Setup Verification")
    print("=" * 60)

def check_python_version():
    """Check if Python version is 3.12+"""
    print("🐍 Python Version Check...")
    
    version_info = sys.version_info
    current_version = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    print(f"   Current Python version: {current_version}")
    
    if version_info.major == 3 and version_info.minor >= 12:
        print("   ✅ Python version is compatible")
        return True
    else:
        print("   ❌ Python 3.12+ required")
        print("   💡 Install Python 3.12+ and create venv with: python3.12 -m venv venv")
        return False

def check_virtual_environment():
    """Check if we're running in a virtual environment"""
    print("\n🏠 Virtual Environment Check...")
    
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    venv_path = os.environ.get('VIRTUAL_ENV')
    
    if in_venv and venv_path:
        print(f"   ✅ Virtual environment active: {os.path.basename(venv_path)}")
        return True
    else:
        print("   ❌ Virtual environment not detected")
        print("   💡 Activate with: source venv/bin/activate (Linux/macOS) or venv\\Scripts\\activate (Windows)")
        return False

def check_package(package_name, display_name=None):
    """Check if a Python package is installed"""
    if display_name is None:
        display_name = package_name
    
    try:
        importlib.import_module(package_name)
        print(f"   ✅ {display_name}")
        return True
    except ImportError:
        print(f"   ❌ {display_name}")
        return False

def check_packages():
    """Check if all required packages are installed"""
    print("\n📦 Package Verification...")
    
    packages = [
        ('flask', 'Flask'),
        ('spacy', 'SpaCy'),
        ('nltk', 'NLTK'),
        ('textstat', 'TextStat'),
        ('sqlalchemy', 'SQLAlchemy'),
        ('requests', 'Requests'),
        ('yaml', 'PyYAML'),
        ('fitz', 'PyMuPDF'),
        ('docx', 'python-docx'),
    ]
    
    all_good = True
    for package_name, display_name in packages:
        if not check_package(package_name, display_name):
            all_good = False
    
    return all_good

def check_spacy_model():
    """Check if SpaCy English model is installed"""
    print("\n🧠 SpaCy Model Check...")
    
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("   ✅ en_core_web_sm model loaded successfully")
        return True
    except (ImportError, OSError):
        print("   ❌ en_core_web_sm model not found")
        print("   💡 Install with: python -m spacy download en_core_web_sm")
        return False

def check_nltk_data():
    """Check if NLTK data is downloaded"""
    print("\n📊 NLTK Data Check...")
    
    try:
        import nltk
        required_data = ['punkt', 'stopwords', 'wordnet', 'averaged_perceptron_tagger']
        all_good = True
        
        for data_name in required_data:
            try:
                nltk.data.find(f'tokenizers/{data_name}' if data_name in ['punkt'] else 
                             f'corpora/{data_name}' if data_name in ['stopwords', 'wordnet'] else 
                             f'taggers/{data_name}')
                print(f"   ✅ {data_name}")
            except LookupError:
                print(f"   ❌ {data_name}")
                all_good = False
        
        if not all_good:
            print("   💡 Download missing data with the setup script in main.py")
        
        return all_good
    except ImportError:
        print("   ❌ NLTK not installed")
        return False

def check_ollama():
    """Check if Ollama is running (optional)"""
    print("\n🤖 Ollama Check (Optional AI Features)...")
    
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        if response.status_code == 200:
            print("   ✅ Ollama service is running")
            
            # Check for our recommended model
            data = response.json()
            models = [model['name'] for model in data.get('models', [])]
            if any('llama3:8b' in model for model in models):
                print("   ✅ llama3:8b model found")
            else:
                print("   ⚠️  llama3:8b model not found")
                print("   💡 Install with: ollama pull llama3:8b")
            
            return True
    except:
        pass
    
    print("   ⚠️  Ollama service not running (AI features will be disabled)")
    print("   💡 Install Ollama from: https://ollama.com/download")
    print("   💡 Then run: ollama serve && ollama pull llama3:8b")
    return False

def check_directories():
    """Check if required directories exist"""
    print("\n📁 Directory Structure Check...")
    
    required_dirs = ['uploads', 'logs', 'instance']
    all_good = True
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"   ✅ {dir_name}/")
        else:
            print(f"   ⚠️  {dir_name}/ (will be created automatically)")
    
    return all_good

def check_permissions():
    """Check file permissions"""
    print("\n🔐 Permissions Check...")
    
    # Check if we can write to the current directory
    try:
        test_file = Path('.setup_test')
        test_file.touch()
        test_file.unlink()
        print("   ✅ Write permissions in project directory")
        return True
    except PermissionError:
        print("   ❌ No write permissions in project directory")
        return False

def run_verification():
    """Run all verification checks"""
    print_header()
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Python Packages", check_packages),
        ("SpaCy Model", check_spacy_model),
        ("NLTK Data", check_nltk_data),
        ("Directories", check_directories),
        ("Permissions", check_permissions),
        ("Ollama (Optional)", check_ollama),
    ]
    
    results = []
    for check_name, check_func in checks:
        results.append(check_func())
    
    # Print summary
    print("\n" + "=" * 60)
    print("📋 Verification Summary:")
    print("=" * 60)
    
    critical_checks = results[:7]  # All except Ollama
    optional_checks = results[7:]   # Just Ollama
    
    critical_passed = sum(critical_checks)
    total_critical = len(critical_checks)
    
    if critical_passed == total_critical:
        print("🎉 All critical checks passed! You're ready to go!")
        print("\n🚀 Start the application with: python main.py")
        if not optional_checks[0]:  # Ollama not available
            print("💡 AI features disabled. Install Ollama for text rewriting capabilities.")
    else:
        print(f"⚠️  {total_critical - critical_passed} critical issues found.")
        print("\n🔧 Please fix the issues above before starting the application.")
        print("📖 See SETUP_TROUBLESHOOTING.md for detailed solutions.")
    
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
