"""
Database package initialization
Handles SQLAlchemy setup and database initialization.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Import all models to ensure they're registered
    from . import models
    
    return db

def create_tables():
    """Create all tables."""
    db.create_all()

def drop_tables():
    """Drop all tables (use with caution)."""
    db.drop_all()
