"""Import historical liabilities from liabilities.csv into liability_entries table.

Usage:
    python scripts/import_liabilities_csv.py <user_id>
    python scripts/import_liabilities_csv.py <user_id> --dry-run
"""
import argparse
import csv
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import text
from sqlmodel import Session

from app.database import engine

CSV_PATH = Path(__file__).parent.parent / "liabilities.csv"
COLUMNS = {
    "Undergraduate Loan": "Undergraduate Loan",
    "Postgraduate Loan": "Postgraduate Loan",
}


def parse_amount(value: str) -> Decimal | None:
    """Parse £1,234.56 or -£1,234.56 into Decimal. Returns None if empty."""
    value = value.strip()
    if not value:
        return None
    negative = value.startswith("-")
    cleaned = value.replace("-", "").replace("£", "").replace(",", "").strip()
    if not cleaned:
        return None
    amount = Decimal(cleaned)
    return -amount if negative else amount


def parse_date(value: str) -> date:
    """Parse dd/mm/yy into date."""
    from datetime import datetime
    return datetime.strptime(value.strip(), "%d/%m/%y").date()


def main(user_id: str, dry_run: bool = False) -> None:
    with Session(engine) as session:
        # Look up liability_type IDs (COLUMNS maps csv_col -> db_name)
        type_ids: dict[str, int] = {}
        for csv_col, db_name in COLUMNS.items():
            row = session.exec(
                text("SELECT id FROM liability_types WHERE name = :name"),
                params={"name": db_name},
            ).first()
            if row is None:
                print(f"ERROR: liability_type '{db_name}' not found in DB")
                sys.exit(1)
            type_ids[csv_col] = row[0]
            print(f"Found '{db_name}' -> id={row[0]}")

        rows_to_insert = []
        with open(CSV_PATH, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entry_date = parse_date(row["Date"])
                for col in COLUMNS:
                    amount = parse_amount(row.get(col, ""))
                    if amount is None:
                        continue
                    rows_to_insert.append({
                        "user_id": user_id,
                        "liability_type_id": type_ids[col],
                        "entry_date": entry_date,
                        "amount": amount,
                    })

        print(f"\n{len(rows_to_insert)} entries to insert")
        for r in rows_to_insert:
            print(f"  {r['entry_date']}  {r['liability_type_id']}  £{r['amount']}")

        if dry_run:
            print("\nDRY RUN — no changes made.")
            return

        inserted = 0
        for r in rows_to_insert:
            session.exec(
                text("""
                    INSERT INTO liability_entries (user_id, liability_type_id, entry_date, amount, currency)
                    VALUES (:user_id, :liability_type_id, :entry_date, :amount, 'GBP')
                    ON CONFLICT (user_id, entry_date, liability_type_id) DO NOTHING
                """),
                params=r,
            )
            inserted += 1

        session.commit()
        print(f"\nDone — {inserted} entries inserted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import liabilities.csv into liability_entries")
    parser.add_argument("user_id", help="Firebase UID")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    main(args.user_id, dry_run=args.dry_run)
