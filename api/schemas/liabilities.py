"""Pydantic schemas for the liabilities router."""
from datetime import date

from pydantic import BaseModel


class LiabilityTypeResponse(BaseModel):
    id: int
    name: str
    in_use: bool


class LiabilityEntryRequest(BaseModel):
    liability_type_id: int
    entry_date: date
    amount: float
    currency: str = "GBP"


class LiabilityEntryResponse(BaseModel):
    id: int
    liability_type_id: int
    entry_date: date
    amount: float
    currency: str


class LiabilityHistoryItemResponse(BaseModel):
    entry_id: int
    type_id: int
    type_name: str
    balance: float  # unified history shape per D-01 (CONTEXT.md)


class LiabilityHistoryDayResponse(BaseModel):
    date: str
    total: float
    entries: list[LiabilityHistoryItemResponse]
