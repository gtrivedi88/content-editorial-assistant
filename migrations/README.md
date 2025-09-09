# Database Migrations

This directory contains database migration and initialization scripts.

## First-Time Setup

To initialize the database for the first time:

```bash
# Initialize database with tables and default rules
python when it

## Testing the Database

Run the comprehensive database tests:

```bash
# Run all database tests
pytest tests/database/ -v

# Run specific test
pytest tests/database/test_database_integration.py::test_session_creation -v

# Run tests with coverage
pytest tests/database/ --cov=database --cov-report=html
```

## Database Management

```bash
# Drop all tables (DANGEROUS!)
python migrations/init_database.py drop

# Reinitialize after dropping
python migrations/init_database.py init
```

## Environment Variables

Make sure these are set in your `.env` file:

```env
# For development (SQLite)
DATABASE_URL=sqlite:///style_guide_ai.db

# For production (PostgreSQL)
# DATABASE_URL=postgresql://username:password@localhost:5432/style_guide_ai

FLASK_APP=app.py
FLASK_ENV=development
```

## Production Setup

For production with PostgreSQL:

1. Install PostgreSQL
2. Create database and user
3. Set DATABASE_URL environment variable
4. Run initialization script

```bash
# Example PostgreSQL setup
sudo -u postgres psql
CREATE DATABASE style_guide_ai;
CREATE USER style_guide_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE style_guide_ai TO style_guide_user;
\q

# Set environment variable
export DATABASE_URL=postgresql://style_guide_user:secure_password@localhost:5432/style_guide_ai

# Initialize database
python migrations/init_database.py init
```
