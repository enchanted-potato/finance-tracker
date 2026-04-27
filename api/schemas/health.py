"""Health response schema."""
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response schema for the health endpoint.

    :param status: Service status string (e.g. "ok").
    """

    status: str
