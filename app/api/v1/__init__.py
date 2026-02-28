"""API v1 blueprint — aggregates all v1 resource routes.

Route modules are imported here so that their ``@bp.route`` decorators
execute against the shared blueprint instance.
"""

from flask import Blueprint

bp = Blueprint("v1", __name__)

# Import route modules so their @bp.route decorators register
from app.api.v1 import analysis  # noqa: F401
from app.api.v1 import upload  # noqa: F401
from app.api.v1 import issues  # noqa: F401
from app.api.v1 import suggestions  # noqa: F401
from app.api.v1 import citations  # noqa: F401
from app.api.v1 import report  # noqa: F401
from app.api.v1 import health  # noqa: F401
