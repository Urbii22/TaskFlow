from pydantic import BaseModel, ConfigDict


class ColumnBase(BaseModel):
    name: str
    position: int


class ColumnCreate(ColumnBase):
    board_id: int


class ColumnUpdate(BaseModel):
    name: str | None = None
    position: int | None = None


class ColumnRead(ColumnBase):
    id: int
    board_id: int

    model_config = ConfigDict(from_attributes=True)
