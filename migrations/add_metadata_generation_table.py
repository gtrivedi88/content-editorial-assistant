"""
Add MetadataGeneration table for AI-powered metadata extraction
This migration adds the metadata_generations table and related indexes.
"""

import os
import sys
import logging

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database import db
from database.models import MetadataGeneration

logger = logging.getLogger(__name__)


def upgrade():
    """Create MetadataGeneration table and indexes."""
    try:
        # Check if table already exists using SQLAlchemy inspector
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        if 'metadata_generations' in existing_tables:
            logger.info("MetadataGeneration table already exists, skipping...")
            return True
        
        # Create the table using SQLAlchemy model
        logger.info("Creating metadata_generations table...")
        
        # Use SQLAlchemy's create_all to create just the MetadataGeneration table
        MetadataGeneration.__table__.create(db.engine, checkfirst=True)
        
        logger.info("MetadataGeneration table created with all indexes and constraints")
        
        logger.info("Successfully created MetadataGeneration table and indexes")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create MetadataGeneration table: {e}")
        db.session.rollback()
        return False


def downgrade():
    """Remove MetadataGeneration table."""
    try:
        logger.info("Dropping metadata_generations table...")
        drop_table = text("DROP TABLE IF EXISTS metadata_generations")
        
        db.session.execute(drop_table)
        db.session.commit()
        
        logger.info("Successfully dropped MetadataGeneration table")
        return True
        
    except Exception as e:
        logger.error(f"Failed to drop MetadataGeneration table: {e}")
        db.session.rollback()
        return False


if __name__ == '__main__':
    """Run migration directly."""
    import os
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from flask import Flask
    from database import init_db
    from config import Config
    
    # Create Flask app for migration
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    
    with app.app_context():
        print("Running MetadataGeneration table migration...")
        success = upgrade()
        if success:
            print("✅ Migration completed successfully")
        else:
            print("❌ Migration failed")
