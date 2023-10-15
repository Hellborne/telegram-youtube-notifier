from typing import Optional

from pydantic import ConfigDict

from .base import Schema


class UserSchema(Schema):
    id: Optional[int] = None
    user_id: int
    username: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    is_admin: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)


__all__ = ["UserSchema"]
