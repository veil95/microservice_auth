import re
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from pydantic_core import PydanticCustomError

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")



class UserLogin(BaseModel):
    username: str
    password: str


class UserRequestRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=25, description="username должен быть от 3 до 25 символов")
    display_name: str = Field(..., min_length=1, max_length=30, description="Отображаемое имя должно быть от 1 до 30 символов")
    password_plaintext: str = Field(..., min_length=5, description="минимальная длина паролы должна быть 5 символов")
    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        if not USERNAME_PATTERN.fullmatch(value):
            raise PydanticCustomError(
                "username_invalid_chars",
                "Username может содержать только латинские буквы, цифры и _",
            )
        return value.lower()

