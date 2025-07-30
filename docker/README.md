# Docker Deployment

Lightweight AI-powered writing assistant deployment using Docker.

## Overview

This Docker deployment provides a lightweight AI-powered writing assistant with:
- **Advanced NLP Analysis**: Style analysis and text processing
- **Document Processing**: Support for PDF, DOCX, TXT, and Markdown
- **External AI Integration**: Connect to your own Ollama instance or API providers
- **Privacy-First**: Core processing happens locally on your machine
- **Fast Deployment**: Lightweight image without embedded AI models

## System Requirements

- **Docker Desktop** installed ([Download here](https://www.docker.com/products/docker-desktop/))
- **4GB+ RAM** recommended for optimal performance
- **2GB+ disk space** for application and dependencies
- **Internet connection** for initial download

## Quick Start

### One-Command Deployment

```bash 
docker run -p 5000:5000 quay.io/rhdeveldocs/style-guide-ai:latest
```

**Access your application at:** http://localhost:5000

**Startup time: ~30 seconds** for the core application.

#### 🚨 **Port Conflict Resolution**

If port 5000 is already in use, you'll see an error like:
```
Error: bind: address already in use
```

**Solution**: Use a different external port:

```bash
# Use port 8080 instead of 5000
docker run -p 8080:5000 quay.io/rhdeveldocs/style-guide-ai:latest

# Access at: http://localhost:8080
```

**Common alternative ports:**
- `8080:5000` → http://localhost:8080
- `3000:5000` → http://localhost:3000  
- `8000:5000` → http://localhost:8000
- `9000:5000` → http://localhost:9000

**Check what's using port 5000:**
```bash
# On Linux/Mac
lsof -i :5000

# On Windows
netstat -ano | findstr :5000
```

### Production Deployment (Recommended)

For regular use with data persistence:

```bash
docker run -d \
  --name style-guide-ai \
  -p 5000:5000 \
  -v style-guide-uploads:/app/uploads \
  -v style-guide-instance:/app/instance \
  --restart unless-stopped \
  quay.io/rhdeveldocs/style-guide-ai:latest
```

**For port conflicts, change the external port:**
```bash
docker run -d \
  --name style-guide-ai \
  -p 8080:5000 \
  -v style-guide-uploads:/app/uploads \
  -v style-guide-instance:/app/instance \
  --restart unless-stopped \
  quay.io/rhdeveldocs/style-guide-ai:latest
```
Then access at: http://localhost:8080

## AI Features Setup

To use AI-powered features, you have several options:

### Option 1: External Ollama (Recommended for Local AI)

Run Ollama in a separate container:

```bash
# Start Ollama service
docker run -d --name ollama -p 11434:11434 ollama/ollama

# Pull your preferred model
docker exec ollama ollama pull llama3:8b
```

Then configure the Style Guide AI app to connect to `http://localhost:11434`.

### Option 2: API Providers

Configure API providers (OpenAI, etc.) in the application settings.

### Option 3: Docker Compose (Complete Setup)

Use the provided docker-compose.yml for a complete setup with both services:

```bash
cd docker
docker-compose up -d
```

**For port conflicts with docker-compose**, edit `docker-compose.yml`:
```yaml
ports:
  - "8080:5000"    # Change from 5000:5000 to 8080:5000
```

### Container Management

```bash
# Stop the application
docker stop style-guide-ai

# Start the application
docker start style-guide-ai

# View logs
docker logs style-guide-ai

# Remove completely
docker rm style-guide-ai
```

## Features

### 🔍 **Core Features (Always Available)**
- **Style Analysis**: Comprehensive grammar, punctuation, and readability analysis
- **Document Processing**: Support for PDF, DOCX, TXT, and Markdown files
- **Real-time Feedback**: Interactive error highlighting and suggestions
- **Structural Analysis**: Context-aware rule application
- **Rule-based Improvements**: Basic text enhancements using predefined rules

### 🤖 **AI-Powered Features (Requires External Setup)**
- **Intelligent Rewriting**: Advanced text improvement using external AI models
- **Two-pass Iterative Process**: AI reviews and refines its own output
- **Context-aware Suggestions**: Understands document structure and purpose
- **Confidence Scoring**: Quantifies improvement quality

> **📋 Note**: The application works immediately for style analysis and basic improvements. AI rewriting features require connecting to external AI services (see setup options above).

### External AI Configuration

The lightweight container **connects to external AI services** for enhanced functionality. Choose your preferred option:

#### **Option A: Local Ollama Setup**
```bash
# Start external Ollama service
docker run -d --name ollama -p 11434:11434 ollama/ollama

# Download your preferred model
docker exec ollama ollama pull llama3:8b

# Verify model installation
docker exec ollama ollama list
```

#### **Option B: API Provider Setup**
Configure API providers (OpenAI, Anthropic, etc.) in the application settings.

#### **No Container Restart Required**
Once external AI is configured:
- ✅ **Automatic Detection**: The application automatically detects available AI services
- ✅ **Hot Configuration**: Changes take effect immediately without restarts
- ✅ **Multiple Providers**: Support for various AI providers simultaneously
- ✅ **Fallback Support**: Graceful degradation when AI services are unavailable

The application will automatically switch from rule-based to AI-powered rewriting when external AI is available.

#### **What Works Without External AI**
- ✅ **Style Analysis**: Full grammar and readability analysis
- ✅ **Document Processing**: All file format support
- ✅ **Rule-based Improvements**: Basic text enhancements
- ✅ **Error Detection**: Comprehensive issue identification

## 🔧 Troubleshooting

### Common Issues and Solutions

#### **Port Already in Use**
```bash
Error: bind: address already in use
```
**Solution**: Use a different external port
```bash
docker run -p 8080:5000 quay.io/rhdeveldocs/style-guide-ai:latest
```

#### **Container Won't Start**
```bash
# Check container logs
docker logs style-guide-ai

# Check if container is running
docker ps -a
```

#### **Can't Access Application**
1. **Check if container is running**: `docker ps`
2. **Verify port mapping**: Look for `0.0.0.0:5000->5000/tcp` in `docker ps` output
3. **Try different browser**: Sometimes localhost caching can cause issues
4. **Check firewall**: Ensure localhost traffic is allowed

#### **AI Features Not Working**
1. **Verify external Ollama is running**: `curl http://localhost:11434/api/tags`
2. **Check application logs**: `docker logs style-guide-ai`
3. **Configure API provider**: In application settings if using external APIs

#### **Performance Issues**
- **Increase memory**: Add `--memory=4g` to docker run command
- **Use SSD storage**: For better I/O performance with volumes
- **Close unnecessary applications**: Free up system resources

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