# Models Module

Centralized AI model management for the Style Guide Application.

## Quick Start

```python
from models import ModelManager

manager = ModelManager()
result = manager.generate_text("Your prompt here...")
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

Set `MODEL_PROVIDER` in `models/config.py`:
- `ollama` - Local models
- `api` - External APIs (Groq, HuggingFace, OpenAI)  
- `llamastack` - Lightrail platform

## Setup

### Ollama (Local)
```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama3:8b
```

### API Providers
```bash
export API_KEY='your-api-key'
```

## Testing

```bash
python -m models.test_models
```

## API Reference

```python
from models import ModelManager

manager = ModelManager()
text = manager.generate_text("Your prompt here")
status = manager.get_status()
health = manager.health_check()
```

## Adding Custom Providers

```python
from .base_provider import BaseModelProvider
from models import ModelFactory

class CustomProvider(BaseModelProvider):
    # Implement abstract methods

ModelFactory.register_provider('custom', CustomProvider)
```

## Environment Variables

```bash
MODEL_PROVIDER=ollama          # or 'api', 'llamastack'
OLLAMA_MODEL=llama3:8b
API_KEY=your-api-key
API_PROVIDER=groq              # groq, huggingface, openai
``` 