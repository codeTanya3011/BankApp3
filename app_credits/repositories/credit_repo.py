from ..models import Credit
from .base_repo import BaseRepo
from datetime import date
from sqlalchemy import select, func


class CreditRepo(BaseRepo):

    async def get_user_credits(self, user_id: int):
        stmt = select(Credit).where(Credit.user_id == user_id)
        result = await self.db.execute(stmt)

        return result.scalars().all()

    async def create_credit(self, **credit_data) -> None:
        new_credit = Credit(**credit_data)
        self.db.add(new_credit)

    async def get_credit_by_id(self, credit_id: int):
        stmt = select(Credit).where(Credit.id == credit_id)
        res = await self.db.execute(stmt)

        return res.scalar_one_or_none()

    async def get_issued_credits(
        self,
        date_from: date,
        date_to: date
    ) -> tuple[int, float]:
        stmt = select(
            func.count(Credit.id),
            func.coalesce(func.sum(Credit.body), 0)
        ).where(
            Credit.issuance_date.between(date_from, date_to)
        )
        result = await self.db.execute(stmt)
        count, total = result.one()

        return count, float(total)


