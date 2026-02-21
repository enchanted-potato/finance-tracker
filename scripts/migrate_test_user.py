#!/usr/bin/env python
"""Migrate test-user data to real Firebase UID.

This script migrates all data from the hardcoded 'test-user' (used during Phase 3
development) to a real Firebase UID. Run this once after first login in Phase 5
deployment.

Usage:
    python scripts/migrate_test_user.py <firebase_uid>
    python scripts/migrate_test_user.py <firebase_uid> --dry-run

Example:
    python scripts/migrate_test_user.py abc123xyz456 --dry-run
    python scripts/migrate_test_user.py abc123xyz456
"""

import argparse
import sys

from loguru import logger
from sqlmodel import Session, text

from app.database import engine


def migrate_test_user(target_uid: str, dry_run: bool = False) -> None:
    """Migrate all test-user data to target Firebase UID.

    Args:
        target_uid: Firebase UID to migrate data to
        dry_run: If True, print SQL without executing

    Raises:
        Exception: If migration fails
    """
    # SQL statements to migrate data
    statements = [
        (
            "account_types",
            "UPDATE account_types SET user_id = :new_uid WHERE user_id = 'test-user'",
        ),
        ("accounts", "UPDATE accounts SET user_id = :new_uid WHERE user_id = 'test-user'"),
        (
            "liabilities",
            "UPDATE liabilities SET user_id = :new_uid WHERE user_id = 'test-user'",
        ),
        ("snapshots", "UPDATE snapshots SET user_id = :new_uid WHERE user_id = 'test-user'"),
        ("users", "DELETE FROM users WHERE id = 'test-user'"),
    ]

    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        logger.info(f"Target UID: {target_uid}")
        logger.info("SQL statements that would be executed:")
        for table, sql in statements:
            logger.info(f"  {table}: {sql}")
        return

    # Confirmation prompt
    print(f"\nThis will migrate all data from 'test-user' to '{target_uid}'.")
    print("This operation cannot be undone.")
    response = input("Continue? [y/N]: ").strip().lower()

    if response != "y":
        logger.info("Migration cancelled by user")
        sys.exit(0)

    # Execute migration in a transaction
    logger.info(f"Starting migration from 'test-user' to '{target_uid}'")

    with Session(engine) as session:
        try:
            rows_affected = {}

            for table, sql in statements:
                result = session.exec(text(sql), params={"new_uid": target_uid})
                rows_affected[table] = result.rowcount
                logger.info(f"  {table}: {rows_affected[table]} rows affected")

            session.commit()
            logger.success("Migration completed successfully")

            # Print summary
            print("\nMigration Summary:")
            for table, count in rows_affected.items():
                print(f"  {table}: {count} rows")

        except Exception as e:
            session.rollback()
            logger.error(f"Migration failed: {e}")
            raise


def main() -> None:
    """Parse arguments and run migration."""
    parser = argparse.ArgumentParser(
        description="Migrate test-user data to real Firebase UID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "uid",
        type=str,
        help="Firebase UID to migrate data to",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL without executing",
    )

    args = parser.parse_args()

    migrate_test_user(args.uid, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
