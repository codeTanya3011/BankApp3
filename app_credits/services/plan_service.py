import pandas as pd
from datetime import date
from calendar import monthrange
from collections import defaultdict
from decimal import Decimal
import io
from ..data_base import UnitOfWork
from ..models import CategoryNames
from ..schemas import (
    PlanPerformanceResponse,
    YearPerformanceMonthResponse
)
from fastapi import HTTPException


class PlanService:

    @staticmethod
    async def insert_plans_from_csv(file_bytes: bytes, uow: UnitOfWork) -> None:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python')
        await PlanService._process_dataframe(df, uow)

    @staticmethod
    async def insert_plans_from_excel(file_bytes: bytes, uow: UnitOfWork) -> None:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception:
            raise HTTPException(status_code=400, detail="Наданий файл не є валідним Excel-файлом")

        await PlanService._process_dataframe(df, uow)

    @staticmethod
    async def _process_dataframe(df: pd.DataFrame, uow: UnitOfWork) -> None:
        async with uow:
            for _, row in df.iterrows():
                amount = row["sum"]
                if pd.isna(amount):
                    raise Exception("Стовпець 'сума' не має містити пустих значень")

                period_dt = pd.to_datetime(row["period"], dayfirst=True).date()
                if period_dt.day != 1:
                    raise Exception(f"Невірний період: {period_dt}. Має бути 1-ше число місяця.")

                category_id = int(row["category_id"])

                if await uow.plans.plan_exists(period_dt, category_id):
                    raise Exception(f"План для категорії {category_id} на період {period_dt} вже існує")

                plan_payload = {
                    "period": period_dt,
                    "sum": Decimal(str(amount)),
                    "category_id": category_id
                }
                await uow.plans.create_plan(**plan_payload)
            await uow.commit()

    @staticmethod
    async def get_plans_performance(check_date: date, uow: UnitOfWork) -> list[PlanPerformanceResponse]:
        async with uow:
            plans = await uow.plans.get_plans_for_month(check_date.year, check_date.month)
            result: list[PlanPerformanceResponse] = []

            for plan in plans:
                period_start = plan.period
                category_name = plan.category.name.lower().strip()
                fact_sum = 0.0

                if category_name in [CategoryNames.ISSUANCE_EN, CategoryNames.ISSUANCE_UA]:
                    _, fact_sum = await uow.credits.get_issued_credits(period_start, check_date)

                elif category_name in [
                    CategoryNames.COLLECTION_EN, CategoryNames.PERCENT_EN,
                    CategoryNames.COLLECTION_UA, CategoryNames.PERCENT_UA
                ]:
                    _, fact_sum = await uow.payments.get_percent_payments(period_start, check_date)
                else:
                    continue

                plan_sum = float(plan.sum)
                percent = round((fact_sum / plan_sum) * 100, 2) if plan_sum > 0 else 0

                result.append(PlanPerformanceResponse(
                    period=plan.period,
                    category=plan.category.name,
                    plan_sum=plan_sum,
                    fact_sum=fact_sum,
                    performance_percent=percent
                ))
            return result

    @staticmethod
    async def year_performance(year: int, uow: UnitOfWork) -> list[YearPerformanceMonthResponse]:
        async with uow:
            result: list[YearPerformanceMonthResponse] = []
            year_issued_total = 0.0
            year_payments_total = 0.0
            monthly_cache = {}

            for month in range(1, 13):
                start_date = date(year, month, 1)
                end_date = date(year, month, monthrange(year, month)[1])
                i_count, i_sum = await uow.credits.get_issued_credits(start_date, end_date)
                p_count, p_sum = await uow.payments.get_percent_payments(start_date, end_date)

                monthly_cache[month] = {"i_count": i_count, "i_sum": i_sum, "p_count": p_count, "p_sum": p_sum}
                year_issued_total += i_sum
                year_payments_total += p_sum

            plans = await uow.plans.get_plans_by_year(year)
            plans_map = defaultdict(lambda: {CategoryNames.ISSUANCE_EN: 0.0, CategoryNames.COLLECTION_EN: 0.0})

            for plan in plans:
                c_name = plan.category.name.lower().strip()
                key = CategoryNames.ISSUANCE_EN if c_name == CategoryNames.ISSUANCE_UA else CategoryNames.COLLECTION_EN
                plans_map[plan.period.month][key] = float(plan.sum)

            for month in range(1, 13):
                m = monthly_cache[month]
                i_plan = plans_map[month][CategoryNames.ISSUANCE_EN]
                p_plan = plans_map[month][CategoryNames.COLLECTION_EN]

                result.append(YearPerformanceMonthResponse(
                    month=month, year=year,
                    issued_plan_sum=i_plan, issued_fact_sum=m["i_sum"], issued_count=m["i_count"],
                    issued_percent=(round((m["i_sum"] / i_plan) * 100, 2) if i_plan else 0),  # if... защита от деления на ноль
                    payments_plan_sum=p_plan, payments_fact_sum=m["p_sum"], payments_count=m["p_count"],
                    payments_percent=(round((m["p_sum"] / p_plan) * 100, 2) if p_plan else 0),
                    issued_part_of_year=(round((m["i_sum"] / year_issued_total) * 100, 2) if year_issued_total else 0),
                    payments_part_of_year=(
                        round((m["p_sum"] / year_payments_total) * 100, 2) if year_payments_total else 0)
                ))
            return result