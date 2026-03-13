"""Migration: refactor accounts table to type-keyed entry model.

Drops: name, currency, exchange_rate, is_active columns.
Adds: UniqueConstraint(user_id, entry_date, account_type_id).
Drops old index ix_accounts_user_active and ix_accounts_user_name_entry_date.
Creates new index ix_accounts_user_type_date.

WARNING: This deletes any rows that would violate the new unique constraint
(duplicate type on same date for same user). Review data first.

Run once against the live database.
"""
from sqlalchemy import text

from app.database import engine


def main():
    with engine.connect() as conn:
        # Drop old indexes
        conn.execute(text("DROP INDEX IF EXISTS ix_accounts_user_active"))
        conn.execute(text("DROP INDEX IF EXISTS ix_accounts_user_name_entry_date"))

        # Drop columns that no longer exist in the model
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS name"))
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS currency"))
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS exchange_rate"))
        conn.execute(text("ALTER TABLE accounts DROP COLUMN IF EXISTS is_active"))

        # Add new unique constraint
        conn.execute(text("""
            ALTER TABLE accounts
            ADD CONSTRAINT uq_accounts_user_date_type
            UNIQUE (user_id, entry_date, account_type_id)
        """))

        # Add new index
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_accounts_user_type_date
            ON accounts(user_id, account_type_id, entry_date)
        """))

        conn.commit()
    print("Migration complete.")


if __name__ == "__main__":
    main()
