import os
from .dictionary_service import DictionaryService
from .plan_service import PlanService
from .payment_service import PaymentService
from .user_service import UserService
from .credit_service import CreditService
from ..data_base import engine, UnitOfWork
from ..exceptions import AppException
from ..models import Base


class ImportService:

    @staticmethod
    async def import_all_data(uow: UnitOfWork):
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        steps = [
            ("users.csv", UserService.import_users_from_csv),
            ("dictionary.csv", DictionaryService.import_dictionary_from_csv),
            ("credits.csv", CreditService.import_credits_from_csv),
            ("payments.csv", PaymentService.import_payments_from_csv),
            ("plans.csv", PlanService.insert_plans_from_csv)
        ]
        log = []
        for file_name, func in steps:
            path = f"documents/{file_name}"

            if not os.path.exists(path):
                log.append(f"⚠️ {file_name} пропущено: файл не знайдено по шляху {path}")
                continue

            try:
                with open(path, "rb") as f:
                    file_bytes = f.read()
                    if not file_bytes:
                        raise AppException(f"Файл {file_name} порожній", status_code=400)

                    await func(file_bytes, uow)

                log.append(f"✅ {file_name} успішно загружено")

            except Exception as e:
                log.append(f"❌ Помилка в {file_name}: {type(e).__name__} - {str(e)}")

        return {
            "status": "Migration finished",
            "log": log,
            "note": "Якщо помилка 'id', перевір роздільник в CSV (повинні бути пробіли)"
        }