# Docker Deployment

Complete AI-powered writing assistant deployment using Docker.

## Overview

This Docker deployment provides a complete AI-powered writing assistant with:
- **Local AI Processing**: Ollama with Llama 8B model pre-installed
- **Advanced NLP Analysis**: Style analysis and text rewriting
- **Document Processing**: Support for PDF, DOCX, TXT, and Markdown
- **Privacy-First**: All processing happens locally on your machine
- **No Setup Required**: Everything included in one container

## System Requirements

- **Docker Desktop** installed ([Download here](https://www.docker.com/products/docker-desktop/))
- **8GB+ RAM** recommended for optimal performance
- **10GB+ disk space** for AI models and application data
- **Internet connection** for initial download

## Quick Start

### One-Command Deployment

```bash 
docker run -p 5000:5000 -p 11435:11434 -e FLASK_RUN_HOST=0.0.0.0 -e HOST=0.0.0.0 quay.io/rhdeveldocs/peer-lens:latest
```

**Access your application at:** http://localhost:5000

**Initial startup takes 2-3 minutes** as the AI models load automatically.

> **Note**: This command uses port 11435 for the Ollama API to avoid conflicts with existing Ollama installations that typically use port 11434.

### Production Deployment (Recommended)

For regular use with data persistence:

```bash
docker run -d \
  --name peer-lens-ai \
  -p 5000:5000 \
  -p 11435:11434 \
  -e FLASK_RUN_HOST=0.0.0.0 \
  -e HOST=0.0.0.0 \
  -v peer-lens-uploads:/app/uploads \
  -v peer-lens-ollama:/root/.ollama \
  --restart unless-stopped \
  quay.io/rhdeveldocs/peer-lens:latest
```

**Enable AI Features (Optional):**
```bash
# Download the AI model for enhanced rewriting (one-time setup)
docker exec -it peer-lens-ai ollama pull llama3:8b

# Verify model installation
docker exec -it peer-lens-ai ollama list
```

> **💡 Tip**: The application works immediately for style analysis and basic improvements. AI rewriting features become available after downloading the model.

### Container Management

```bash
# Stop the application
docker stop peer-lens-ai

# Start the application
docker start peer-lens-ai

# View logs
docker logs peer-lens-ai

# Remove completely
docker rm peer-lens-ai
```

## Features

### 🔍 **Core Features (Always Available)**
- **Style Analysis**: Comprehensive grammar, punctuation, and readability analysis
- **Document Processing**: Support for PDF, DOCX, TXT, and Markdown files
- **Real-time Feedback**: Interactive error highlighting and suggestions
- **Structural Analysis**: Context-aware rule application
- **Rule-based Improvements**: Basic text enhancements using predefined rules

### 🤖 **AI-Powered Features (Requires Model Download)**
- **Intelligent Rewriting**: Advanced text improvement using Llama 8B
- **Two-pass Iterative Process**: AI reviews and refines its own output
- **Context-aware Suggestions**: Understands document structure and purpose
- **Confidence Scoring**: Quantifies improvement quality

> **📋 Note**: The application works immediately for style analysis and basic improvements. AI rewriting features require downloading the Llama model (see instructions below).

### AI Model Setup (Optional but Recommended)

The container includes Ollama but **you need to download the AI model** for full functionality:

#### **Step 1: Download the Model**
```bash
# Find your running container
docker ps

# Download the model (one-time setup)
docker exec -it <container_name> ollama pull llama3:8b
```

#### **Step 2: Verify Model Installation**
```bash
# Check if model is available
docker exec -it <container_name> ollama list
```

You should see `llama3:8b` in the list.

#### **Step 3: Restart Container (if needed)**
```bash
docker restart <container_name>
```

#### **No Additional Configuration Required**
Once the model is downloaded:
- ✅ **Automatic Detection**: The application automatically detects the model
- ✅ **Immediate Availability**: AI features become available instantly
- ✅ **No Settings**: No configuration files or environment variables to change
- ✅ **Persistent**: Model persists across container restarts (with volume mounts)

The application will automatically switch from rule-based to AI-powered rewriting.

#### **What Works Without the Model**
- ✅ **Style Analysis**: Full grammar and readability analysis
- ✅ **Document Processing**: All file format support
- ✅ **Rule-based Improvements**: Basic text enhancements
- ✅ **Error Detection**: Comprehensive issue identification

#### **What Requires the Model**
- 🤖 **AI Rewriting**: Advanced text improvement
- 🤖 **Iterative Refinement**: Two-pass improvement process
- 🤖 **Context-aware Suggestions**: Deep understanding of text meaning

### Alternative: Pre-download Model with Persistent Storage

For regular use, set up persistent storage so the model doesn't need re-downloading:

```bash
docker run -d \
  --name peer-lens-ai \
  -p 5000:5000 \
  -p 11435:11434 \
  -e FLASK_RUN_HOST=0.0.0.0 \
  -e HOST=0.0.0.0 \
  -v peer-lens-uploads:/app/uploads \
  -v peer-lens-ollama:/root/.ollama \
  --restart unless-stopped \
  quay.io/rhdeveldocs/peer-lens:latest

# Then download the model once
docker exec -it peer-lens-ai ollama pull llama3:8b
```

The model will persist across container restarts.

### Style Analysis
- Sentence length optimization
- Passive voice detection
- Readability scoring (9th-11th grade target)
- Technical writing metrics

### Document Processing
- PDF text extraction
- Microsoft Word (.docx) support
- Markdown and plain text processing
- Batch processing capabilities

### Privacy and Security
- **100% local processing** - no data sent to external servers
- Your documents never leave your machine
- Open-source transparency
- No API keys or subscriptions required

## Application Endpoints

- **Main Application**: http://localhost:5000
- **Ollama API**: http://localhost:11435
- **Health Check**: http://localhost:5000/health

## Troubleshooting

### Application Won't Start
- Verify Docker is running: `docker info`
- Increase Docker memory allocation to 8GB+ in Docker Desktop settings
- Ensure ports 5000 and 11435 are available

### Performance Issues
- Allocate more RAM to Docker (8GB+ recommended)
- Close other memory-intensive applications
- Use SSD storage for better performance

### Port Conflicts
If you have Ollama running on your host system (port 11434), the default command will fail. Use this corrected version:

```bash
# Recommended: Uses port 11435 for Ollama API and includes network binding fix
docker run -p 5000:5000 -p 11435:11434 -e FLASK_RUN_HOST=0.0.0.0 -e HOST=0.0.0.0 quay.io/rhdeveldocs/peer-lens:latest
```

For completely different ports:
```bash
# Use alternative ports
docker run -p 8080:5000 -p 11436:11434 -e FLASK_RUN_HOST=0.0.0.0 -e HOST=0.0.0.0 quay.io/rhdeveldocs/peer-lens:latest
# Access at: http://localhost:8080
```

### Connection Issues
If you get "connection reset" errors, ensure the environment variables are set:
- `FLASK_RUN_HOST=0.0.0.0` - Makes Flask bind to all interfaces
- `HOST=0.0.0.0` - Alternative environment variable for network binding

### AI Model Issues

**Problem**: AI rewriting features don't work, logs show "Model llama3:8b not found"

**Solution**: Download the model inside the container:
```bash
# Find your container name
docker ps

# Download the model (takes 5-10 minutes)
docker exec -it <container_name> ollama pull llama3:8b

# Verify installation
docker exec -it <container_name> ollama list
```

**Problem**: Model download fails or times out

**Solutions**:
1. **Increase Docker memory**: Ensure Docker has at least 8GB RAM allocated
2. **Check internet connection**: Model download requires ~5GB download
3. **Retry download**: Sometimes network issues cause failures
4. **Use persistent storage**: Set up volume mounts to avoid re-downloading

**Problem**: "Style analysis works but AI rewriting is greyed out"

**Status**: This is expected behavior when the model isn't downloaded. The application gracefully provides rule-based improvements instead.

### Model Storage Location

The AI model is stored in `/root/.ollama` inside the container. To persist across container restarts:

```bash
# Create a named volume for model storage
docker volume create peer-lens-ollama

# Use the volume when running the container
docker run -d \
  --name peer-lens-ai \
  -p 5000:5000 -p 11435:11434 \
  -e FLASK_RUN_HOST=0.0.0.0 -e HOST=0.0.0.0 \
  -v peer-lens-ollama:/root/.ollama \
  --restart unless-stopped \
  quay.io/rhdeveldocs/peer-lens:latest
```

## Image Information

**Registry**: quay.io/rhdeveldocs/peer-lens:latest  
**Size**: ~8GB (includes pre-downloaded Llama 8B model)  
**Python Version**: 3.12  
**Architecture**: Multi-platform (amd64, arm64)  
**Startup Time**: 2-3 minutes (first run)  

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Ensure Docker has sufficient resources allocated
3. Review container logs for error messages
4. Verify system requirements are met

## Next Steps

Once your application is running:
1. **Upload a document** at http://localhost:5000
2. **Try the style analysis** - works immediately with any document
3. **Optional**: Download the AI model for enhanced rewriting features:
   ```bash
   docker exec -it <container_name> ollama pull llama3:8b
   ```
4. **Explore AI rewriting** - advanced text improvement with iterative refinement
5. **Process multiple documents** for batch improvements

**Quick Start Guide:**
- Style analysis and basic improvements work immediately
- AI rewriting requires the model download (one-time setup)
- All processing happens locally - your documents never leave your machine

For development and customization instructions, see [DEVELOPER.md](DEVELOPER.md). 