from sqlalchemy import select
from ..models import Dictionary
from .base_repo import BaseRepo


class DictionaryRepo(BaseRepo):

    async def get_category_by_id(self, category_id: int) -> Dictionary | None:
        stmt = select(Dictionary).where(Dictionary.id == category_id)
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()

    async def create_category(self, **dict_data) -> None:
        new_category = Dictionary(**dict_data)
        self.db.add(new_category)

    async def get_category_by_name(self, name: str) -> Dictionary | None:
        stmt = select(Dictionary).where(Dictionary.name == name)
        result = await self.db.execute(stmt)

        return result.scalar_one_or_none()