# Deployment guide

Note |  **This documentation is for system administrators and DevOps engineers** who are deploying Content Editorial Assistant to production environments. The application is already hosted for general use. This guide is for those who need to deploy their own instance.  
---|---  
  
## Overview

This guide covers deployment options for the Content Editorial Assistant, from local development to production environments.

## Deployment options

Method | Use Case | Complexity  
---|---|---  
**Local development** | Testing and development | Low  
**Docker container** | Consistent deployments, any platform | Medium  
**GitLab CI/CD** | Automated deployments on push | Medium  
**LightRail platform** | Enterprise deployment with LlamaStack | High  
  
## Prerequisites

  * Python 3.12+

  * Git

  * Docker (for container deployment)

  * GitLab account (for CI/CD)

  * LightRail access (for platform deployment)

## Local development deployment

### Quick start
[code] 
    # Clone repository
    git clone <repository-url>
    cd content-editorial-assiatant
    
    # Create virtual environment
    python3.12 -m venv venv
    source venv/bin/activate  # Linux/macOS
    # OR
    venv\Scripts\activate     # Windows
    
    # Install dependencies
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Run application
    python main.py
[/code]

Access at: <http://localhost:5000>

### Configuration

Create a `.env` file in project root:
[code] 
    FLASK_DEBUG=true
    FLASK_ENV=development
    MODEL_PROVIDER=ollama
    MODEL_ID=llama3:8b
    LOG_LEVEL=DEBUG
[/code]

See [Environment Variables Reference](<environment-variables.html>) for complete options.

## Docker Deployment

### Build Docker Image
[code] 
    # Build image
    docker build -t content-editorial-assistant:latest .
    
    # Run container
    docker run -d \
      --name cea \
      -p 5000:5000 \
      -e MODEL_PROVIDER=api \
      -e BASE_URL=https://api.groq.com/openai/v1 \
      -e ACCESS_TOKEN=your-api-key \
      -v $(pwd)/instance:/app/instance \
      content-editorial-assistant:latest
[/code]

### Docker Compose

Create `docker-compose.yml`:
[code] 
    version: '3.8'
    
    services:
      cea:
        build: .
        ports:
          - "5000:5000"
        environment:
          - FLASK_ENV=production
          - MODEL_PROVIDER=api
          - BASE_URL=${BASE_URL}
          - ACCESS_TOKEN=${ACCESS_TOKEN}
          - DATABASE_URL=postgresql://cea:password@db:5432/cea
          - HOST=0.0.0.0
        volumes:
          - ./instance:/app/instance
          - ./logs:/app/logs
        depends_on:
          - db
        restart: unless-stopped
    
      db:
        image: postgres:15
        environment:
          - POSTGRES_DB=cea
          - POSTGRES_USER=cea
          - POSTGRES_PASSWORD=password
        volumes:
          - postgres_data:/var/lib/postgresql/data
        restart: unless-stopped
    
    volumes:
      postgres_data:
[/code]

Run with:
[code] 
    docker-compose up -d
[/code]

### Dockerfile Details

The project Dockerfile includes:

  * **Base Image** : `python:3.12-slim`

  * **Ruby Integration** : For AsciiDoc processing

  * **Model Preloading** : SpaCy and NLTK data

  * **Health Checks** : Built-in health monitoring

  * **Non-root User** : Security best practice

Key features:
[code] 
    # Multi-layer caching for fast rebuilds
    # Precomputed embeddings at build time
    # Offline-first model loading
    # Gunicorn production server
[/code]

## GitLab CI/CD Deployment

### Pipeline Configuration

The project uses GitLab CI/CD with LightRail platform integration.

Current pipeline (`.gitlab-ci.yml`):
[code] 
    stages:
      - build
      - deploy-preview
      - deploy-qa
      - deploy-stage
      - deploy-prod
      - clean
    
    variables:
      LIGHTRAIL_VERSION: 1.5.0
      LIGHTRAIL_RELEASE_BRANCH: main
    
    include:
      - project: dxp/platforms-pipelines/lightrail-platform/lightrail
        ref: 1.5.0
        file:
          - pipeline/global.yaml
          - pipeline/stages/build/build.yaml
          - pipeline/stages/deploy/deploy.yaml
          - pipeline/stages/clean/clean.yaml
[/code]

### Environment-Specific Deployment

Deployments are currently disabled by default:
[code] 
    build-release:
      rules:
        - when: never
    deploy-qa:
      rules:
        - when: never
[/code]

**To enable deployments** , modify these rules in `.gitlab-ci.yml`.

### CI/CD Variables

Configure in GitLab at **Settings → CI/CD → Variables** :

#### Required Variables

Variable | Type | Description  
---|---|---  
`MODEL_PROVIDER` | Text | AI provider (`ollama`, `api`, `llamastack`)  
`BASE_URL` | Text | API endpoint URL  
`ACCESS_TOKEN` | Secret (Masked) | API authentication token  
`DATABASE_URL` | Secret (Masked) | Production database connection string  
`SECRET_KEY` | Secret (Masked) | Flask session encryption key  
  
#### Optional Variables

  * `MODEL_ID` \- Specific model to use

  * `MODEL_TEMPERATURE` \- Generation temperature

  * `LOG_LEVEL` \- Logging verbosity

  * `SENTRY_DSN` \- Error tracking (if enabled)

### Security Best Practices

  1. **Mark secrets as Masked** : Hides values in job logs

  2. **Mark production vars as Protected** : Only accessible on protected branches

  3. **Use environment scopes** : Separate dev/staging/prod variables

  4. **Rotate keys regularly** : Update `ACCESS_TOKEN` periodically

## LightRail Platform Deployment

LightRail is Red Hat's internal platform for deploying AI-powered applications.

### Architecture
[code] 
    ┌─────────────────────────────────────┐
    │     Content Editorial Assistant      │
    │            (Your App)                │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │          LlamaStack                  │
    │    (AI Model Serving Layer)         │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │        LightRail Platform            │
    │  (Infrastructure & Orchestration)   │
    └─────────────────────────────────────┘
[/code]

### Configuration

LlamaStack configuration in `llamastack/config.yaml`:
[code] 
    # LlamaStack configuration
    model_id: style_analyzer_model
    provider: lightrail
    # Additional LightRail-specific settings
[/code]

Environment variables for LlamaStack:
[code] 
    MODEL_PROVIDER=llamastack
    CEA_MODEL_ID=style_analyzer_model
[/code]

### Deployment Process

  1. **Build** : GitLab CI builds Docker image

  2. **Push** : Image pushed to LightRail registry

  3. **Deploy** : LightRail orchestrates deployment

  4. **Health Check** : Automated health verification

  5. **Traffic Routing** : Gradual traffic shift

### OpenShift Configuration

The project includes OpenShift manifests:

**`openshift-deployment-patch.yaml`** : * Persistent volume configuration * Database persistence * Environment variable injection

**`openshift-route.yaml`** : * External access configuration * TLS termination * Custom domain support

### Monitoring

LightRail provides:

  * **Metrics** : Prometheus-based monitoring

  * **Logs** : Centralized log aggregation

  * **Alerts** : Automated alerting on failures

  * **Dashboards** : Real-time performance visualization

## Production Checklist

### Pre-Deployment

  * ❏ **Python version** : 3.12+ verified

  * ❏ **Dependencies** : All installed and tested

  * ❏ **Tests** : All tests passing

  * ❏ **Environment variables** : Configured and validated

  * ❏ **Database** : Migrations applied

  * ❏ **AI models** : Available and tested

  * ❏ **Security** : Secrets not committed

### Configuration Review

  * ❏ **SECRET_KEY** : Strong random key set

  * ❏ **DEBUG mode** : Disabled in production

  * ❏ **CORS origins** : Restricted to actual domains

  * ❏ **Database** : Production database configured

  * ❏ **Logging** : Appropriate log level (INFO or WARNING)

  * ❏ **File uploads** : Size limits configured

### Performance

  * ❏ **Gunicorn** : Configured with appropriate workers

  * ❏ **Database pool** : Connection pool sized correctly

  * ❏ **Caching** : Model caching enabled

  * ❏ **Health checks** : Configured and tested

### Monitoring

  * ❏ **Logging** : Logs aggregated and monitored

  * ❏ **Metrics** : Prometheus metrics exposed

  * ❏ **Alerts** : Critical alerts configured

  * ❏ **Error tracking** : Sentry or similar configured

## Post-Deployment Verification

### Health Check
[code] 
    curl https://your-domain.com/health
    
    # Expected response:
    {
      "status": "healthy",
      "services": {
        "document_processor": "available",
        "style_analyzer": "available",
        "ai_rewriter": "available",
        "database": "available"
      }
    }
[/code]

### Smoke Tests
[code] 
    # Test file upload
    curl -X POST https://your-domain.com/upload \
      -F "file=@test.txt"
    
    # Test analysis
    curl -X POST https://your-domain.com/analyze \
      -H "Content-Type: application/json" \
      -d '{"text": "Test content", "content_type": "concept"}'
[/code]

### Performance Baseline

Monitor these metrics:

  * **Response time** : < 2s for analysis

  * **Memory usage** : Stable under 2GB

  * **CPU usage** : < 70% average

  * **Error rate** : < 1%

## Troubleshooting

### Application Won't Start

**Check logs** :
[code] 
    # Docker
    docker logs cea
    
    # LightRail
    oc logs -f deployment/cea
    
    # Local
    tail -f logs/app.log
[/code]

**Common issues** :

  * Missing environment variables

  * Database connection failure

  * Port already in use

  * Permission issues

### Model Provider Issues

**Ollama not accessible** :
[code] 
    # Verify Ollama is running
    curl http://localhost:11434/api/tags
    
    # Check firewall rules
    # Ensure network connectivity
[/code]

**API provider authentication fails** :
[code] 
    # Verify API key
    curl -H "Authorization: Bearer $ACCESS_TOKEN" $BASE_URL/models
    
    # Check key permissions
    # Verify BASE_URL is correct
[/code]

### Database Connection Issues

**PostgreSQL connection fails** :
[code] 
    # Test connection
    psql "$DATABASE_URL"
    
    # Check connection string format
    # Verify host, port, credentials
    # Check firewall/security groups
[/code]

### High Memory Usage

**Solutions** :

  1. Reduce Gunicorn workers: `GUNICORN_WORKERS=2`

  2. Clear cache: Restart application

  3. Check for memory leaks: Use memory profiler

  4. Upgrade instance: More RAM may be needed

## Scaling Considerations

### Horizontal Scaling

For high traffic:

  1. **Multiple instances** : Run behind load balancer

  2. **Stateless design** : Session data in Redis

  3. **External database** : Shared PostgreSQL instance

  4. **Distributed caching** : Redis for model caching

### Vertical Scaling

Resource recommendations:

Traffic Level | CPU | RAM | Workers  
---|---|---|---  
Low (< 100 req/day) | 1 core | 2 GB | 2  
Medium (< 1000 req/day) | 2 cores | 4 GB | 4  
High (< 10000 req/day) | 4 cores | 8 GB | 8  
Very High (10000+ req/day) | 8+ cores | 16+ GB | 16+  
  
## Backup and Recovery

### Database Backups
[code] 
    # PostgreSQL backup
    pg_dump "$DATABASE_URL" > backup_$(date +%Y%m%d).sql
    
    # Restore
    psql "$DATABASE_URL" < backup_20240115.sql
[/code]

### Application State
[code] 
    # Backup instance folder (SQLite database)
    tar -czf instance_backup.tar.gz instance/
    
    # Backup logs
    tar -czf logs_backup.tar.gz logs/
    
    # Backup uploaded files
    tar -czf uploads_backup.tar.gz uploads/
[/code]

## See Also

  * [Environment Variables Reference](<environment-variables.html>)

  * [Getting Started Guide](<getting-started.html>)

  * [System Architecture](<architecture:architecture.html>)

Last updated 2026-01-22 23:36:56 +0530 
