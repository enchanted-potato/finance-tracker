"""Configure router — account-type and liability-type CRUD with safe delete (409)."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.database import get_session
from app.services import account_service, liability_service, type_service
from api.dependencies import get_current_user
from api.schemas.configure import (
    AccountTypeConfigResponse,
    AccountTypeCreateRequest,
    LiabilityTypeConfigResponse,
    LiabilityTypeCreateRequest,
)

router = APIRouter(prefix="/api/configure", tags=["configure"])


@router.get("/account-types", response_model=list[AccountTypeConfigResponse])
def list_account_types_config(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[AccountTypeConfigResponse]:
    """List account types visible to this user with an in_use flag."""
    types = account_service.list_account_types(session=session, user_id=user_id)
    return [
        AccountTypeConfigResponse(
            id=t.id,
            name=t.name,
            is_pension=t.is_pension,
            in_use=type_service.account_type_usage_count(session=session, type_id=t.id) > 0,
        )
        for t in types
    ]


@router.post("/account-types", response_model=AccountTypeConfigResponse, status_code=status.HTTP_201_CREATED)
def create_account_type_endpoint(
    body: AccountTypeCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> AccountTypeConfigResponse:
    """Create a user-owned account type."""
    at = type_service.create_account_type(
        session=session, name=body.name, user_id=user_id, is_pension=body.is_pension
    )
    return AccountTypeConfigResponse(id=at.id, name=at.name, is_pension=at.is_pension, in_use=False)


@router.delete("/account-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account_type_endpoint(
    type_id: int,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> None:
    """Delete an account type. Returns 409 Conflict if the type is in use."""
    try:
        type_service.delete_account_type(session=session, type_id=type_id)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg) from exc


@router.get("/liability-types", response_model=list[LiabilityTypeConfigResponse])
def list_liability_types_config(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[LiabilityTypeConfigResponse]:
    """List liability types visible to this user with an in_use flag."""
    types = liability_service.list_liability_types(session=session, user_id=user_id)
    return [
        LiabilityTypeConfigResponse(
            id=t.id,
            name=t.name,
            in_use=type_service.liability_type_usage_count(session=session, type_id=t.id) > 0,
        )
        for t in types
    ]


@router.post("/liability-types", response_model=LiabilityTypeConfigResponse, status_code=status.HTTP_201_CREATED)
def create_liability_type_endpoint(
    body: LiabilityTypeCreateRequest,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> LiabilityTypeConfigResponse:
    """Create a user-owned liability type."""
    lt = type_service.create_liability_type(session=session, name=body.name, user_id=user_id)
    return LiabilityTypeConfigResponse(id=lt.id, name=lt.name, in_use=False)


@router.delete("/liability-types/{type_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_liability_type_endpoint(
    type_id: int,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> None:
    """Delete a liability type. Returns 409 Conflict if the type is in use."""
    try:
        type_service.delete_liability_type(session=session, type_id=type_id)
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg) from exc
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=msg) from exc
