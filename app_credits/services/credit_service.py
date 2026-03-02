from ..data_base import UnitOfWork
from ..exceptions import NotFoundUserError
from datetime import date

from ..models import CategoryNames
from ..schemas.credit_schema import UserCreditResponse, UserCreditsListResponse
from decimal import Decimal
from typing import List
import pandas as pd
import io


class CreditService:

    @staticmethod
    async def import_credits_from_csv(file_bytes: bytes, uow: UnitOfWork):
        df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine='python')

        async with uow:
            for _, row in df.iterrows():
                credit_payload = {
                    "id": int(row["id"]),
                    "user_id": int(row["user_id"]),
                    "issuance_date": pd.to_datetime(row["issuance_date"], dayfirst=True).date(),
                    "return_date": pd.to_datetime(row["return_date"], dayfirst=True).date(),
                    "actual_return_date": pd.to_datetime(row["actual_return_date"], dayfirst=True).date()
                    if pd.notnull(row["actual_return_date"]) else None,
                    "body": Decimal(str(row["body"])),
                    "percent": Decimal(str(row["percent"]))
                }
                await uow.credits.create_credit(**credit_payload)

            await uow.commit()

    @staticmethod
    async def get_user_credits(user_id: int, uow: UnitOfWork) -> UserCreditsListResponse:
        async with uow:
            user = await uow.users.get_user_by_id(user_id)
            if not user:
                raise NotFoundUserError(user_id=user_id)

            credits_objs = await uow.credits.get_user_credits(user_id)
            if not credits_objs:

                return UserCreditsListResponse(user_id=user_id, credits=[])

            result: List[UserCreditResponse] = []
            for cr in credits_objs:
                credit_dict = {
                    "id": cr.id,
                    "issuance_date": cr.issuance_date,
                    "return_date": cr.return_date,
                    "actual_return_date": cr.actual_return_date,
                    "body": cr.body,
                    "percent": cr.percent
                }

                data = await CreditService.open_credit_data(credit_dict, uow)
                result.append(data)

            return UserCreditsListResponse(user_id=user_id, credits=result)

    @staticmethod
    async def closed_credit_data(credit_data: dict, uow: UnitOfWork) -> UserCreditResponse:

        return await CreditService.open_credit_data(credit_data, uow)

    @staticmethod
    async def open_credit_data(credit_data: dict, uow: UnitOfWork) -> UserCreditResponse:
        credit_id = credit_data["id"]
        payments = await uow.payments.get_credit_payments(credit_id)
        # ініціалізація сум
        body_sum = Decimal("0")
        percent_sum = Decimal("0")

        if payments:
            for p in payments:
                raw_type_name = getattr(p, "name", getattr(p, "type_name", "unknown"))
                p_type = str(raw_type_name).lower().strip()
                p_sum = Decimal(str(p.sum))

                if p_type in [CategoryNames.BODY_UA, CategoryNames.BODY_EN]:
                    body_sum += p_sum
                elif p_type in [CategoryNames.PERCENT_UA, CategoryNames.PERCENT_EN]:
                    percent_sum += p_sum

        actual_ret = credit_data["actual_return_date"]
        ret_date = credit_data["return_date"]
        is_closed = actual_ret is not None
        days_overdue = 0

        if ret_date:
            ref_date = actual_ret if is_closed else date.today()
            d1 = ref_date.date() if hasattr(ref_date, "date") else ref_date
            d2 = ret_date.date() if hasattr(ret_date, "date") else ret_date
            days_overdue = max((d1 - d2).days, 0)

        return UserCreditResponse(
            issuance_date=credit_data["issuance_date"],
            is_closed=is_closed,
            body=credit_data["body"],
            percent=credit_data["percent"],
            actual_return_date=actual_ret,
            return_date=ret_date,
            days_overdue=days_overdue,
            payments_sum=body_sum + percent_sum,
            body_payments_sum=body_sum,
            percent_payments_sum=percent_sum
        )