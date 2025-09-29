from pydantic import BaseModel, ConfigDict


class BoardBase(BaseModel):
    name: str


class BoardCreate(BoardBase):
    pass


class BoardUpdate(BaseModel):
    name: str | None = None


class BoardRead(BoardBase):
    id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
