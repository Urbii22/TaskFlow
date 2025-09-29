from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import Role


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    role: Role

    # Permite crear el modelo desde instancias ORM (Pydantic v2)
    model_config = ConfigDict(from_attributes=True)
