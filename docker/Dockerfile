# Peer Lens AI Writing Assistant - Full Version
# Complete AI-powered writing assistant with Ollama, Llama 8B, and all NLP dependencies
# Optimized for regular users with fast startup and maximum reliability

FROM python:3.12

# Set environment variables for optimal performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    OLLAMA_HOST=0.0.0.0 \
    OLLAMA_PORT=11434 \
    OLLAMA_KEEP_ALIVE=24h \
    OLLAMA_MAX_LOADED_MODELS=1 \
    FLASK_ENV=production

# Install system dependencies in a single layer for efficiency
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    pkg-config \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Ollama (cached unless Ollama updates)
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Create app directory
WORKDIR /app

# Copy ONLY requirements.txt first for better caching
COPY requirements.txt .

# Install Python dependencies (cached unless requirements.txt changes)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Download NLP models (cached unless spaCy/NLTK versions change)
RUN python -m spacy download en_core_web_sm && \
    python -m spacy download en_core_web_md && \
    python -c "\
import nltk; \
nltk.download('punkt', quiet=True); \
nltk.download('stopwords', quiet=True); \
nltk.download('wordnet', quiet=True); \
nltk.download('averaged_perceptron_tagger', quiet=True); \
print('✅ NLTK data downloaded successfully')"

# Download Llama 8B model (THIS WILL BE CACHED! 🎉)
# Only re-downloads if Ollama version changes
RUN echo "🤖 Downloading Llama 8B model (cached after first build)..." && \
    ollama serve & \
    OLLAMA_PID=$! && \
    sleep 20 && \
    echo "📥 Pulling Llama 8B model..." && \
    ollama pull llama3:8b && \
    echo "✅ Llama 8B model cached successfully!" && \
    ollama list && \
    sleep 5 && \
    kill $OLLAMA_PID

# Create necessary directories with proper permissions
RUN mkdir -p uploads instance templates static logs && \
    chmod 755 uploads instance logs

# Copy application code LAST (changes here won't invalidate model cache)
COPY . .

# Create optimized startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starting Peer Lens AI Writing Assistant..."\n\
echo "📦 Starting Ollama service..."\n\
ollama serve &\n\
OLLAMA_PID=$!\n\
echo "⏳ Waiting for Ollama to start..."\n\
sleep 10\n\
echo "🤖 Verifying Llama 8B model availability..."\n\
if ollama list | grep -q "llama3:8b"; then\n\
    echo "✅ Llama 8B model is ready! (loaded from cache)"\n\
else\n\
    echo "⚠️  Model loading, will be available shortly..."\n\
fi\n\
echo "🌐 Starting Flask application..."\n\
echo "✨ App will be available at: http://localhost:5000"\n\
echo "🤖 Ollama API available at: http://localhost:11434"\n\
echo "🔒 Privacy-first: All processing happens locally"\n\
exec python app.py\n\
' > /app/start.sh && \
chmod +x /app/start.sh

# Expose ports
EXPOSE 5000 11434

# Health check optimized for regular users
HEALTHCHECK --interval=30s --timeout=20s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Add comprehensive labels
LABEL maintainer="Peer Lens AI Team" \
      version="1.0.0" \
      description="Complete AI-powered writing assistant with Ollama and Llama 8B" \
      target="regular-users" \
      python.version="3.12" \
      ai.model="llama3:8b" \
      features="ai-rewriting,nlp-analysis,document-processing" \
      cache.optimized="true"

# Set proper permissions and run as app user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Run the startup script
CMD ["/app/start.sh"] 