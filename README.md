# 🎯 Content Editorial Assistant (CEA)

**AI-Powered Technical Writing Assistant with Local Ollama Integration**

Transform your technical documentation with comprehensive style analysis, readability scoring, and AI-powered iterative rewriting. Designed for technical writers targeting 9th-11th grade readability standards.

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Cross-Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-green.svg)](https://github.com/yourusername/peer-review-platform)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](License)
---

## 🚀 Super Simple Setup (Just 3 Steps!)

### 📋 Prerequisites
- **Python 3.12+** ([Download here](https://www.python.org/downloads/))
  
  ⚠️ **CRITICAL:** This project requires Python 3.12 or higher. Older versions WILL NOT WORK.
  
  **Quick Check:**
  ```bash
  python3.12 --version  # Should show: Python 3.12.x
  ```

### 🔧 Step 1: Create Virtual Environment

**Windows:**
```batch
# Navigate to project folder
cd C:\path\to\style-guide-ai

# Create and activate virtual environment (ensure Python 3.12 is installed)
python -m venv venv
venv\Scripts\activate
```

**Linux (Fedora/RHEL-based):**
```bash
# Update system and install Python 3.12
sudo dnf clean all
sudo dnf update
sudo dnf install python3.12

# Navigate to project folder
cd ~/path/to/style-guide-ai

# Create and activate virtual environment
python3.12 -m venv venv
source venv/bin/activate
```

**macOS:**
```bash
# Navigate to project folder
cd ~/path/to/style-guide-ai

# Create and activate virtual environment (ensure Python 3.12 is installed)
python3.12 -m venv venv
source venv/bin/activate
```

**✅ You should see `(venv)` at the start of your command prompt**

### 📦 Step 2: Install Requirements
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all Python packages (conflict-free!)
pip install -r requirements.txt
```

### 🎯 Step 3: Start the Application
```bash
python main.py
```

**Then visit:** [http://localhost:5000](http://localhost:5000) 🌐

**✨ That's it!** The application will auto-setup everything on first run:
- ✅ SpaCy language models
- ✅ NLTK data downloads  
- ✅ Directory creation
- ✅ Dependency verification
- ✅ Ollama detection & guidance

---

## 🔄 Daily Usage

**Always activate your virtual environment first:**

**Windows:**
```batch
cd C:\path\to\style-guide-ai
venv\Scripts\activate
python main.py
```

**Linux/macOS:**
```bash
cd ~/path/to/style-guide-ai
source venv/bin/activate
python main.py
```

---

## ✨ Key Features

### 🧠 **Iterative AI Rewriting**
- **Two-Pass Process:** AI reviews and refines its own output
- **Local Ollama Integration:** Privacy-first with Llama models
- **Real-Time Progress:** Watch the AI improvement process step-by-step
- **Smart Confidence Scoring:** Know how much the AI improved your text

### 📊 **Comprehensive Analysis**
- **Grade Level Assessment:** Targets 9th-11th grade readability
- **Multiple Readability Scores:** Flesch, Gunning Fog, SMOG, Coleman-Liau, ARI
- **Style Issues Detection:** Passive voice, sentence length, wordiness
- **Technical Writing Metrics:** Custom scoring for documentation

### 📁 **Multi-Format Support**
- **Text Files:** .txt, .md (Markdown)
- **Documents:** .docx (Microsoft Word)
- **Technical Formats:** .adoc (AsciiDoc), .dita (DITA)
- **PDFs:** Extract and analyze existing documents
- **Direct Input:** Paste text directly into the interface

### 🎨 **Modern Interface**
- **Real-Time Analysis:** Instant feedback on text quality
- **Interactive Error Highlighting:** Click to see specific issues
- **Progress Transparency:** No fake spinners - see actual AI work
- **Responsive Design:** Works on desktop, tablet, and mobile

---

## 🤖 AI Features (Optional)

For the best AI rewriting experience, install **Ollama** with our recommended model:

### Windows
1. Download from: https://ollama.com/download/windows
2. Run installer
3. Open Command Prompt: `ollama pull llama3:8b`

### macOS
1. Download from: https://ollama.com/download/mac
2. Install .dmg file
3. Open Terminal: `ollama pull llama3:8b`

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3:8b
```

**Recommended Model:**
- `llama3:8b` - **Superior writing quality and reasoning (4.7GB)** ⭐ **Recommended**

**Alternative Models (if needed):**
- `llama3.2:3b` - Good balance of speed and quality (2GB)

**Why llama3:8b?**
- ✅ Superior writing quality and reasoning capabilities
- ✅ Excellent for complex technical writing improvements
- ✅ Better understanding of context and nuance
- ✅ Optimal performance with our two-pass iterative process

### 🔧 Using a Different Model (Optional)

If you prefer to use a different model than our recommended `llama3:8b`, you can easily customize it:

**Step 1: Update Configuration**
Edit `config.py` and change line 45:
```python
# Change this line:
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:8b')

# To your preferred model, for example:
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
```

**Step 2: Pull Your Chosen Model**
```bash
# For llama3.2:3b (faster, smaller)
ollama pull llama3.2:3b

# Or any other compatible model
ollama pull your-chosen-model
```

**Step 3: Restart the Application**
```bash
python main.py
```

**Popular Alternative Models:**
- `llama3.2:3b` - Good balance of speed and quality (2GB)
- `llama3.2:1b` - Very fast, basic quality (1.3GB)
- `llama3:70b` - Highest quality, requires powerful hardware (40GB)
- `codellama:7b` - Optimized for technical/code documentation (3.8GB)

---

## 📝 AsciiDoc Support (Optional)

For **AsciiDoc** document parsing and analysis, install the **asciidoctor** Ruby gem:

### Prerequisites: Ruby Installation

**Windows:**
1. Download from: https://rubyinstaller.org/
2. Run the installer (includes Ruby + DevKit)
3. Open Command Prompt and verify: `ruby --version`

**macOS:**
```bash
# Ruby is usually pre-installed. If not:
brew install ruby

# Verify installation
ruby --version
```

**Linux:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install ruby-full

# Fedora/RHEL
sudo dnf install ruby ruby-devel

# Verify installation
ruby --version
```

### Install Asciidoctor Gem

```bash
# Install asciidoctor
gem install asciidoctor

# Or with sudo if needed
sudo gem install asciidoctor

# Verify installation
asciidoctor --version
```

### Benefits of Asciidoctor

- ✅ **High-Performance Parsing:** Uses persistent Ruby server (15x faster than subprocess)
- ✅ **Full AsciiDoc Support:** Complete parsing of admonitions, tables, includes, etc.
- ✅ **Accurate Structure Analysis:** Proper block-level content analysis
- ✅ **Document Title Detection:** Correctly identifies and displays document titles

**Without Asciidoctor:**
- ⚠️ AsciiDoc parsing will be limited to basic text extraction
- ⚠️ Document structure analysis may be incomplete
- ⚠️ Style analysis won't recognize AsciiDoc-specific elements

---

## 🔧 Troubleshooting

### 🚨 Having Setup Issues?

**For comprehensive troubleshooting, see:** [`SETUP_TROUBLESHOOTING.md`](SETUP_TROUBLESHOOTING.md)

This detailed guide covers:
- ✅ Python version conflicts and installation
- ✅ Virtual environment problems  
- ✅ Package installation failures
- ✅ SpaCy and NLTK setup issues
- ✅ Ollama/Llama installation and configuration
- ✅ OS-specific solutions (Windows/macOS/Linux)
- ✅ Complete setup verification script

### Quick Fixes

**Python Version Issues:**
```bash
# CRITICAL: You must use Python 3.12+
python3.12 --version  # Should show 3.12.x

# Create venv with EXACT Python version
python3.12 -m venv venv
```

**Virtual Environment Issues:**
```bash
# Always activate venv first (you should see (venv) in prompt)
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate      # Windows

# Verify Python version in venv
python --version           # Should show Python 3.12.x
```

**Package Installation Issues:**
```bash
# Nuclear option: fresh reinstall
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

**Quick Setup Verification:**
```bash
# Verify everything is working
python -c "import flask, spacy, nltk; print('✅ Core packages OK')"
python -c "import spacy; spacy.load('en_core_web_sm'); print('✅ SpaCy model OK')"
```

---

## 📊 Example Analysis

**Input Text:**
> "In order to facilitate the implementation of the new system, it was decided by the team that the best approach would be to utilize a modular architecture."

**AI Analysis Detects:**
- ❌ Passive voice: "it was decided"
- ❌ Wordy phrases: "in order to", "utilize"
- ❌ Long sentence: 25 words (target: 15-20)
- ❌ Grade level: 14th (target: 9th-11th)

**AI Rewrite (Pass 1):**
> "To implement the new system, the team decided to use a modular architecture."

**AI Rewrite (Pass 2 - Final):**
> "The team chose a modular architecture to implement the new system."

**Improvements:**
- ✅ Reduced from 25 to 10 words
- ✅ Converted to active voice
- ✅ Removed wordy phrases
- ✅ Lowered to 9th grade level
- ✅ Improved clarity and flow

---

## 🏗️ Architecture

```
style-guide-ai/
├── main.py               # Main Flask application (auto-setup included!)
├── requirements.txt      # Clean, conflict-free dependencies
├── config.py             # Main application configuration
├── style_analyzer/       # Analysis modules
├── rewriter/             # AI rewriting components
├── rules/                # Style rules and checks
├── models/               # AI model management
├── ui/                   # User interface files
│   ├── templates/        # HTML templates  
│   └── static/          # CSS, JS, images
├── uploads/             # File upload storage
└── logs/               # Application logs
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE)

---

## 🙏 Acknowledgments

- **SpaCy** for advanced NLP processing
- **Ollama** for local AI model serving
- **Flask** for the web framework
- **Bootstrap** for responsive UI components

---

**Made with ❤️ for technical writers who value privacy and quality.** 

