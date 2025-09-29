from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Importa todos los modelos para registrar los mapeos y resolver
# relaciones declaradas por nombre (p. ej., "Task", "Comment", etc.).
# Estos imports deben permanecer al final para evitar ciclos.
from app.models import board as _board  # noqa: E402,F401
from app.models import column as _column  # noqa: E402,F401
from app.models import comment as _comment  # noqa: E402,F401
from app.models import task as _task  # noqa: E402,F401
from app.models import user as _user  # noqa: E402,F401
