from ..models import User
from .base_repo import BaseRepo


class UserRepo(BaseRepo):

    async def get_user_by_id(self, user_id: int) -> User | None:

        return await self.db.get(User, user_id)

    async def create_user(self, **user_data) -> None:
        new_user = User(**user_data)
        self.db.add(new_user)

