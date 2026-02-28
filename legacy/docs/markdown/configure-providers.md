# How to Configure AI Model Providers

## Overview

Content Editorial Assistant supports multiple AI model providers for flexibility and choice. This guide shows you how to configure each provider.

## Supported Providers

Provider | Best For | Requirements  
---|---|---  
**Ollama** | Privacy-first local deployment | Ollama installed locally  
**API Providers** | Cloud-based inference, no local setup | API key from supported provider  
**LlamaStack** | Enterprise deployment on LightRail | LightRail platform access  
  
## Ollama (Local LLM Serving)

### Why Choose Ollama?

  * ✅ **Privacy** : Models run entirely on your machine

  * ✅ **No API costs** : Free after initial setup

  * ✅ **Fast** : No network latency

  * ✅ **Offline** : Works without internet

### Installation

**Linux** :
[code] 
    curl -fsSL https://ollama.com/install.sh | sh
[/code]

**macOS** :
[code] 
    # Download from https://ollama.com/download/mac
    # Or with Homebrew:
    brew install ollama
[/code]

**Windows** : Download installer from <https://ollama.com/download/windows>

### Pull Models
[code] 
    # Recommended: llama3:8b (superior quality)
    ollama pull llama3:8b
    
    # Alternative: llama3.2:3b (faster, smaller)
    ollama pull llama3.2:3b
    
    # List available models
    ollama list
[/code]

### Configuration

Create `.env` file:
[code] 
    MODEL_PROVIDER=ollama
    BASE_URL=http://localhost:11434
    MODEL_ID=llama3:8b
    TIMEOUT=60
    MODEL_TEMPERATURE=0.4
    MODEL_MAX_TOKENS=3072
[/code]

### Start Ollama Server
[code] 
    # Start server
    ollama serve
    
    # Verify it's running
    curl http://localhost:11434/api/tags
[/code]

### Testing
[code] 
    # Test from command line
    ollama run llama3:8b "Rewrite this text to be clearer: The system was configured."
    
    # Test from Python
    python -c "from models import ModelManager; print(ModelManager().get_status())"
[/code]

## API Providers (Cloud-based)

### Supported API Providers

#### Groq (Recommended for API)

**Why Groq?** * Fastest inference speed * Free tier available * Llama 3 70B model access

**Setup** :

  1. Get API key: <https://console.groq.com/keys>

  2. Configure:

[code] 
    MODEL_PROVIDER=api
    BASE_URL=https://api.groq.com/openai/v1
    MODEL_ID=llama3-70b-8192
    ACCESS_TOKEN=gsk_your_api_key_here
    TIMEOUT=60
[/code]

#### HuggingFace Inference API

**Why HuggingFace?** * Wide model selection * Free tier available * Community models

**Setup** :

  1. Get API key: <https://huggingface.co/settings/tokens>

  2. Configure:

[code] 
    MODEL_PROVIDER=api
    BASE_URL=https://api-inference.huggingface.co/models
    MODEL_ID=meta-llama/Llama-3-8b-hf
    ACCESS_TOKEN=hf_your_api_key_here
    TIMEOUT=120
[/code]

#### OpenAI

**Why OpenAI?** * High-quality models (GPT-4) * Reliable API * Advanced features

**Setup** :

  1. Get API key: <https://platform.openai.com/api-keys>

  2. Configure:

[code] 
    MODEL_PROVIDER=api
    BASE_URL=https://api.openai.com/v1
    MODEL_ID=gpt-4
    ACCESS_TOKEN=sk_your_api_key_here
    TIMEOUT=60
[/code]

#### Custom OpenAI-Compatible APIs

Any OpenAI-compatible API endpoint works:
[code] 
    MODEL_PROVIDER=api
    BASE_URL=https://your-custom-api.com/v1
    MODEL_ID=your-model-name
    ACCESS_TOKEN=your_api_key
    CERT_PATH=/path/to/certificate.pem  # Optional for self-signed certs
    TIMEOUT=60
[/code]

### API Provider Configuration Reference

Variable | Required | Description  
---|---|---  
`MODEL_PROVIDER` | ✅ Yes | Set to `api`  
`BASE_URL` | ✅ Yes | API endpoint URL  
`MODEL_ID` | ✅ Yes | Model identifier  
`ACCESS_TOKEN` | ✅ Yes | API authentication key  
`CERT_PATH` | ⚠️ Optional | Certificate path for custom APIs  
`TIMEOUT` | ⚠️ Optional | Request timeout (default: 60s)  
  
### Testing API Connection
[code] 
    # Test API connectivity
    curl -H "Authorization: Bearer $ACCESS_TOKEN" \
         -H "Content-Type: application/json" \
         -d '{"model": "'"$MODEL_ID"'", "messages": [{"role": "user", "content": "Hello"}]}' \
         "$BASE_URL/chat/completions"
    
    # Test from Python
    python -m models.test_models
[/code]

## LlamaStack (LightRail Platform)

### Overview

LlamaStack provides enterprise-grade AI model serving on Red Hat's LightRail platform.

### Why LlamaStack?

  * ✅ **Enterprise security** : SOC 2 compliant

  * ✅ **Managed infrastructure** : No server management

  * ✅ **Integrated monitoring** : Built-in observability

  * ✅ **Scalable** : Auto-scaling based on load

### Prerequisites

  * Access to LightRail platform

  * Model deployed on LlamaStack

  * Model ID assigned by platform team

### Configuration
[code] 
    MODEL_PROVIDER=llamastack
    CEA_MODEL_ID=style_analyzer_model  # Your model ID
[/code]

**Note** : LlamaStack configuration is simplified because authentication and endpoints are managed by the platform.

### LlamaStack Configuration File

Additional settings in `llamastack/config.yaml`:
[code] 
    model_id: style_analyzer_model
    provider: lightrail
    # Additional platform-specific settings
[/code]

### Integration

The application automatically integrates with LlamaStack when deployed to LightRail:
[code] 
    # In main.py
    from llama_stack_client import LlamaStackClient
    
    # Setup LlamaStack client
    setup_llama_stack_client()
    
    # Client is automatically injected into app context
    if llama_stack_client:
        app.llama_stack_client = llama_stack_client
[/code]

### Testing
[code] 
    # Verify LlamaStack connectivity
    python -c "from models import ModelManager; print(ModelManager().health_check())"
[/code]

## Switching Between Providers

### Runtime Provider Switch

You can switch providers programmatically:
[code] 
    from models import ModelManager
    
    manager = ModelManager()
    
    # Switch to Ollama
    manager.switch_provider('ollama', {
        'base_url': 'http://localhost:11434',
        'model': 'llama3:8b'
    })
    
    # Switch to API provider
    manager.switch_provider('api', {
        'base_url': 'https://api.groq.com/openai/v1',
        'model': 'llama3-70b-8192',
        'api_key': 'your-key-here'
    })
[/code]

### Environment-Based Selection

Use different `.env` files for different environments:
[code] 
    # .env.development (local Ollama)
    MODEL_PROVIDER=ollama
    MODEL_ID=llama3:8b
    
    # .env.staging (Groq API)
    MODEL_PROVIDER=api
    BASE_URL=https://api.groq.com/openai/v1
    MODEL_ID=llama3-70b-8192
    
    # .env.production (LlamaStack)
    MODEL_PROVIDER=llamastack
    CEA_MODEL_ID=style_analyzer_model
[/code]

Load appropriate file:
[code] 
    # Development
    ln -sf .env.development .env
    
    # Staging
    ln -sf .env.staging .env
    
    # Production
    ln -sf .env.production .env
[/code]

## Model Parameters Configuration

### Temperature

Controls randomness (0.0 = deterministic, 1.0 = creative):
[code] 
    MODEL_TEMPERATURE=0.4  # Recommended for technical writing
[/code]

  * **0.1-0.3** : Very focused, minimal creativity

  * **0.4-0.6** : Balanced (recommended)

  * **0.7-0.9** : More creative, less predictable

### Max Tokens

Maximum generation length:
[code] 
    MODEL_MAX_TOKENS=3072  # Default, suitable for most content
[/code]

### Top-P Sampling

Nucleus sampling parameter (0.0-1.0):
[code] 
    MODEL_TOP_P=0.7  # Recommended
[/code]

### Top-K Sampling

Limits to top K tokens:
[code] 
    MODEL_TOP_K=20  # Recommended
[/code]

## Troubleshooting

### Ollama Connection Failed

**Error** : `Connection refused` to `localhost:11434`

**Solutions** :

  1. Verify Ollama is running:
[code] ps aux | grep ollama
         curl http://localhost:11434/api/tags
[/code]

  2. Start Ollama server:
[code] ollama serve
[/code]

  3. Check firewall rules

### API Authentication Failed

**Error** : `401 Unauthorized`

**Solutions** :

  1. Verify API key:
[code] echo $ACCESS_TOKEN
[/code]

  2. Check key permissions in provider dashboard

  3. Regenerate key if expired

### Model Not Found

**Error** : `Model 'xyz' not found`

**Solutions** :

  1. List available models:
[code] # Ollama
         ollama list
         
         # API providers
         curl -H "Authorization: Bearer $ACCESS_TOKEN" $BASE_URL/models
[/code]

  2. Pull/select correct model

  3. Check MODEL_ID spelling

### Timeout Errors

**Error** : Request timeout after 60s

**Solutions** :

  1. Increase timeout:
[code] TIMEOUT=120
[/code]

  2. Use faster model

  3. Reduce MAX_TOKENS

## Performance Optimization

### Model Selection Guide

Model | Speed | Quality | Size  
---|---|---|---  
`llama3.2:1b` | ⚡⚡⚡ Very Fast | ⭐⭐ Basic | 1.3GB  
`llama3.2:3b` | ⚡⚡ Fast | ⭐⭐⭐ Good | 2GB  
`llama3:8b` | ⚡ Moderate | ⭐⭐⭐⭐ Excellent | 4.7GB  
`llama3-70b-8192` (API) | ⚡⚡⚡ Fast (cloud) | ⭐⭐⭐⭐⭐ Superior | Cloud  
  
### Caching Recommendations

Enable model caching for faster responses:
[code] 
    # Ollama keeps models in memory
    # API providers cache at their end
    # Application caches model connections
[/code]

### Resource Requirements

**Ollama Local Deployment** :

  * llama3:8b: 8GB RAM minimum

  * llama3.2:3b: 4GB RAM minimum

  * GPU: Optional but recommended

**API Providers** :

  * No local resources needed

  * Network bandwidth important

## Best Practices

  1. **Use Ollama for development** : Fast iteration, no API costs

  2. **Use API providers for production** : Reliable, scalable

  3. **Test before switching** : Validate provider works in your environment

  4. **Monitor API usage** : Track costs and quotas

  5. **Set appropriate timeouts** : Balance speed vs reliability

  6. **Keep models updated** : `ollama pull <model>` regularly

## See Also

  * [Environment Variables Reference](<ROOT:environment-variables.html>)

  * [Getting Started Guide](<ROOT:getting-started.html>)

  * [Deployment Guide](<ROOT:deployment-guide.html>)

  * [Models Module Documentation](<../../models/README.md>)

Last updated 2025-11-25 12:56:47 +0530 
