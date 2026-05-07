from pydantic import BaseModel


class MetricCards(BaseModel):
    net_worth: float | None
    assets: float | None
    liabilities: float | None
    net_worth_delta: float | None


class TrendPoint(BaseModel):
    date: str
    net_worth: float | None
    assets: float | None
    liabilities: float | None


class AllocationSlice(BaseModel):
    name: str
    value: float


class PensionBar(BaseModel):
    name: str
    value: float


class DashboardResponse(BaseModel):
    cards: MetricCards
    trend: list[TrendPoint]
    allocation: list[AllocationSlice]
    pension: list[PensionBar]
