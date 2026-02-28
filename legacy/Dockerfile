FROM python:3.12-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ libffi-dev libssl-dev libxml2-dev libxslt1-dev \
    zlib1g-dev libjpeg-dev libpng-dev git curl ruby ruby-dev \
    && gem install asciidoctor \
    && rm -rf /var/lib/apt/lists/* && apt-get clean

RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY requirements.txt .

ENV NLTK_DATA=/app/.cache/nltk_data

RUN mkdir -p /app/.cache/nltk_data /app/uploads /app/logs /app/instance /app/temp /app/feedback_data \
    /nltk_data && chmod -R 777 /nltk_data \
    && pip install --no-cache-dir -r requirements.txt \
    && python -m spacy validate \
    && python -c "import nltk; \
        nltk.download('punkt', download_dir='/app/.cache/nltk_data', quiet=True); \
        nltk.download('stopwords', download_dir='/app/.cache/nltk_data', quiet=True); \
        nltk.download('cmudict', download_dir='/app/.cache/nltk_data', quiet=True)" \
    && cp -r /app/.cache/nltk_data/* /nltk_data/ \
    && chown -R appuser:0 /app /nltk_data \
    && chmod -R g+w /app /nltk_data

COPY --chown=appuser:appuser main.py config.py gunicorn.conf.py main.sh ./

RUN chmod +x main.sh

COPY --chown=appuser:appuser app_modules/ ./app_modules/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser database/ ./database/
COPY --chown=appuser:appuser rule_enhancements/ ./rule_enhancements/
COPY --chown=appuser:appuser models/ ./models/
COPY --chown=appuser:appuser rewriter/ ./rewriter/
COPY --chown=appuser:appuser rules/ ./rules/
COPY --chown=appuser:appuser scripts/ ./scripts/
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser structural_parsing/ ./structural_parsing/
COPY --chown=appuser:appuser style_analyzer/ ./style_analyzer/
COPY --chown=appuser:appuser style_guides/ ./style_guides/
COPY --chown=appuser:appuser ui/ ./ui/
COPY --chown=appuser:appuser validation/ ./validation/
COPY --chown=appuser:appuser llamastack/ ./llamastack/
COPY --chown=appuser:appuser pdf_reports/ ./pdf_reports/

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 FLASK_APP=main.py \
    FLASK_ENV=production FLASK_DEBUG=false PORT=8080 HOST=0.0.0.0 ENVIRONMENT=production

EXPOSE 8080
USER appuser

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["./main.sh"]
