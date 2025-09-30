from __future__ import annotations

from typing import Generic, Sequence, Tuple, Type, TypeVar
from datetime import datetime, timezone

from sqlalchemy.orm import Session

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: int) -> ModelType | None:
        obj = db.get(self.model, id)
        if obj is None:
            return None
        # Excluir registros soft-deleted si el modelo tiene el atributo
        if hasattr(self.model, "deleted_at") and getattr(obj, "deleted_at", None) is not None:
            return None
        return obj

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> Tuple[Sequence[ModelType], int]:
        query = db.query(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.filter(self.model.deleted_at.is_(None))
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def create(self, db: Session, obj_in: dict) -> ModelType:
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, db_obj: ModelType, obj_in: dict) -> ModelType:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, id: int) -> ModelType | None:
        obj = db.get(self.model, id)
        if obj is None:
            return None
        # Soft delete si el modelo tiene deleted_at, si no, borrar físicamente
        if hasattr(self.model, "deleted_at"):
            setattr(obj, "deleted_at", datetime.now(timezone.utc))
            db.add(obj)
        else:
            db.delete(obj)
        db.commit()
        return obj
