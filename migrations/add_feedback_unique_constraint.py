"""
Add unique constraint to UserFeedback table for (session_id, violation_id)
This migration adds a unique constraint to prevent duplicate feedback entries.
"""

import logging
from sqlalchemy import text
from database import db
from database.models import UserFeedback

logger = logging.getLogger(__name__)


def upgrade():
    """Add unique constraint to feedback table."""
    try:
        # Check if constraint already exists
        constraint_check = text("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'feedback' 
            AND constraint_name = 'unique_session_violation_feedback'
            AND constraint_type = 'UNIQUE'
        """)
        
        result = db.session.execute(constraint_check)
        existing_constraint = result.fetchone()
        
        if existing_constraint:
            logger.info("Unique constraint already exists, skipping...")
            return True
        
        # Remove duplicate records before adding constraint
        logger.info("Removing duplicate feedback entries...")
        
        # Keep the most recent feedback for each session_id + violation_id combination
        remove_duplicates = text("""
            DELETE FROM feedback 
            WHERE id NOT IN (
                SELECT DISTINCT ON (session_id, violation_id) id
                FROM feedback 
                ORDER BY session_id, violation_id, timestamp DESC
            )
        """)
        
        result = db.session.execute(remove_duplicates)
        deleted_count = result.rowcount
        
        if deleted_count > 0:
            logger.info(f"Removed {deleted_count} duplicate feedback entries")
        
        # Add the unique constraint
        logger.info("Adding unique constraint...")
        add_constraint = text("""
            ALTER TABLE feedback 
            ADD CONSTRAINT unique_session_violation_feedback 
            UNIQUE (session_id, violation_id)
        """)
        
        db.session.execute(add_constraint)
        db.session.commit()
        
        logger.info("Successfully added unique constraint to feedback table")
        return True
        
    except Exception as e:
        logger.error(f"Failed to add unique constraint: {e}")
        db.session.rollback()
        return False


def downgrade():
    """Remove unique constraint from feedback table."""
    try:
        logger.info("Removing unique constraint...")
        remove_constraint = text("""
            ALTER TABLE feedback 
            DROP CONSTRAINT IF EXISTS unique_session_violation_feedback
        """)
        
        db.session.execute(remove_constraint)
        db.session.commit()
        
        logger.info("Successfully removed unique constraint from feedback table")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove unique constraint: {e}")
        db.session.rollback()
        return False


if __name__ == '__main__':
    """Run migration directly."""
    print("Running feedback unique constraint migration...")
    success = upgrade()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
