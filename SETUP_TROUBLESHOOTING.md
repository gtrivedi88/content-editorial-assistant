# 🔧 Complete Setup & Troubleshooting Guide

## ⚡ Quick Start Checklist

**Before you begin, complete this checklist:**

### Step 1: Python Version Check
```bash
# Check your Python version
python --version
python3 --version
python3.12 --version

# You MUST have Python 3.12+ for this project
```

### Step 2: System Preparation
```bash
# Linux (Fedora/RHEL/CentOS)
sudo dnf clean all
sudo dnf update
sudo dnf install python3.12 python3.12-pip python3.12-venv

# Linux (Ubuntu/Debian) 
sudo apt update
sudo apt install python3.12 python3.12-pip python3.12-venv

# macOS (with Homebrew)
brew install python@3.12

# Windows: Download from https://www.python.org/downloads/
```

---

## 🐍 Python Version Troubleshooting

### Problem 1: "Python 3.12 not found"

**Symptoms:**
- `python3.12 --version` returns "command not found"
- Installation fails with version errors

**Solution by OS:**

#### Linux (Fedora/RHEL/CentOS):
```bash
# Enable Python 3.12 repository
sudo dnf install dnf-plugins-core
sudo dnf config-manager --set-enabled crb  # For RHEL 9
sudo dnf install python3.12 python3.12-pip python3.12-venv python3.12-devel

# Verify installation
python3.12 --version
which python3.12
```

#### Linux (Ubuntu/Debian):
```bash
# Add deadsnakes PPA for newer Python versions
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-pip python3.12-venv python3.12-dev

# Verify installation
python3.12 --version
which python3.12
```

#### macOS:
```bash
# Method 1: Homebrew (Recommended)
brew install python@3.12
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Method 2: Direct download
# Download from https://www.python.org/downloads/
# Install the .pkg file

# Verify installation
python3.12 --version
which python3.12
```

#### Windows:
```powershell
# Method 1: Official installer
# Download from https://www.python.org/downloads/release/python-3120/
# Run installer and check "Add Python to PATH"

# Method 2: Windows Store
# Install "Python 3.12" from Microsoft Store

# Verify installation
python --version
python3.12 --version
where python
```

### Problem 2: "Multiple Python versions conflict"

**Symptoms:**
- Wrong Python version used in virtual environment
- Import errors after creating venv
- Package installation failures

**Solution:**
```bash
# Always use the FULL path to Python 3.12
# Find your Python 3.12 installation
which python3.12          # Linux/macOS
where python3.12           # Windows (in PowerShell)

# Create venv with explicit Python version
/usr/bin/python3.12 -m venv venv              # Linux example
/opt/homebrew/bin/python3.12 -m venv venv     # macOS Homebrew example
C:\Python312\python.exe -m venv venv          # Windows example

# Activate and verify
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate      # Windows

# Verify Python version in venv
python --version           # Should show Python 3.12.x
```

### Problem 3: "Virtual environment issues"

**Symptoms:**
- `(venv)` not showing in prompt
- Import errors despite package installation
- Packages installed globally instead of in venv

**Solution:**
```bash
# 1. Remove corrupted venv
rm -rf venv                # Linux/macOS
rmdir /s venv             # Windows

# 2. Create fresh venv with correct Python
python3.12 -m venv venv

# 3. Activate properly
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate     # Windows

# 4. Verify activation (you should see (venv) in prompt)
echo $VIRTUAL_ENV         # Linux/macOS (should show path)
echo %VIRTUAL_ENV%        # Windows (should show path)

# 5. Upgrade pip in venv
python -m pip install --upgrade pip

# 6. Install requirements
pip install -r requirements.txt
```

---

## 📦 Dependency Installation Issues

### Problem 1: "Package installation failures"

**Common Error Messages:**
- "error: Microsoft Visual C++ 14.0 is required"
- "Failed building wheel for [package]"
- "Could not find a version that satisfies the requirement"

**Solutions:**

#### Windows:
```powershell
# Install Microsoft C++ Build Tools
# Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or install Visual Studio Community with C++ development tools
```

#### Linux:
```bash
# Install build dependencies
# Fedora/RHEL/CentOS:
sudo dnf groupinstall "Development Tools"
sudo dnf install python3.12-devel gcc gcc-c++ make

# Ubuntu/Debian:
sudo apt install build-essential python3.12-dev gcc g++ make
```

#### macOS:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Or install Xcode from App Store
```

### Problem 2: "SpaCy model download failures"

**Solution:**
```bash
# Manual SpaCy model installation
python -m spacy download en_core_web_sm --user
python -m spacy download en_core_web_md --user

# If that fails, try direct download
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl

# Verify installation
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('SpaCy model loaded successfully')"
```

### Problem 3: "NLTK data download issues"

**Solution:**
```bash
# Manual NLTK data download
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords') 
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
print('NLTK data downloaded successfully')
"

# If download fails, set different download directory
python -c "
import nltk
import os
nltk.data.path.append(os.path.expanduser('~/nltk_data'))
# Then repeat downloads above
"
```

---

## 🤖 AI Features Setup (Ollama & Llama)

### When to Install Ollama/Llama

**Install Ollama/Llama if you want:**
- ✅ AI-powered text rewriting and improvement
- ✅ Iterative content enhancement (AI reviews its own output)
- ✅ Advanced style suggestions beyond basic grammar checking
- ✅ Privacy-first AI processing (runs locally)

**Skip Ollama/Llama if you only need:**
- ❌ Basic style analysis and readability scoring
- ❌ Grammar and punctuation checking
- ❌ Document structure analysis
- ❌ Upload and basic text processing

### Step-by-Step Ollama Installation

#### 1. Install Ollama

**Linux:**
```bash
# Method 1: Official installer (Recommended)
curl -fsSL https://ollama.com/install.sh | sh

# Method 2: Manual download
# Download from: https://github.com/ollama/ollama/releases
# Extract and add to PATH

# Verify installation
ollama --version
```

**macOS:**
```bash
# Method 1: Download installer
# Download from: https://ollama.com/download/mac
# Install the .dmg file

# Method 2: Homebrew
brew install ollama

# Verify installation
ollama --version
```

**Windows:**
```powershell
# Download installer from: https://ollama.com/download/windows
# Run the .exe installer
# Restart your terminal

# Verify installation
ollama --version
```

#### 2. Start Ollama Service

```bash
# Start Ollama service (runs in background)
ollama serve

# Or on some systems, it starts automatically after installation
# Check if it's running:
curl http://localhost:11434/api/tags
```

#### 3. Install Recommended Model

```bash
# Install our recommended model (4.7GB download)
ollama pull llama3:8b

# Verify model installation
ollama list

# Test the model
ollama run llama3:8b "Hello, world!"
```

#### 4. Alternative Models (if needed)

```bash
# Smaller/faster models:
ollama pull llama3.2:3b     # 2GB - Good balance
ollama pull llama3.2:1b     # 1.3GB - Fastest

# Larger/better models (requires more RAM/VRAM):
ollama pull llama3:70b      # 40GB - Highest quality
ollama pull codellama:7b    # 3.8GB - Code-focused
```

### Ollama Troubleshooting

#### Problem 1: "Ollama service not starting"

```bash
# Check if port is in use
lsof -i :11434              # Linux/macOS
netstat -an | findstr 11434 # Windows

# Kill conflicting process if needed
sudo kill -9 $(lsof -t -i:11434)  # Linux/macOS

# Start Ollama with verbose logging
ollama serve --verbose

# Check system resources (Ollama needs RAM)
free -h                     # Linux
vm_stat                     # macOS
systeminfo                  # Windows
```

#### Problem 2: "Model download fails"

```bash
# Check internet connection
ping ollama.com

# Try downloading with resume capability
ollama pull llama3:8b --resume

# Check available disk space (models are large)
df -h                       # Linux/macOS
dir C:\ /s                 # Windows

# Clear Ollama cache if needed
ollama rm [model-name]
```

#### Problem 3: "Out of memory errors"

```bash
# Check available RAM
free -h                     # Linux
vm_stat                     # macOS
wmic computersystem get TotalPhysicalMemory  # Windows

# Use smaller model if RAM is limited
ollama pull llama3.2:1b     # Requires ~2GB RAM
ollama pull llama3.2:3b     # Requires ~4GB RAM
ollama pull llama3:8b       # Requires ~8GB RAM
```

---

## 🔍 Complete Setup Verification Script

Create this verification script to check everything:

```bash
#!/bin/bash
# save as verify_setup.sh

echo "🔍 Style Guide AI Setup Verification"
echo "====================================="

# Check Python version
echo -n "Python 3.12+ check: "
python_version=$(python --version 2>&1 | grep -o '3\.1[2-9]\|3\.[2-9][0-9]')
if [ ! -z "$python_version" ]; then
    echo "✅ $(python --version)"
else
    echo "❌ Python 3.12+ not found"
    exit 1
fi

# Check virtual environment
echo -n "Virtual environment: "
if [ ! -z "$VIRTUAL_ENV" ]; then
    echo "✅ Active ($(basename $VIRTUAL_ENV))"
else
    echo "❌ Not activated"
fi

# Check key packages
echo "Package verification:"
packages=("flask" "spacy" "nltk" "textstat" "ollama")
for package in "${packages[@]}"; do
    echo -n "  $package: "
    if python -c "import $package" 2>/dev/null; then
        echo "✅"
    else
        echo "❌"
    fi
done

# Check SpaCy model
echo -n "SpaCy en_core_web_sm: "
if python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null; then
    echo "✅"
else
    echo "❌"
fi

# Check Ollama (optional)
echo -n "Ollama service: "
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅"
else
    echo "⚠️ Not running (optional)"
fi

# Check Ollama model (optional)
echo -n "Llama3:8b model: "
if ollama list 2>/dev/null | grep -q "llama3:8b"; then
    echo "✅"
else
    echo "⚠️ Not installed (optional)"
fi

echo ""
echo "🚀 Run 'python main.py' to start the application!"
```

**Run verification:**
```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

---

## 📋 Complete Setup Sequence

Follow this exact sequence for guaranteed success:

### Phase 1: System Preparation
```bash
# 1. Update system and install Python 3.12
# (Use appropriate commands for your OS from above)

# 2. Verify Python installation
python3.12 --version  # Must show 3.12.x

# 3. Navigate to project directory
cd /path/to/style-guide-ai
```

### Phase 2: Environment Setup
```bash
# 4. Create virtual environment with specific Python version
python3.12 -m venv venv

# 5. Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# 6. Verify activation (should see (venv) in prompt)
python --version          # Should show Python 3.12.x
```

### Phase 3: Dependencies Installation
```bash
# 7. Upgrade pip
python -m pip install --upgrade pip

# 8. Install all requirements
pip install -r requirements.txt

# 9. Verify key packages
python -c "import flask, spacy, nltk, textstat; print('Core packages OK')"
```

### Phase 4: Model Setup
```bash
# 10. Download SpaCy models
python -m spacy download en_core_web_sm

# 11. Download NLTK data
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
"
```

### Phase 5: AI Setup (Optional)
```bash
# 12. Install Ollama (if you want AI features)
# Follow Ollama installation steps above

# 13. Pull recommended model
ollama pull llama3:8b

# 14. Verify Ollama
curl http://localhost:11434/api/tags
```

### Phase 6: Application Start
```bash
# 15. Start the application
python main.py

# 16. Open browser to http://localhost:5000
```

---

## 🚨 Emergency Troubleshooting

If nothing works, try this nuclear reset:

```bash
# 1. Remove everything
rm -rf venv .setup_complete __pycache__
find . -name "*.pyc" -delete

# 2. Clear Python caches
python3.12 -Bc "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.py[co]')]"

# 3. Start completely fresh
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# 4. Run setup verification script
./verify_setup.sh

# 5. Start application
python main.py
```

---

## 📞 Getting Help

If you're still having issues:

1. **Check the application logs:**
   ```bash
   tail -f logs/app.log
   ```

2. **Run with debug mode:**
   ```bash
   export FLASK_DEBUG=1
   python main.py
   ```

3. **Create a bug report with this information:**
   - Your OS and version
   - Python version (`python --version`)
   - Virtual environment status
   - Error messages from logs
   - Output of `pip list`

4. **Common solutions:**
   - Always use Python 3.12+ (the project won't work with older versions)
   - Always activate your virtual environment before installing packages
   - On Windows, make sure you have Visual C++ build tools
   - On Linux, install development packages for your distribution
   - Ensure you have sufficient disk space for models (10GB+ recommended)
   - Ensure sufficient RAM (8GB+ recommended for AI features)

Remember: **The core application works without Ollama/Llama** - AI features are optional enhancements!
