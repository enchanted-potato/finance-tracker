"""Migration: add entry_date column to accounts table.

Run once against the live database. Safe to re-run (IF NOT EXISTS).
"""
from sqlalchemy import text
from app.database import engine


def main():
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM accounts"))
        conn.execute(text("DELETE FROM snapshots"))
        conn.execute(text("DELETE FROM liability_entries"))
        conn.execute(text("""
            ALTER TABLE accounts
            ADD COLUMN IF NOT EXISTS entry_date DATE NOT NULL DEFAULT CURRENT_DATE
        """))
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS ix_accounts_user_name_entry_date
            ON accounts(user_id, name, entry_date)
        """))
        conn.commit()
    print("Migration complete: all accounts deleted, entry_date added.")


if __name__ == "__main__":
    main()
