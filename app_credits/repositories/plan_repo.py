from datetime import date
from sqlalchemy import select, func
from ..models import Plan
from .base_repo import BaseRepo
from sqlalchemy.orm import joinedload


class PlanRepo(BaseRepo):

    async def plan_exists(self, period: date, category_id: int) -> bool:
        stmt = select(Plan.id).where(
            Plan.period == period,
            Plan.category_id == category_id
        )
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none() is not None

    async def create_plan(self, **plan_data) -> None:
        new_plan = Plan(**plan_data)
        self.db.add(new_plan)

    async def get_plans_by_year(self, year: int) -> list[Plan]:
        stmt = (
            select(Plan)
            .options(joinedload(Plan.category))
            .where(func.extract("year", Plan.period) == year)
        )
        result = await self.db.execute(stmt)

        return list(result.scalars().all())

    async def get_plans_for_month(self, year: int, month: int) -> list[Plan]:
        stmt = (
            select(Plan)
            .options(joinedload(Plan.category))
            .where(
                func.extract("year", Plan.period) == year,
                func.extract("month", Plan.period) == month
            )
        )
        result = await self.db.execute(stmt)

        return list(result.scalars().all())



