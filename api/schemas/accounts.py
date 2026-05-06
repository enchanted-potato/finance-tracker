"""Pydantic schemas for the accounts router."""
from datetime import date

from pydantic import BaseModel


class AccountTypeResponse(BaseModel):
    id: int
    name: str
    is_pension: bool
    in_use: bool


class AccountEntryRequest(BaseModel):
    account_type_id: int
    entry_date: date
    balance: float
    currency: str = "GBP"
    exchange_rate: float = 1.0


class AccountEntryResponse(BaseModel):
    id: int
    account_type_id: int
    entry_date: date
    balance: float
    currency: str


class EntryItemResponse(BaseModel):
    entry_id: int
    type_id: int
    type_name: str
    balance: float


class HistoryDayResponse(BaseModel):
    date: str
    total: float
    entries: list[EntryItemResponse]
