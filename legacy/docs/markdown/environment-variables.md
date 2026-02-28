# Environment variables reference

Note |  **This documentation is for developers and system administrators** who are deploying or configuring Content Editorial Assistant locally or in production environments.  
---|---  
  
## Overview

Content Editorial Assistant uses environment variables for configuration. This guide provides a complete reference for all available variables.

## Configuration methods

### 1\. .env file (recommended for development)

Create a `.env` file in the project root:
[code] 
    MODEL_PROVIDER=ollama
    OLLAMA_MODEL=llama3:8b
    MODEL_TEMPERATURE=0.4
[/code]

### 2\. Environment variables (production)

Export variables in your shell or CI/CD pipeline:
[code] 
    export MODEL_PROVIDER=api
    export BASE_URL=https://api.groq.com/openai/v1
    export ACCESS_TOKEN=your-token-here
[/code]

### 3\. GitLab CI/CD variables

For GitLab CI/CD, add variables at **Settings → CI/CD → Variables** :

  * Mark sensitive keys as **Masked**

  * Mark production keys as **Protected**

## AI model configuration

### Model provider selection

Variable | Default | Description  
---|---|---  
`MODEL_PROVIDER` | `ollama` | AI provider: `ollama`, `api`, or `llamastack`  
`MODEL_ID` | `llama3:8b` | Model identifier specific to your provider  
`MODEL_TEMPERATURE` | `0.4` | Generation temperature (0.0-1.0)  
`MODEL_MAX_TOKENS` | `3072` | Maximum tokens per generation  
`MODEL_TOP_P` | `0.7` | Top-p sampling parameter  
`MODEL_TOP_K` | `20` | Top-k sampling parameter  
  
### Ollama configuration (local)
[code] 
    MODEL_PROVIDER=ollama
    BASE_URL=http://localhost:11434
    MODEL_ID=llama3:8b
    TIMEOUT=60
[/code]

**Prerequisites:** * Ollama installed and running * Model pulled: `ollama pull llama3:8b`

### API Provider Configuration (Remote)
[code] 
    MODEL_PROVIDER=api
    BASE_URL=https://api.groq.com/openai/v1
    MODEL_ID=llama3-70b-8192
    ACCESS_TOKEN=gsk_your_api_key_here
    TIMEOUT=60
    CERT_PATH=true  # or path to custom certificate
[/code]

**Supported API Providers:**

  * **Groq** : Fast inference for Llama models

  * **HuggingFace** : Wide model selection

  * **OpenAI** : GPT models

  * Any OpenAI-compatible API

### LlamaStack Configuration (LightRail Platform)
[code] 
    MODEL_PROVIDER=llamastack
    CEA_MODEL_ID=style_analyzer_model
[/code]

**Prerequisites:** * LightRail platform access * Model deployed on LlamaStack

## Flask Application Configuration

Variable | Default | Description  
---|---|---  
`FLASK_DEBUG` | `False` | Enable debug mode (development only)  
`FLASK_ENV` | `production` | Environment: `development` or `production`  
`SECRET_KEY` | Auto-generated | Session encryption key (set in production)  
`PORT` | `5000` | Application port  
`HOST` | `127.0.0.1` | Application host (use `0.0.0.0` for Docker)  
  
## Database Configuration

Variable | Default | Description  
---|---|---  
`DATABASE_URL` | `sqlite:///instance/content_editorial_assistant.db` | Database connection string  
`SQLALCHEMY_TRACK_MODIFICATIONS` | `False` | Track modifications (leave disabled)  
`SQLALCHEMY_POOL_SIZE` | `10` | Connection pool size  
`SQLALCHEMY_MAX_OVERFLOW` | `20` | Max overflow connections  
  
### PostgreSQL Configuration
[code] 
    DATABASE_URL=postgresql://user:password@localhost:5432/cea_db
    SQLALCHEMY_POOL_SIZE=20
    SQLALCHEMY_MAX_OVERFLOW=40
[/code]

## File Upload Configuration

Variable | Default | Description  
---|---|---  
`MAX_CONTENT_LENGTH` | `16777216` | Max upload size in bytes (16MB default)  
`UPLOAD_FOLDER` | `uploads` | Upload directory path  
`ALLOWED_EXTENSIONS` | `txt,pdf,docx,md,adoc,dita` | Allowed file extensions  
  
## Analysis Configuration

Variable | Default | Description  
---|---|---  
`CONFIDENCE_THRESHOLD` | `0.43` | Minimum confidence for error reporting (0.0-1.0)  
`ENABLE_SPACY` | `true` | Enable SpaCy NLP analysis  
`ENABLE_RULES` | `true` | Enable style rules system  
`ENABLE_AMBIGUITY_DETECTION` | `true` | Enable ambiguity detection  
`ENABLE_MODULAR_COMPLIANCE` | `true` | Enable modular compliance checking  
  
## Performance & Monitoring

Variable | Default | Description  
---|---|---  
`LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`  
`LOG_FILE` | `logs/app.log` | Log file path  
`METRICS_ENABLED` | `true` | Enable Prometheus metrics  
`WEBSOCKET_PING_INTERVAL` | `25` | WebSocket ping interval (seconds)  
`WEBSOCKET_PING_TIMEOUT` | `60` | WebSocket timeout (seconds)  
  
## Testing Configuration

Variable | Default | Description  
---|---|---  
`TESTING` | `false` | Enable testing mode  
`TEST_DATABASE_URL` | `:memory:` | Test database (in-memory SQLite)  
`AI_TEST_PROVIDER` | Same as `MODEL_PROVIDER` | AI provider for tests  
  
## Security Configuration

Variable | Default | Description  
---|---|---  
`SESSION_COOKIE_SECURE` | `true` in production | Require HTTPS for cookies  
`SESSION_COOKIE_HTTPONLY` | `true` | Prevent JavaScript access to cookies  
`SESSION_COOKIE_SAMESITE` | `Lax` | CSRF protection: `Strict`, `Lax`, or `None`  
`CORS_ORIGINS` | `*` | Allowed CORS origins (comma-separated)  
  
## Example Configurations

### Development with Local Ollama
[code] 
    # .env file
    FLASK_DEBUG=true
    FLASK_ENV=development
    MODEL_PROVIDER=ollama
    MODEL_ID=llama3:8b
    BASE_URL=http://localhost:11434
    LOG_LEVEL=DEBUG
[/code]

### Production with Groq API
[code] 
    # Production environment variables
    FLASK_ENV=production
    SECRET_KEY=your-secret-key-here
    MODEL_PROVIDER=api
    BASE_URL=https://api.groq.com/openai/v1
    MODEL_ID=llama3-70b-8192
    ACCESS_TOKEN=gsk_your_api_key_here
    DATABASE_URL=postgresql://user:pass@db.example.com:5432/cea
    HOST=0.0.0.0
    PORT=5000
    LOG_LEVEL=INFO
[/code]

### LightRail Platform Deployment
[code] 
    # LightRail configuration
    FLASK_ENV=production
    MODEL_PROVIDER=llamastack
    CEA_MODEL_ID=style_analyzer_model
    DATABASE_URL=postgresql://...
    HOST=0.0.0.0
    PORT=8080
[/code]

### Testing Environment
[code] 
    # Test configuration
    TESTING=true
    TEST_DATABASE_URL=:memory:
    MODEL_PROVIDER=ollama
    AI_TEST_PROVIDER=ollama
    LOG_LEVEL=DEBUG
[/code]

## Validation

Verify your configuration:
[code] 
    # Check model provider
    python -c "from models import ModelManager; print(ModelManager().get_status())"
    
    # Check database connection
    python -c "from database import db; print('Database OK')"
    
    # Full configuration check
    python -m scripts.validate_config
[/code]

## Troubleshooting

### Model Provider Issues

**Problem** : `ModelManager` fails to initialize

**Solution** : Check provider-specific requirements:
[code] 
    # For Ollama
    curl http://localhost:11434/api/tags
    
    # For API providers
    curl -H "Authorization: Bearer $ACCESS_TOKEN" $BASE_URL/models
[/code]

### Database Connection Issues

**Problem** : Database connection fails

**Solution** : Verify connection string format:
[code] 
    # SQLite (relative path)
    DATABASE_URL=sqlite:///instance/cea.db
    
    # PostgreSQL
    DATABASE_URL=postgresql://user:pass@host:5432/dbname
[/code]

### Environment Variable Not Loading

**Problem** : Variables from `.env` not recognized

**Solution** : Ensure `python-dotenv` is installed and `.env` is in project root:
[code] 
    pip install python-dotenv
    ls -la .env  # Should exist in project root
[/code]

## Security Best Practices

  1. **Never commit`.env` files** \- Add to `.gitignore`

  2. **Use masked variables in CI/CD** \- Prevent exposure in logs

  3. **Rotate API keys regularly** \- Update `ACCESS_TOKEN` periodically

  4. **Use strong SECRET_KEY** \- Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`

  5. **Limit CORS origins** \- Don't use `*` in production

## See Also

  * [Getting Started Guide](<getting-started.html>)

  * [Deployment Guide](<deployment-guide.html>)

  * [Configure AI Providers](<how-to:configure-providers.html>)

Last updated 2026-01-22 23:36:56 +0530 
