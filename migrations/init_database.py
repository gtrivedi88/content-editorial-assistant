"""
Database initialization and migration script
Run this to set up the database for the first time.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from database import init_db, db
from database.models import *  # Import all models
from database.services import database_service
from config import Config

def create_app():
    """Create Flask app for migration."""
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def init_database():
    """Initialize database with all tables."""
    app = create_app()
    
    with app.app_context():
        print("🔧 Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Insert default rules
        print("🔧 Inserting default style rules...")
        rules_created = database_service.initialize_default_rules()
        print(f"✅ Created {rules_created} default style rules!")
        
        # Verify setup
        print("🔧 Verifying database setup...")
        health = database_service.get_system_health()
        if health['status'] == 'healthy':
            print("✅ Database setup verification passed!")
            print(f"   - Database connection: {health['database_connection']}")
            print(f"   - Active sessions: {health['active_sessions']}")
        else:
            print(f"❌ Database setup verification failed: {health.get('error', 'Unknown error')}")
        
        print("\n🎉 Database initialization complete!")
        print("   You can now start the application with: python app.py")

def drop_database():
    """Drop all database tables (DANGEROUS - use with caution)."""
    app = create_app()
    
    with app.app_context():
        print("⚠️  WARNING: This will delete ALL data in the database!")
        confirm = input("Type 'DELETE ALL DATA' to confirm: ")
        
        if confirm == 'DELETE ALL DATA':
            print("🗑️  Dropping all database tables...")
            db.drop_all()
            print("✅ All tables dropped successfully!")
        else:
            print("❌ Operation cancelled - database preserved.")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Database management script')
    parser.add_argument('action', choices=['init', 'drop'], 
                       help='Action to perform (init=create tables, drop=delete all data)')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        init_database()
    elif args.action == 'drop':
        drop_database()
