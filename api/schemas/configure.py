"""Pydantic schemas for the configure router (account-type / liability-type CRUD)."""
from pydantic import BaseModel


class AccountTypeConfigResponse(BaseModel):
    id: int
    name: str
    is_pension: bool
    in_use: bool


class LiabilityTypeConfigResponse(BaseModel):
    id: int
    name: str
    in_use: bool


class AccountTypeCreateRequest(BaseModel):
    name: str
    is_pension: bool = False


class LiabilityTypeCreateRequest(BaseModel):
    name: str
