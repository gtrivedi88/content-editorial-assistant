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

### AI-Powered Text Rewriting
- Intelligent text improvement using Llama 8B
- Two-pass iterative refinement process
- Context-aware suggestions
- Confidence scoring for improvements

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

### Common Issues

**Container exits immediately:**
- Check available system memory
- Verify Docker has sufficient resources allocated

**AI responses are slow:**
- Ensure at least 8GB RAM is allocated to Docker
- Close unnecessary applications to free up system resources

**Upload failures:**
- Check file permissions in upload directory
- Verify supported file formats (PDF, DOCX, TXT, MD)

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
1. Upload a document at http://localhost:5000
2. Try the AI rewriting features
3. Explore the style analysis capabilities
4. Process multiple documents for batch improvements

For development and customization instructions, see [DEVELOPER.md](DEVELOPER.md). 