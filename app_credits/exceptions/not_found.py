from .base_exc import NotFoundError


class NotFoundUserError(NotFoundError):
    def __init__(self, user_id: int = None):
        self.user_id = user_id
        if user_id:
            message = f"User with id {user_id} not found"
        else:
            message = "User not found"
        super().__init__(message)


