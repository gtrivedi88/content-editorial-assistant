# Style Guide AI - Lightweight Version
# AI-powered writing assistant without embedded Ollama (users can connect external Ollama instances)
# Optimized for fast deployment and reduced image size

FROM python:3.12

# Set environment variables for optimal performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
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
    ruby-full \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Ruby gems (cached unless gem versions change)
RUN gem install asciidoctor --no-document && \
    echo "✅ Asciidoctor gem installed successfully" && \
    asciidoctor --version

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

# Create necessary directories with proper permissions
RUN mkdir -p uploads instance templates static logs && \
    chmod 755 uploads instance logs

# Copy application code LAST (changes here won't invalidate dependency cache)
COPY . .

# Create optimized startup script
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🚀 Starting Style Guide AI Writing Assistant..."\n\
echo "🌐 Starting Flask application..."\n\
echo "✨ App will be available at: http://localhost:5000"\n\
echo "🔒 Privacy-first: All processing happens locally"\n\
echo "💡 To use AI features, connect to your external Ollama instance or API provider"\n\
exec python app.py\n\
' > /app/start.sh && \
chmod +x /app/start.sh

# Expose Flask port
EXPOSE 5000

# Health check optimized for lightweight deployment
HEALTHCHECK --interval=30s --timeout=20s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Add comprehensive labels
LABEL maintainer="Style Guide AI Team" \
      version="2.0.0" \
      description="Lightweight AI-powered writing assistant (connect external Ollama/APIs)" \
      target="lightweight-deployment" \
      python.version="3.12" \
      features="nlp-analysis,document-processing,external-ai-support" \
      cache.optimized="true"

# Set proper permissions and run as app user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Run the startup script
CMD ["/app/start.sh"] 