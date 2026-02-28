FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ libffi-dev libssl-dev libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libpng-dev git curl ruby ruby-dev \
    && gem install asciidoctor \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY requirements.txt .

RUN mkdir -p /app/data \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m spacy validate \
    && chown -R appuser:0 /app \
    && chmod -R g+w /app

COPY --chown=appuser:appuser main.py gunicorn.conf.py main.sh multishot_examples.yaml ./

RUN chmod +x main.sh

COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser rules/ ./rules/
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser static/ ./static/
COPY --chown=appuser:appuser style_guides/ ./style_guides/
COPY --chown=appuser:appuser templates/ ./templates/
COPY --chown=appuser:appuser llamastack/ ./llamastack/

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 HOST=0.0.0.0 ENVIRONMENT=production

EXPOSE 8080
USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/health || exit 1

CMD ["./main.sh"]
