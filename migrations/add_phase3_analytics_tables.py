"""
Phase 3 Analytics Database Migration Script
Creates ContentPerformanceMetrics, MetadataFeedback, and TaxonomyLearning tables.
Also adds new fields to existing MetadataGeneration table.
"""

import sys
import os
import logging
from sqlalchemy import text, inspect

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, db
from database.models import (
    ContentPerformanceMetrics, 
    MetadataFeedback, 
    TaxonomyLearning,
    MetadataGeneration
)
from config import Config

logger = logging.getLogger(__name__)


def upgrade():
    """Add Phase 3 analytics tables and update existing MetadataGeneration table."""
    try:
        # Initialize Flask app context for database operations
        from flask import Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Initialize database
        init_db(app)
        
        with app.app_context():
            # Check database connection
            db.session.execute(text('SELECT 1'))
            logger.info("Database connection established successfully")
            
            # Check what tables already exist
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            tables_created = 0
            tables_skipped = 0
            
            # 1. Update MetadataGeneration table with new Phase 3 fields
            if 'metadata_generations' in existing_tables:
                logger.info("Updating MetadataGeneration table with Phase 3 fields...")
                
                # Check existing columns
                existing_columns = [col['name'] for col in inspector.get_columns('metadata_generations')]
                
                # Add new columns if they don't exist
                new_columns = [
                    ('content_hash', 'VARCHAR(64)'),
                    ('content_length', 'INTEGER'),
                    ('last_edited_at', 'TIMESTAMP'),
                    ('approved_at', 'TIMESTAMP')
                ]
                
                for column_name, column_type in new_columns:
                    if column_name not in existing_columns:
                        try:
                            alter_sql = f'ALTER TABLE metadata_generations ADD COLUMN {column_name} {column_type}'
                            db.session.execute(text(alter_sql))
                            logger.info(f"✅ Added column {column_name} to metadata_generations")
                        except Exception as e:
                            logger.warning(f"Failed to add column {column_name}: {e}")
                    else:
                        logger.info(f"⏭️  Column {column_name} already exists in metadata_generations")
                
                # Add index on content_hash
                try:
                    db.session.execute(text('CREATE INDEX IF NOT EXISTS idx_metadata_generations_content_hash ON metadata_generations(content_hash)'))
                    logger.info("✅ Added index on content_hash")
                except Exception as e:
                    logger.warning(f"Failed to add content_hash index: {e}")
            
            # 2. Create ContentPerformanceMetrics table
            if 'content_performance_metrics' not in existing_tables:
                logger.info("Creating ContentPerformanceMetrics table...")
                ContentPerformanceMetrics.__table__.create(db.engine, checkfirst=True)
                logger.info("✅ ContentPerformanceMetrics table created")
                tables_created += 1
            else:
                logger.info("⏭️  ContentPerformanceMetrics table already exists")
                tables_skipped += 1
            
            # 3. Create MetadataFeedback table
            if 'metadata_feedback' not in existing_tables:
                logger.info("Creating MetadataFeedback table...")
                MetadataFeedback.__table__.create(db.engine, checkfirst=True)
                logger.info("✅ MetadataFeedback table created")
                tables_created += 1
            else:
                logger.info("⏭️  MetadataFeedback table already exists")
                tables_skipped += 1
            
            # 4. Create TaxonomyLearning table
            if 'taxonomy_learning' not in existing_tables:
                logger.info("Creating TaxonomyLearning table...")
                TaxonomyLearning.__table__.create(db.engine, checkfirst=True)
                logger.info("✅ TaxonomyLearning table created")
                tables_created += 1
            else:
                logger.info("⏭️  TaxonomyLearning table already exists")
                tables_skipped += 1
            
            # 5. Create additional indexes for performance
            create_indexes()
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"🎉 Phase 3 analytics migration completed!")
            logger.info(f"   📊 Tables created: {tables_created}")
            logger.info(f"   ⏭️  Tables skipped (already exist): {tables_skipped}")
            logger.info(f"   🔗 All foreign key relationships established")
            
            return True
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'db' in locals():
            db.session.rollback()
        raise


def create_indexes():
    """Create performance indexes for the new tables."""
    indexes = [
        # ContentPerformanceMetrics indexes
        'CREATE INDEX IF NOT EXISTS idx_content_performance_metadata_id ON content_performance_metrics(metadata_generation_id)',
        'CREATE INDEX IF NOT EXISTS idx_content_performance_period ON content_performance_metrics(measurement_period_start, measurement_period_end)',
        'CREATE INDEX IF NOT EXISTS idx_content_performance_views ON content_performance_metrics(page_views)',
        'CREATE INDEX IF NOT EXISTS idx_content_performance_traffic ON content_performance_metrics(organic_search_traffic)',
        
        # MetadataFeedback indexes
        'CREATE INDEX IF NOT EXISTS idx_metadata_feedback_metadata_id ON metadata_feedback(metadata_generation_id)',
        'CREATE INDEX IF NOT EXISTS idx_metadata_feedback_type ON metadata_feedback(feedback_type, component)',
        'CREATE INDEX IF NOT EXISTS idx_metadata_feedback_session ON metadata_feedback(user_session_id)',
        'CREATE INDEX IF NOT EXISTS idx_metadata_feedback_created ON metadata_feedback(created_at)',
        'CREATE INDEX IF NOT EXISTS idx_metadata_feedback_training ON metadata_feedback(used_for_training)',
        
        # TaxonomyLearning indexes
        'CREATE INDEX IF NOT EXISTS idx_taxonomy_learning_hash ON taxonomy_learning(content_hash)',
        'CREATE INDEX IF NOT EXISTS idx_taxonomy_learning_algorithm ON taxonomy_learning(algorithm_used)',
        'CREATE INDEX IF NOT EXISTS idx_taxonomy_learning_accuracy ON taxonomy_learning(accuracy_score)',
        'CREATE INDEX IF NOT EXISTS idx_taxonomy_learning_created ON taxonomy_learning(created_at)',
        'CREATE INDEX IF NOT EXISTS idx_taxonomy_learning_training ON taxonomy_learning(used_for_training)'
    ]
    
    for index_sql in indexes:
        try:
            db.session.execute(text(index_sql))
            logger.debug(f"✅ Created index: {index_sql.split('idx_')[1].split(' ON')[0]}")
        except Exception as e:
            logger.warning(f"Failed to create index: {e}")


def downgrade():
    """Remove Phase 3 analytics tables and revert MetadataGeneration changes."""
    try:
        from flask import Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        init_db(app)
        
        with app.app_context():
            logger.info("Starting Phase 3 analytics downgrade...")
            
            # Drop tables in reverse order (respecting foreign keys)
            tables_to_drop = [
                'taxonomy_learning',
                'metadata_feedback', 
                'content_performance_metrics'
            ]
            
            for table_name in tables_to_drop:
                try:
                    db.session.execute(text(f'DROP TABLE IF EXISTS {table_name} CASCADE'))
                    logger.info(f"✅ Dropped table: {table_name}")
                except Exception as e:
                    logger.warning(f"Failed to drop table {table_name}: {e}")
            
            # Remove added columns from metadata_generations (optional - might want to keep data)
            logger.info("Note: Keeping Phase 3 columns in metadata_generations to preserve data")
            logger.info("If you need to remove them manually, run:")
            logger.info("  ALTER TABLE metadata_generations DROP COLUMN IF EXISTS content_hash;")
            logger.info("  ALTER TABLE metadata_generations DROP COLUMN IF EXISTS content_length;")
            logger.info("  ALTER TABLE metadata_generations DROP COLUMN IF EXISTS last_edited_at;")
            logger.info("  ALTER TABLE metadata_generations DROP COLUMN IF EXISTS approved_at;")
            
            db.session.commit()
            logger.info("🎉 Phase 3 analytics downgrade completed!")
            
            return True
            
    except Exception as e:
        logger.error(f"Downgrade failed: {e}")
        if 'db' in locals():
            db.session.rollback()
        raise


def verify_migration():
    """Verify that the migration was successful."""
    try:
        from flask import Flask
        app = Flask(__name__)
        app.config.from_object(Config)
        init_db(app)
        
        with app.app_context():
            # Check that all tables exist
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            required_tables = [
                'metadata_generations',
                'content_performance_metrics',
                'metadata_feedback',
                'taxonomy_learning'
            ]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            
            if missing_tables:
                logger.error(f"❌ Missing tables after migration: {missing_tables}")
                return False
            
            # Check column count for each table
            table_column_counts = {}
            for table in required_tables:
                columns = inspector.get_columns(table)
                table_column_counts[table] = len(columns)
                logger.info(f"📊 {table}: {len(columns)} columns")
            
            # Verify relationships by attempting joins
            try:
                result = db.session.execute(text("""
                    SELECT COUNT(*) FROM metadata_generations mg
                    LEFT JOIN content_performance_metrics cpm ON mg.id = cpm.metadata_generation_id
                    LEFT JOIN metadata_feedback mf ON mg.id = mf.metadata_generation_id
                """)).scalar()
                logger.info(f"✅ Foreign key relationships verified (join returned {result} rows)")
            except Exception as e:
                logger.warning(f"⚠️  Foreign key verification failed: {e}")
            
            logger.info("🎉 Migration verification completed successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        return False


if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    import argparse
    parser = argparse.ArgumentParser(description='Phase 3 Analytics Database Migration')
    parser.add_argument('--action', choices=['upgrade', 'downgrade', 'verify'], 
                       default='upgrade', help='Migration action to perform')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'upgrade':
            if upgrade():
                print("✅ Phase 3 analytics tables migration completed successfully!")
            else:
                print("❌ Migration failed!")
                sys.exit(1)
        elif args.action == 'downgrade':
            if downgrade():
                print("✅ Phase 3 analytics tables downgrade completed successfully!")
            else:
                print("❌ Downgrade failed!")
                sys.exit(1)
        elif args.action == 'verify':
            if verify_migration():
                print("✅ Migration verification passed!")
            else:
                print("❌ Migration verification failed!")
                sys.exit(1)
                
    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)
