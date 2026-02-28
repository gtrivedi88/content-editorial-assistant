"""
Gunicorn Configuration for Content Editorial Assistant
Optimized for long-running analysis requests
"""

import multiprocessing
import os

# Server socket
bind = f"{os.getenv('HOST', '0.0.0.0')}:{os.getenv('PORT', '8080')}"
backlog = 2048

# Enable preload to share heavy resources like SpaCy model
preload_app = True

# Worker processes
default_workers = min(4, max(2, multiprocessing.cpu_count()))
workers = int(os.getenv('GUNICORN_WORKERS', os.getenv('WEB_CONCURRENCY', default_workers)))
worker_class = 'gevent'
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50

# Timeout configuration
timeout = int(os.getenv('GUNICORN_TIMEOUT', '300')) # 5-minute timeout
graceful_timeout = 30
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = os.getenv('LOG_LEVEL', 'info').lower()

# Server hooks for verification
def when_ready(server):
    """Called just after the server is started."""
    server.log.info(f"Gunicorn is ready. Listening at: {bind}")
    server.log.info(f"Using {workers} worker(s) of type '{worker_class}' with {timeout}s timeout")