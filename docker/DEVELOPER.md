# Developer Guide

This guide covers building, deploying, and developing the Docker containerized AI writing assistant.

## Development Workflow

### Build and Push to Registry

```bash
# Build and push to Quay.io (takes 15-20 minutes)
cd docker && ./build-and-push.sh

# Your image will be available at:
# quay.io/rhdeveldocs/peer-lens:latest
```

### Code Update Workflow

```bash
# 1. Commit your changes
git add .
git commit -m "Updated rules"
git push origin main

# 2. Rebuild and push Docker image
cd docker && ./build-and-push.sh
```

## Docker Layer Caching Optimization

The Dockerfile is optimized for maximum caching efficiency to reduce build times and registry storage.

### What Gets Cached (Never Re-downloads)

- Ollama installation (~200MB)
- Llama 8B model (~4.7GB) 
- Python dependencies (unless requirements.txt changes)
- NLP models (spaCy, NLTK data)

### Only Re-downloads When

- Ollama version updates
- You change `requirements.txt`
- You explicitly force rebuild with `--no-cache`

### Build Performance

- **First build**: 10-15 minutes (downloads everything)
- **Subsequent builds**: 1-2 minutes (uses cached layers)
- **Registry push**: Only changed layers get pushed to Quay.io

### How Layer Caching Works

1. **Local caching**: Docker reuses unchanged layers from previous builds
2. **Registry caching**: Quay.io stores layers - only new/changed layers get pushed
3. **Layer ordering**: Application code is copied LAST, so model cache isn't invalidated

## Build Commands

### Standard Build

```bash
# Build using the optimized script
cd docker && ./build-and-push.sh
```

### Force Complete Rebuild

```bash
# Clear all caches and rebuild everything
docker build --no-cache -f Dockerfile -t quay.io/rhdeveldocs/peer-lens:latest ..
docker push quay.io/rhdeveldocs/peer-lens:latest
```

### Local Development Build

```bash
# Build for local development only
docker build -f Dockerfile -t peer-lens-dev ..
```

## Development Environment

### Using Docker Compose

```bash
# Start development environment with hot reloading
docker-compose up

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

### Local Development Setup

```bash
# Run container with volume mounts for development
docker run -it \
  -p 5000:5000 \
  -p 11434:11434 \
  -v $(pwd)/..:/app \
  -v peer-lens-ollama:/root/.ollama \
  --name peer-lens-dev \
  peer-lens-dev
```

## Docker Configuration

### Dockerfile Structure

The Dockerfile follows these optimization principles:

1. **Base image**: Python 3.12 slim
2. **Layer ordering**: Most stable layers first
3. **Dependency caching**: Requirements installed before code copy
4. **Model pre-loading**: Ollama and Llama 8B downloaded during build
5. **Security**: Non-root user, minimal attack surface

### Multi-Stage Build Benefits

- **Smaller final image**: Only runtime dependencies included
- **Better caching**: Build dependencies cached separately
- **Security**: No build tools in final image

## Registry Management

### Quay.io Configuration

```bash
# Login to Quay.io
docker login quay.io

# Build and tag
docker build -t quay.io/rhdeveldocs/peer-lens:latest .

# Push to registry
docker push quay.io/rhdeveldocs/peer-lens:latest
```

### Multi-Architecture Builds

```bash
# Build for multiple architectures
docker buildx create --use
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t quay.io/rhdeveldocs/peer-lens:latest \
  --push .
```

## Troubleshooting Development Issues

### Build Problems

**If build seems slow:**
- Check if you changed `requirements.txt` (forces dependency rebuild)
- Verify Docker has enough disk space for caching
- Use `docker system df` to check cache usage
- Consider using `--no-cache` for problematic builds

**If model isn't working:**
- Container needs 8GB RAM minimum
- Llama 8B loads automatically on first request
- Check logs: `docker logs <container-id>`
- Verify Ollama service is running: `docker exec <container-id> ollama list`

### Development Workflow Issues

**Container exits during development:**
- Check volume mounts are correct
- Verify port mappings
- Review application logs for errors

**Hot reloading not working:**
- Ensure volume mounts include source code
- Check file permissions
- Verify Flask development mode is enabled

## Performance Optimization

### Build Performance

```bash
# Check Docker cache usage
docker system df

# Clean up unused caches
docker system prune -a

# Monitor build progress
docker build --progress=plain -f Dockerfile -t peer-lens .
```

### Runtime Performance

```bash
# Monitor container resource usage
docker stats peer-lens-ai

# Check memory usage within container
docker exec peer-lens-ai free -h

# Monitor disk usage
docker exec peer-lens-ai df -h
```

## Security Considerations

### Container Security

- **Non-root user**: Application runs as non-root user
- **Minimal base image**: Using Python slim image
- **No shell access**: Production containers don't include shell utilities
- **Read-only filesystem**: Where possible, mount volumes read-only

### Network Security

- **Port exposure**: Only necessary ports (5000, 11434) exposed
- **No external dependencies**: All processing happens locally
- **No data transmission**: No external API calls for AI processing

## Testing

### Container Testing

```bash
# Test container startup
docker run --rm quay.io/rhdeveldocs/peer-lens:latest python -c "import app; print('OK')"

# Test AI model loading
docker run --rm quay.io/rhdeveldocs/peer-lens:latest ollama list

# Run health check
curl http://localhost:5000/health
```

### Integration Testing

```bash
# Test full workflow
docker run -d --name test-container \
  -p 5000:5000 -p 11434:11434 \
  quay.io/rhdeveldocs/peer-lens:latest

# Wait for startup
sleep 60

# Test endpoints
curl http://localhost:5000/health
curl -X POST http://localhost:5000/analyze -d '{"text": "Test content"}'

# Cleanup
docker stop test-container
docker rm test-container
```

## Maintenance

### Regular Maintenance Tasks

```bash
# Update base image
docker pull python:3.12-slim

# Rebuild with latest dependencies
docker build --no-cache -t quay.io/rhdeveldocs/peer-lens:latest .

# Clean up old images
docker image prune -a
```

### Monitoring

```bash
# Check container health
docker inspect peer-lens-ai --format='{{.State.Health.Status}}'

# Monitor logs
docker logs -f peer-lens-ai

# Check resource usage
docker stats peer-lens-ai
```

## Technical Specifications

### Image Details

- **Registry**: quay.io/rhdeveldocs/peer-lens:latest
- **Size**: ~8GB (includes pre-downloaded models)
- **Python Version**: 3.12
- **AI Model**: Llama 8B (4.7GB)
- **Architecture**: Multi-platform (amd64, arm64)
- **Security**: Non-root user, minimal attack surface

### Dependencies

- **Ollama**: Local AI model serving
- **Flask**: Web application framework
- **spaCy**: NLP processing
- **NLTK**: Language processing toolkit
- **PyPDF2**: PDF text extraction
- **python-docx**: Word document processing

### Environment Variables

```bash
# Development configuration
FLASK_ENV=development
FLASK_DEBUG=1
OLLAMA_HOST=localhost:11434

# Production configuration
FLASK_ENV=production
FLASK_DEBUG=0
WORKERS=4
```

## Support for Developers

### Common Development Tasks

1. **Adding new rules**: Modify Python modules, rebuild container
2. **Updating AI models**: Change Ollama configuration in Dockerfile
3. **UI changes**: Update static files, no rebuild needed for development
4. **Performance tuning**: Modify Docker resources, update configurations

### Best Practices

1. **Always test locally** before pushing to registry
2. **Use layer caching** for faster builds
3. **Monitor resource usage** during development
4. **Keep security in mind** when adding dependencies
5. **Document changes** in commit messages

For user deployment instructions, see [README.md](README.md). 