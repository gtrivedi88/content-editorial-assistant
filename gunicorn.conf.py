"""Gunicorn configuration for Content Editorial Assistant.

Optimized for long-running analysis requests with gevent workers.
"""

import multiprocessing
import os

# Server socket
bind: str = "%s:%s" % (os.getenv('HOST', '0.0.0.0'), os.getenv('PORT', '8080'))
backlog: int = 2048

# Enable preload to share heavy resources like SpaCy model
preload_app: bool = True

# Worker processes
default_workers: int = min(4, max(2, multiprocessing.cpu_count()))
workers: int = int(os.getenv('GUNICORN_WORKERS', os.getenv('WEB_CONCURRENCY', str(default_workers))))
worker_class: str = 'gevent'
worker_connections: int = 1000
max_requests: int = 1000
max_requests_jitter: int = 50

# Timeout configuration
timeout: int = int(os.getenv('GUNICORN_TIMEOUT', '300'))  # 5-minute timeout
graceful_timeout: int = 30
keepalive: int = 5

# Logging
accesslog: str = '-'
errorlog: str = '-'
loglevel: str = os.getenv('LOG_LEVEL', 'info').lower()


def when_ready(server: object) -> None:
    """Log server readiness with bind address and worker configuration.

    Args:
        server: The Gunicorn server instance.
    """
    server.log.info("Gunicorn is ready. Listening at: %s", bind)
    server.log.info(
        "Using %s worker(s) of type '%s' with %ss timeout",
        workers, worker_class, timeout,
    )


def post_worker_init(worker: object) -> None:
    """Eagerly initialize singletons after fork for warm first requests.

    Runs in each worker process after ``fork()``, avoiding fork-safety
    issues with ``threading.Lock`` and mutable state.  SpaCy's model
    data is ``mmap``-based and safely shared from ``preload_app``.

    Args:
        worker: The Gunicorn worker instance.
    """
    from app.extensions import get_nlp
    from app.services.session.store import get_session_store

    get_nlp()
    get_session_store()

    try:
        from rules import term_registry  # noqa: F401 — triggers module-level load
        worker.log.info("Worker %s: singletons initialized", worker.pid)
    except ImportError:
        worker.log.info("Worker %s: core singletons initialized", worker.pid)
