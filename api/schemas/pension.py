"""Pydantic schemas for the pension router."""
from datetime import date

from pydantic import BaseModel


class PensionTypeResponse(BaseModel):
    id: int
    name: str
    is_pension: bool


class PensionEntryRequest(BaseModel):
    account_type_id: int
    entry_date: date
    balance: float
    currency: str = "GBP"
    exchange_rate: float = 1.0


class PensionEntryResponse(BaseModel):
    id: int
    account_type_id: int
    entry_date: date
    balance: float
    currency: str


class PensionHistoryItemResponse(BaseModel):
    entry_id: int
    type_id: int
    type_name: str
    balance: float


class PensionHistoryDayResponse(BaseModel):
    date: str
    total: float
    entries: list[PensionHistoryItemResponse]
