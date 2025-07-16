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
        result = conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table';")
        )
        tables = [row[0] for row in result.fetchall()]
        print(f"Created tables: {tables}")

        # Check for all required tables
        required_tables = [
            "players",
            "tasks",
            "game_sessions",
            "player_game_links",
            "vote_history",
            "discussion_logs",
            "task_logs",
            "join_queue",
        ]

        missing_tables = []
        for table in required_tables:
            if table in tables:
                print(f"✅ {table} table created successfully")
            else:
                print(f"❌ {table} table not found!")
                missing_tables.append(table)

        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            exit(1)

    print("Database initialization complete!")
