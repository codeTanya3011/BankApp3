from typing import Annotated
from fastapi import APIRouter, UploadFile, Depends, Query
from datetime import date
from ..data_base import UnitOfWork, get_unit_of_work
from ..services import PlanService, ImportService
from ..schemas import MessageResponse, YearPerformanceMonthResponse, PlanPerformanceResponse


plan_router = APIRouter(prefix="/plans", tags=["Plans"])

# Створюємо псевдонім, щоб код був чистим
UOWDep = Annotated[UnitOfWork, Depends(get_unit_of_work)]


@plan_router.post("/setup-database")
async def setup_database(
    uow: UOWDep
):
    return await ImportService.import_all_data(uow)


@plan_router.post("/insert", response_model=MessageResponse)
async def insert_plans(
    file: UploadFile,
    uow: UOWDep
):
    content = await file.read()
    await PlanService.insert_plans_from_excel(content, uow)
    return MessageResponse(message="Плани успішно завантажені")


@plan_router.get("/performance", response_model=list[PlanPerformanceResponse])
async def get_plans_performance(
    uow: UOWDep,
    check_date: date = Query(..., description="Дата перевірки")
):
    return await PlanService.get_plans_performance(uow=uow, check_date=check_date)


@plan_router.get("/year_performance", response_model=list[YearPerformanceMonthResponse])
async def year_performance(
    year: int,
    uow: UOWDep
):
    return await PlanService.year_performance(year, uow)