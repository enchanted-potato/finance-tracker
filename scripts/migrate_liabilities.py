"""Migration: create liability_entries table and drop liabilities table.

Run once against the live database. Safe to re-run (IF NOT EXISTS / IF EXISTS).
"""
from sqlalchemy import text
from app.database import engine
from app.models import SQLModel


def main():
    SQLModel.metadata.create_all(engine, checkfirst=True)  # creates liability_entries
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS liabilities CASCADE"))
        conn.commit()
    print("Migration complete: liability_entries created, liabilities dropped.")


if __name__ == "__main__":
    main()
