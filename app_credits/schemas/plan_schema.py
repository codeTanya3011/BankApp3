from datetime import date
from typing import Optional
from decimal import Decimal
from pydantic import BaseModel
from pydantic import ConfigDict


class MessageResponse(BaseModel):
    message: str


class PlanBase(BaseModel):
    period: date
    amount: int


class PlanCreate(PlanBase):
    category_id: int


class PlanUpdate(BaseModel):
    period: Optional[date] = None
    amount: Optional[int] = None
    category_id: Optional[int] = None


class PlanResponse(BaseModel):
    id: int
    period: date
    amount: int
    category_id: int

    model_config = ConfigDict(from_attributes=True)


class PlanPerformanceResponse(BaseModel):
    period: date
    category: str
    plan_sum: float
    fact_sum: float
    performance_percent: float


class YearPerformanceMonthResponse(BaseModel):
    month: int
    year: int

    issued_count: int
    issued_plan_sum: float
    issued_fact_sum: float
    issued_percent: float

    payments_count: int
    payments_plan_sum: float
    payments_fact_sum: float
    payments_percent: float

    issued_part_of_year: float
    payments_part_of_year: float


class YearPerformanceResponse(BaseModel):
    year: int
    months: list[YearPerformanceMonthResponse]


class PerformanceOut(BaseModel):
    issued_count: int
    issued_sum: Decimal

    returned_count: int
    returned_sum: Decimal

    percent_accrued: Decimal
    percent_paid: Decimal