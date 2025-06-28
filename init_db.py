#!/usr/bin/env python3
"""
Database initialization script for CI/CD pipeline.
Creates all necessary database tables before running tests.
"""

from bot.database import init_db

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete!")
