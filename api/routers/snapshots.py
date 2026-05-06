"""Snapshots router — history list, CSV export, CSV import, delete."""
import csv
import io
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.database import get_session
from app.services import snapshot_service
from api.dependencies import get_current_user
from api.schemas.snapshots import ImportResult, SnapshotResponse

router = APIRouter(prefix="/api/snapshots", tags=["snapshots"])


@router.get("", response_model=list[SnapshotResponse])
def list_snapshots(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> list[SnapshotResponse]:
    """Return snapshot history ascending by date."""
    snapshots = snapshot_service.get_snapshot_history(session=session, user_id=user_id)
    return [
        SnapshotResponse(
            id=s.id,
            snapshot_date=s.snapshot_date.date().isoformat(),
            total_assets=float(s.total_assets) if s.total_assets is not None else None,
            total_liabilities=float(s.total_liabilities) if s.total_liabilities is not None else None,
            net_worth=float(s.net_worth) if s.net_worth is not None else None,
        )
        for s in snapshots
    ]


@router.get("/export.csv")
def export_snapshots_csv(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> StreamingResponse:
    """Stream all snapshots as a downloadable CSV file."""
    snapshots = snapshot_service.get_snapshot_history(session=session, user_id=user_id)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "total_assets", "total_liabilities", "net_worth"])
    for s in snapshots:
        writer.writerow([
            s.snapshot_date.date().isoformat(),
            float(s.total_assets) if s.total_assets is not None else "",
            float(s.total_liabilities) if s.total_liabilities is not None else "",
            float(s.net_worth) if s.net_worth is not None else "",
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=snapshots.csv"},
    )


@router.post("/import", response_model=ImportResult)
async def import_snapshots_csv(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> ImportResult:
    """Import snapshots from a multipart-uploaded CSV file."""
    raw = await file.read()
    try:
        file_content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File is not valid utf-8: {exc}",
        ) from exc

    imported, skipped, errors = snapshot_service.import_csv_snapshots(
        session=session, user_id=user_id, file_content=file_content
    )
    return ImportResult(imported=imported, skipped=skipped, errors=errors)


@router.delete("/{snapshot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_snapshot_endpoint(
    snapshot_id: int,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[str, Depends(get_current_user)],
) -> None:
    """Hard-delete a snapshot the caller owns."""
    try:
        snapshot_service.delete_snapshot(session=session, snapshot_id=snapshot_id, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
