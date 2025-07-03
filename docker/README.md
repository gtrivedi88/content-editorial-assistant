# 🐳 Docker Deployment

**Location:** `/docker/` directory  
**Purpose:** Complete AI-powered app deployment

---

# 🚀 Docker Quick Guide

## For Developers

### Build and Push to Quay.io
```bash
# 1. Build and push (takes 15-20 minutes)
cd docker && ./build-and-push.sh

# 2. That's it! Your image is live at:
# quay.io/rhdeveldocs/peer-lens:latest
```

### When You Update Your App
```bash
# 1. Push to GitHub
git add .
git commit -m "Updated rules"
git push origin main

# 2. Rebuild Docker image
cd docker && ./build-and-push.sh
```

### 🚀 Docker Layer Caching Optimization

The Dockerfile is optimized for maximum caching efficiency:

**✅ What Gets Cached (Never Re-downloads):**
- Ollama installation (~200MB)
- Llama 8B model (~4.7GB) 
- Python dependencies (unless requirements.txt changes)
- NLP models (spaCy, NLTK data)

**⚠️ Only Re-downloads When:**
- Ollama version updates
- You change `requirements.txt`
- You explicitly force rebuild with `--no-cache`

**🎯 Build Performance:**
- **First build**: 10-15 minutes (downloads everything)
- **Subsequent builds**: 1-2 minutes (uses cached layers)
- **Registry push**: Only changed layers get pushed to Quay.io

**💡 How It Works:**
1. **Local caching**: Docker reuses unchanged layers from previous builds
2. **Registry caching**: Quay.io stores layers - only new/changed layers get pushed
3. **Layer ordering**: App code is copied LAST, so model cache isn't invalidated

### Force Complete Rebuild (if needed)

```bash
# Clear all caches and rebuild everything
docker build --no-cache -f Dockerfile -t quay.io/rhdeveldocs/peer-lens:latest ..
docker push quay.io/rhdeveldocs/peer-lens:latest
```

### Development Workflow

```bash
# 1. Make code changes
# 2. Build (fast - uses cached models)
cd docker && ./build-and-push.sh

# 3. Push automatically includes layer caching
# Only your code changes get uploaded to Quay.io!
```

### Technical Details

**Image Size:** ~8GB (includes everything)
**Python Version:** 3.12
**AI Model:** Llama 8B (pre-downloaded)
**Caching Strategy:** Multi-layer optimization
**Security:** Non-root user, minimal attack surface

### Troubleshooting

**If build seems slow:**
- Check if you changed `requirements.txt` (forces dependency rebuild)
- Verify Docker has enough disk space for caching
- Use `docker system df` to check cache usage

**If model isn't working:**
- Container needs 8GB RAM minimum
- Llama 8B loads automatically on first request
- Check logs: `docker logs <container-id>`

### Local Development

```bash
# For development with hot reloading
docker-compose up
```

## For Users
**One-command deployment with full AI capabilities!**

## What You Get

**Complete AI-powered writing assistant**  
**Ollama with Llama 8B model pre-installed**  
**Advanced NLP analysis and rewriting**  
**Document processing (PDF, DOCX, TXT)**  
**Privacy-first local processing**  
**No setup required - everything included**  

## Requirements

- **Docker Desktop** installed ([Download here](https://www.docker.com/products/docker-desktop/))
- **8GB+ RAM** recommended
- **10GB+ disk space** for the AI models
- **Internet connection** for initial download

## Quick Start (One Command!)

```bash
# Run the complete AI-powered app
docker run -p 5000:5000 -p 11434:11434 quay.io/rhdeveldocs/peer-lens:latest
```

**That's it!** Wait 2-3 minutes for startup, then open: **http://localhost:5000**

## Features Available

### **AI-Powered Rewriting**
- Intelligent text improvement with Llama 8B
- Two-pass iterative refinement
- Context-aware suggestions
- Confidence scoring

### **Style Analysis**
- Sentence length optimization
- Passive voice detection
- Readability scoring (9th-11th grade target)
- Technical writing metrics

### **Document Processing**
- PDF text extraction
- Microsoft Word (.docx) support
- Markdown and plain text
- Batch processing capabilities

### **Privacy-First**
- **100% local processing**
- No data sent to external servers
- Your documents never leave your machine
- Open-source transparency

## Usage Tips

### First-Time Setup
1. **Download Docker Desktop** if not installed
2. **Run the docker command** above
3. **Wait for startup** (downloads happen automatically)
4. **Open http://localhost:5000** in your browser

### For Regular Use
```bash
# Run with persistence (recommended)
docker run -d \
  --name peer-lens-ai \
  -p 5000:5000 \
  -p 11434:11434 \
  -v peer-lens-uploads:/app/uploads \
  -v peer-lens-ollama:/root/.ollama \
  --restart unless-stopped \
  quay.io/rhdeveldocs/peer-lens:latest

# Access your app at: http://localhost:5000
```

### Managing the Container
```bash
# Stop the app
docker stop peer-lens-ai

# Start it again
docker start peer-lens-ai

# Remove completely
docker rm peer-lens-ai
```

## Troubleshooting

### **App Won't Start**
- Check Docker is running: `docker info`
- Increase Docker memory to 8GB+ in Settings
- Ensure ports 5000 and 11434 are available

### **Slow Performance**
- Allocate more RAM to Docker (8GB+ recommended)
- Close other memory-intensive applications
- Use SSD storage for better performance

### **Port Conflicts**
```bash
# Use different ports if 5000 is taken
docker run -p 8080:5000 -p 11435:11434 quay.io/rhdeveldocs/peer-lens:latest
# Then access at: http://localhost:8080
```

## Image Details

### **Full Image (Optimized for Regular Users)**
```bash
docker run -p 5000:5000 quay.io/rhdeveldocs/peer-lens:latest
```
- **Size:** ~8GB (includes pre-downloaded Llama 8B model)
- **Python:** 3.12 (latest stable)
- **Startup:** Fast (2-3 minutes)
- **Best for:** Everyone - complete experience out of the box

## What's Running

When you start the app, you get:
- **Main App:** http://localhost:5000
- **Ollama API:** http://localhost:11434
- **Health Check:** http://localhost:5000/health

## Success!

You now have a complete AI writing assistant running locally with:
- **Professional-grade text analysis**
- **AI-powered rewriting capabilities**
- **Privacy-first local processing**
- **No subscription fees or API keys**
- **Full document processing suite**

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Ensure Docker has sufficient resources
3. Allocate more RAM to Docker (8GB+ recommended)
4. Check container logs: `docker logs peer-lens-ai`

**Enjoy your AI-powered writing assistant!** 