#!/usr/bin/env python3
"""
Database initialization script for CI/CD pipeline.
Creates all necessary database tables before running tests.
"""

import os
from sqlalchemy import text
from bot.database import init_db, SessionLocal, engine

if __name__ == "__main__":
    print("Initializing database...")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')}")
    
    # Create all tables
    init_db()
    
    # Verify tables were created
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result.fetchall()]
        print(f"Created tables: {tables}")
        
        # Check specifically for players table
        if 'players' in tables:
            print("✅ players table created successfully")
        else:
            print("❌ players table not found!")
            exit(1)
    
    print("Database initialization complete!")
