from sqlmodel import SQLModel

from app.database import engine
from app.models import (  # noqa: F401
    Account,
    AccountType,
    Liability,
    LiabilityType,
    Snapshot,
    User,
)


def create_tables() -> None:
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
