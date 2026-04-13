import pandas as pd
from datetime import date
from calendar import monthrange
from collections import defaultdict
from decimal import Decimal
import io
import asyncio
from ..data_base import UnitOfWork
from ..exceptions import AppException
from ..models import CategoryNames
from ..schemas import (
    PlanPerformanceResponse,
    YearPerformanceMonthResponse
)


class PlanService:

    @staticmethod
    async def insert_plans_from_csv(file_bytes: bytes, uow: UnitOfWork) -> None:
        df = await asyncio.to_thread(pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python'))
        await PlanService._process_dataframe(df, uow)

    @staticmethod
    async def insert_plans_from_excel(file_bytes: bytes, uow: UnitOfWork) -> None:
        try:
            df = await asyncio.to_thread(pd.read_excel, io.BytesIO(file_bytes))
        except Exception:
            raise AppException(message="Наданий файл не є валідним Excel-файлом", status_code=400)

        await PlanService._process_dataframe(df, uow)

    @staticmethod
    async def _process_dataframe(df: pd.DataFrame, uow: UnitOfWork) -> None:
        plans_to_create = []
        seen_in_file = set()

        for _, row in df.iterrows():
            amount = row["sum"]
            if pd.isna(amount):
                raise AppException("Стовпець 'сума' не має містити пустих значень")

            try:
                period_dt = pd.to_datetime(row["period"], dayfirst=True).date()
            except Exception:
                raise AppException(f"Невірний формат дати у рядку з сумою {amount}")

            if period_dt.day != 1:
                raise AppException(f"Невірний період: {period_dt}. Має бути 1-ше число місяця.")

            category_id = int(row["category_id"])

            if (period_dt, category_id) in seen_in_file:
                raise AppException(f"Дублікат плану для категорії {category_id} на {period_dt} у файлі")
            seen_in_file.add((period_dt, category_id))

            plans_to_create.append({
                "period": period_dt,
                "sum": Decimal(str(amount)),
                "category_id": category_id
            })

        async with uow:
            all_periods = [p["period"] for p in plans_to_create]
            all_categories = [p["category_id"] for p in plans_to_create]

            existing_plans = await uow.plans.get_existing_plans_bulk(all_periods, all_categories)

            if existing_plans:
                ext_p = existing_plans[0]
                raise AppException(
                    f"План для категорії {ext_p.category_id} на період {ext_p.period} вже існує в базі",
                    status_code=409
                )

            await uow.plans.bulk_create_plans(plans_to_create)

            await uow.commit()

    @staticmethod
    async def get_plans_performance(check_date: date, uow: UnitOfWork) -> list[PlanPerformanceResponse]:
        async with uow:
            plans = await uow.plans.get_plans_for_month(check_date.year, check_date.month)
            if not plans:
                return []

            period_start = plans[0].period
            _, total_issued_fact = await uow.credits.get_issued_credits(period_start, check_date)
            _, total_payments_fact = await uow.credits.get_percent_payments(period_start, check_date)

            result: list[PlanPerformanceResponse] = []

            for plan in plans:
                category_name = plan.category.name.lower().strip()

                if category_name in [CategoryNames.ISSUANCE_EN, CategoryNames.ISSUANCE_UA]:
                    fact_sum = total_issued_fact

                elif category_name in [
                    CategoryNames.COLLECTION_EN, CategoryNames.PERCENT_EN,
                    CategoryNames.COLLECTION_UA, CategoryNames.PERCENT_UA
                ]:
                    fact_sum = total_payments_fact
                else:
                    fact_sum = 0.0

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
            # 1. Получаем агрегированную статистику за весь год двумя запросами
            # Эти методы мы добавили в репозитории (с использованием GROUP BY и extract)
            issued_stats = await uow.credits.get_year_issued_stats(year)
            payment_stats = await uow.payments.get_year_payments_stats(year)

            # 2. Получаем планы на этот год
            plans = await uow.plans.get_plans_by_year(year)

            # 3. Превращаем данные из базы в удобные словари для быстрого доступа по номеру месяца
            # Инициализируем нулями, чтобы не поймать KeyError, если за какой-то месяц нет данных
            issued_map = {m: {"sum": 0.0, "count": 0} for m in range(1, 13)}
            for row in issued_stats:
                issued_map[int(row.month)] = {"sum": float(row.total_sum or 0), "count": row.count}

            payments_map = {m: {"sum": 0.0, "count": 0} for m in range(1, 13)}
            for row in payment_stats:
                payments_map[int(row.month)] = {"sum": float(row.total_sum or 0), "count": row.count}

            # Группируем планы
            plans_map = defaultdict(lambda: {CategoryNames.ISSUANCE_EN: 0.0, CategoryNames.COLLECTION_EN: 0.0})
            for plan in plans:
                c_name = plan.category.name.lower().strip()
                # Логика маппинга категорий
                key = CategoryNames.ISSUANCE_EN if c_name in [CategoryNames.ISSUANCE_UA,
                                                              CategoryNames.ISSUANCE_EN] else CategoryNames.COLLECTION_EN
                plans_map[plan.period.month][key] = float(plan.sum)

            # 4. Считаем годовые итоги (теперь просто суммируем числа в памяти)
            year_issued_total = sum(item["sum"] for item in issued_map.values())
            year_payments_total = sum(item["sum"] for item in payments_map.values())

            # 5. Собираем финальный результат
            result: list[YearPerformanceMonthResponse] = []
            for month in range(1, 13):
                # Берем данные из наших кэш-словарей (база больше не дергается)
                i_fact = issued_map[month]
                p_fact = payments_map[month]

                i_plan = plans_map[month][CategoryNames.ISSUANCE_EN]
                p_plan = plans_map[month][CategoryNames.COLLECTION_EN]

                result.append(YearPerformanceMonthResponse(
                    month=month,
                    year=year,
                    # Секция выдач
                    issued_plan_sum=i_plan,
                    issued_fact_sum=i_fact["sum"],
                    issued_count=i_fact["count"],
                    issued_percent=(round((i_fact["sum"] / i_plan) * 100, 2) if i_plan > 0 else 0),

                    # Секция платежей
                    payments_plan_sum=p_plan,
                    payments_fact_sum=p_fact["sum"],
                    payments_count=p_fact["count"],
                    payments_percent=(round((p_fact["sum"] / p_plan) * 100, 2) if p_plan > 0 else 0),

                    # Доля месяца в годовом объеме
                    issued_part_of_year=(
                        round((i_fact["sum"] / year_issued_total) * 100, 2) if year_issued_total > 0 else 0),
                    payments_part_of_year=(
                        round((p_fact["sum"] / year_payments_total) * 100, 2) if year_payments_total > 0 else 0)
                ))

            return result