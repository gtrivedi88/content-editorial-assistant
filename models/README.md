# Models Module

Centralized AI model management for the Style Guide Application.

## Quick Start

```python
from models import ModelManager

# Basic usage
manager = ModelManager()
result = manager.generate_text("Rewrite this text to be more concise...")
print(result)

# Check if model is ready
if manager.is_available():
    print("Model ready!")
else:
    print("Model not available")
```

## Directory Structure

```
models/
├── config.py              # Main configuration
├── model_manager.py       # Primary interface  
├── factory.py             # Provider factory
├── test_models.py         # Testing utility
├── providers/             # Provider implementations
│   ├── base_provider.py   # Abstract base
│   ├── ollama_provider.py # Local Ollama
│   └── api_provider.py    # External APIs
├── __init__.py            # Module exports
└── README.md              # This file
```

## Configuration

### Current Setup (Ollama - Default)
Your current configuration uses **Ollama** with **llama3:8b** locally.

### Switching Providers

You can switch providers using either of these approaches (choose one, not both):

#### Option 1: Edit Configuration File (Persistent Changes)
Edit `models/config.py` to permanently change the provider:

```python
# For Ollama (local)
ACTIVE_PROVIDER = 'ollama'
OLLAMA_MODEL = 'llama3:8b'  # or any model you have

# For Groq API  
ACTIVE_PROVIDER = 'api'
API_PROVIDER = 'groq'
API_MODEL = 'llama3-70b-8192'

# For HuggingFace API
ACTIVE_PROVIDER = 'api'  
API_PROVIDER = 'huggingface'
API_MODEL = 'meta-llama/Llama-2-70b-chat-hf'
```

#### Option 2: Programmatic Switching (Runtime Changes)
Switch providers during runtime without editing configuration files:

```python
from models import ModelManager

manager = ModelManager()

# Switch to Groq
manager.switch_provider('api', {
    'api_provider': 'groq',
    'model': 'llama3-70b-8192',
    'api_key': 'your-groq-key'
})

# Switch to different Ollama model
manager.switch_provider('ollama', {
    'model': 'mistral:7b'
})
```

**Note**: Option 1 makes permanent changes that persist across application restarts. Option 2 makes temporary changes that only last for the current session.

## Setup Instructions

### Ollama (Local - Recommended for Development)

1. **Install Ollama**
   ```bash
   # Visit https://ollama.com/ for installation
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. **Start Ollama Service**
   ```bash
   ollama serve
   ```

3. **Pull Models**
   ```bash
   ollama pull llama3:8b        # Default
   ollama pull mistral:7b       # Alternative
   ollama pull codellama:7b     # For code tasks
   ```

4. **Verify Setup**
   ```bash
   python -m models.test_models
   ```

### Groq API (Fast Cloud Inference)

1. **Get API Key**
   - Visit [Groq Console](https://console.groq.com/)
   - Create account and get API key

2. **Set Environment Variable**
   ```bash
   export API_KEY='your-groq-api-key'
   ```

3. **Update Configuration**
   ```python
   # In models/config.py
   ACTIVE_PROVIDER = 'api'
   API_PROVIDER = 'groq'
   API_MODEL = 'llama3-70b-8192'  # or mixtral-8x7b-32768
   ```

### HuggingFace API

1. **Get API Token**
   - Visit [HuggingFace Tokens](https://huggingface.co/settings/tokens)
   - Create token with read access

2. **Set Environment Variable**
   ```bash
   export API_KEY='your-hf-token'
   ```

3. **Update Configuration**
   ```python
   # In models/config.py
   ACTIVE_PROVIDER = 'api'
   API_PROVIDER = 'huggingface'
   API_MODEL = 'meta-llama/Llama-2-70b-chat-hf'
   ```

## Testing Your Setup

Run the comprehensive test suite:

```bash
python -m models.test_models
```

This will test:
- Configuration validation
- Model connectivity  
- Health checks
- Text generation

## API Reference

### ModelManager (Primary Interface)

```python
from models import ModelManager

manager = ModelManager()

# Generate text
text = manager.generate_text("Your prompt here", temperature=0.7)

# Check availability
is_ready = manager.is_available()

# Get status
status = manager.get_status()

# Health check
health = manager.health_check()

# Test generation
test_result = manager.test_generation()
```

### Quick Functions

```python
from models import quick_generate, is_model_available, check_model_status

# Quick generation without creating manager
result = quick_generate("Rewrite this text...")

# Quick checks
if is_model_available():
    status = check_model_status()
    print(f"Using: {status['model']}")
```

## Adding Custom Providers

1. **Create Provider Class**
   ```python
   # models/providers/custom_provider.py
   from .base_provider import BaseModelProvider
   
   class CustomProvider(BaseModelProvider):
       def connect(self):
           # Implementation
           pass
       
       def generate_text(self, prompt, **kwargs):
           # Implementation 
           pass
       
       # ... implement other abstract methods
   ```

2. **Register Provider**
   ```python
   from models import ModelFactory
   from .providers.custom_provider import CustomProvider
   
   ModelFactory.register_provider('custom', CustomProvider)
   ```

3. **Use Custom Provider**
   ```python
   # In config.py
   ACTIVE_PROVIDER = 'custom'
   ```

## Troubleshooting

### Common Issues

**"Ollama is not responding"**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama if not running
ollama serve

# Check available models
ollama list
```

**"Model not found in Ollama"**
```bash
# Pull the required model
ollama pull llama3:8b

# List available models
ollama list
```

**"API key missing"**
```bash
# Set API key environment variable
export API_KEY='your-api-key'

# Verify it's set
echo $API_KEY
```

**"Provider not available"**
```python
# Check configuration
from models import ModelConfig
print(ModelConfig.get_active_config())

# Force reconnect
from models import ModelManager
manager = ModelManager()
success = manager.force_reconnect()
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from models import ModelManager
manager = ModelManager()
```

## Features

- **Provider Abstraction**: Switch between Ollama, Groq, HuggingFace, OpenAI seamlessly
- **Only One Active**: Efficient "one provider at a time" resource management
- **Configuration-Driven**: Easy setup via config files or environment variables
- **Health Monitoring**: Comprehensive health checks and status reporting
- **Error Handling**: Graceful failure handling with helpful error messages
- **Testing Utilities**: Built-in test suite for validation
- **Extensible**: Easy to add new providers

## Environment Variables

```bash
# Provider selection
MODEL_PROVIDER=ollama          # or 'api'

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:8b
OLLAMA_TIMEOUT=60

# API settings  
API_PROVIDER=groq              # groq, huggingface, openai
API_MODEL=llama3-70b-8192
API_KEY=your-api-key
API_BASE_URL=https://api.groq.com/openai/v1
API_TIMEOUT=30

# Generation parameters
MODEL_TEMPERATURE=0.4
MODEL_MAX_TOKENS=512
MODEL_TOP_P=0.7
MODEL_TOP_K=20
```

## Performance Tips

1. **Local Development**: Use Ollama with smaller models (7B-8B parameters)
2. **Production**: Use API providers for better performance and reliability
3. **Batch Processing**: Reuse ModelManager instance for multiple generations
4. **Resource Management**: The system automatically cleans up unused providers

## Integration

### Using in Rewriter Module

```python
# Instead of the old approach
from models import ModelManager

class RewriterService:
    def __init__(self):
        self.model_manager = ModelManager()
    
    def rewrite_text(self, text, rules):
        if not self.model_manager.is_available():
            raise RuntimeError("AI model not available")
        
        prompt = f"Rewrite according to rules: {rules}\nText: {text}"
        return self.model_manager.generate_text(prompt)
```

### Using in Other Modules

```python
# Any module that needs AI capabilities
from models import quick_generate, is_model_available

def enhance_text(text):
    if not is_model_available():
        return text  # Fallback to original
    
    return quick_generate(f"Enhance this text: {text}")
```

---

**Need help?** Run `python -m models.test_models` for diagnostics or check the troubleshooting section above. 