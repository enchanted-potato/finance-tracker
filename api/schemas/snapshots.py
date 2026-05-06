"""Pydantic schemas for the snapshots router."""
from pydantic import BaseModel


class SnapshotResponse(BaseModel):
    id: int
    snapshot_date: str                # ISO date "YYYY-MM-DD"
    total_assets: float | None
    total_liabilities: float | None
    net_worth: float | None


class ImportResult(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
