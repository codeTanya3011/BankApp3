from .base_repo import BaseRepo
from sqlalchemy.orm import joinedload
from datetime import date
from sqlalchemy import select, func, extract
from ..models import Payment, Dictionary, CategoryNames


class PaymentRepo(BaseRepo):

    async def get_credit_payments(self, credit_id: int) -> list[Payment]:
        stmt = (
            select(Payment)
            .options(joinedload(Payment.payment_type))
            .where(Payment.credit_id == credit_id)
        )
        result = await self.db.execute(stmt)

        return result.scalars().all()

    async def create_payment(self, **payment_data) -> None:
        new_payment = Payment(**payment_data)
        self.db.add(new_payment)

    async def get_percent_payments(
            self,
            date_from: date,
            date_to: date,
            categories: list[str]
    ) -> tuple[int, float]:
        stmt = select(
            func.count(Payment.id),
            func.coalesce(func.sum(Payment.sum), 0)
        ).join(
            Dictionary,
            Payment.type_id == Dictionary.id
        ).where(
            Payment.payment_date.between(date_from, date_to),
            Dictionary.name.in_(categories)
        )
        result = await self.db.execute(stmt)
        count, total = result.one()

        return count, float(total)

    async def get_year_payments_stats(self, year: int) -> list:
        stmt = (
            select(
                extract('month', Payment.payment_date).label('month'),
                func.count(Payment.id).label('count'),
                func.coalesce(func.sum(Payment.sum), 0).label('total_sum')
            )
            .join(Dictionary, Payment.type_id == Dictionary.id)
            .where(
                extract('year', Payment.payment_date) == year,
                Dictionary.name.in_([
                    CategoryNames.PERCENT_UA.value,
                    CategoryNames.BODY_UA.value
                ])
            )
            .group_by('month')
        )
        result = await self.db.execute(stmt)
        return result.all()
