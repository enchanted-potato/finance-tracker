from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Index, UniqueConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class AccountType(SQLModel, table=True):
    """Predefined or user-custom account categories."""

    __tablename__ = "account_types"
    __table_args__ = (UniqueConstraint("name", "user_id"), {"extend_existing": True})

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    user_id: str | None = Field(default=None, max_length=128)


class Account(SQLModel, table=True):
    """User asset account with current balance."""

    __tablename__ = "accounts"
    __table_args__ = (Index("ix_accounts_user_active", "user_id", "is_active"), {"extend_existing": True})

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=128)
    account_type_id: int = Field(foreign_key="account_types.id")
    name: str = Field(max_length=255)
    balance: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    currency: str = Field(default="GBP", max_length=3)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": sa_text("now()")},
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": sa_text("now()"),
            "onupdate": sa_text("now()"),
        },
    )


class LiabilityType(SQLModel, table=True):
    """Predefined or user-custom liability categories."""

    __tablename__ = "liability_types"
    __table_args__ = (UniqueConstraint("name", "user_id"), {"extend_existing": True})

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    user_id: str | None = Field(default=None, max_length=128)


class Liability(SQLModel, table=True):
    """User liability with current outstanding balance."""

    __tablename__ = "liabilities"
    __table_args__ = (Index("ix_liabilities_user_active", "user_id", "is_active"), {"extend_existing": True})

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=128)
    liability_type_id: int = Field(foreign_key="liability_types.id")
    name: str = Field(max_length=255)
    balance: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    currency: str = Field(default="GBP", max_length=3)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": sa_text("now()")},
    )
    updated_at: datetime = Field(
        default=None,
        sa_column_kwargs={
            "server_default": sa_text("now()"),
            "onupdate": sa_text("now()"),
        },
    )


class Snapshot(SQLModel, table=True):
    """Point-in-time record of net worth."""

    __tablename__ = "snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "snapshot_date"),
        Index("ix_snapshots_user_date", "user_id", "snapshot_date"),
        {"extend_existing": True},
    )

    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(max_length=128)
    total_assets: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    total_liabilities: Decimal = Field(
        default=Decimal("0"), max_digits=14, decimal_places=2
    )
    net_worth: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)
    snapshot_date: datetime = Field()
    detail_json: dict | None = Field(default=None, sa_column=Column(JSONB))
    created_at: datetime = Field(
        default=None,
        sa_column_kwargs={"server_default": sa_text("now()")},
    )
