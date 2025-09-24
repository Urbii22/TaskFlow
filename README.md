# TaskFlow — Backend API (FastAPI + PostgreSQL)

![Status](https://img.shields.io/badge/status-WIP-yellow) ![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue) ![License](https://img.shields.io/badge/license-MIT-green)

API de gestión de tareas/kanban con usuarios, roles y métricas. Pensada para portafolio técnico y como base para proyectos reales.

> **Stack:** FastAPI · Python 3.11 · PostgreSQL · SQLAlchemy 2.x · Alembic · JWT · Redis (opcional) · Docker & Compose · Pytest · GitHub Actions

---

## ✨ Features

- **Auth & Roles**: registro/login, JWT, roles `admin` y `user`.
- **Entidades**: `User`, `Board`, `Column`, `Task`, `Comment`.
- **CRUD completo** de boards/columnas/tareas/comentarios.
- **Filtros avanzados**: estado, prioridad, etiquetas; **paginación** y **ordenación**.
- **Búsqueda** por texto (título/descripción) con PostgreSQL `tsvector`.
- **Auditoría**: `created_at`, `updated_at` y **soft delete**.
- **Rate limit** básico por IP (ej. 60 req/min) con `slowapi` (configurable por env).
- **Caché** de listados con Redis (invalidación por cambios).
- **Salud & Métricas**: `GET /health` y `GET /metrics` para Prometheus.
- **OpenAPI**: `/docs` (Swagger) y `/redoc`.

---

## 🗺️ Arquitectura

```
app/
├─ api/
│  ├─ deps.py
│  ├─ v1/
│  │  ├─ auth.py
│  │  ├─ boards.py
│  │  ├─ columns.py
│  │  ├─ tasks.py
│  │  └─ comments.py
├─ core/
│  ├─ config.py        # settings (pydantic)
│  ├─ security.py      # JWT, pwd hashing
│  ├─ pagination.py    # helpers
│  └─ cache.py         # redis utils
├─ db/
│  ├─ base.py          # Base = declarative_base()
│  ├─ session.py       # sessionmaker / engine
│  └─ init_data.py     # seed opcional
├─ models/             # SQLAlchemy models
├─ repositories/       # capa de acceso a datos
├─ schemas/            # Pydantic models (request/response)
├─ services/           # lógica de negocio
├─ main.py             # create_app() y rutas
└─ migrations/         # Alembic (se crea al iniciar)

alembic.ini            # config Alembic
pyproject.toml         # deps y tooling (si usas Poetry)
requirements.txt       # alternativa con pip
docker-compose.yml
Dockerfile
```

---

## ⚙️ Requisitos

- **Docker** y **Docker Compose** (recomendado)
- **Python 3.11** (solo si deseas correr sin Docker)

---

## 🚀 Puesta en marcha

### Opción A) Con Docker (recomendada)

1) Copia variables de entorno:

```bash
cp .env.example .env
```

2) Build + levantar servicios:

```bash
docker compose up -d --build
```

3) Aplicar migraciones e (opcional) seed de datos:

```bash
# crear estructura (si aún no existen migraciones)
docker compose run --rm api bash -lc "alembic revision --autogenerate -m 'init'"
# aplicar migraciones
docker compose run --rm api bash -lc "alembic upgrade head"
# seed de datos (si existe el script)
docker compose run --rm api python -m app.db.init_data
```

4) Abre la API:

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Salud: http://localhost:8000/health

> **Windows/PowerShell**: Si ves `no configuration file provided: not found`, ejecuta Alembic **desde /app** dentro del contenedor, o indica el archivo con `-c`:
>
> ```powershell
> docker compose run --rm api bash -lc "cd /app && alembic -c alembic.ini upgrade head"
> # o
> docker compose run --rm api bash -lc "alembic -c /app/alembic.ini upgrade head"
> ```

### Opción B) Local (sin Docker)

1) Crear entorno y deps

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

2) Levanta Postgres (local o con Docker):

```bash
docker run --name taskflow-db -e POSTGRES_USER=taskflow -e POSTGRES_PASSWORD=taskflow   -e POSTGRES_DB=taskflow -p 5432:5432 -d postgres:16
```

3) Migraciones:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

4) Ejecuta la API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔑 Variables de entorno (`.env`)

Ejemplo mínimo:

```env
# App
APP_NAME=TaskFlow
ENV=dev
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=changeme-super-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# DB
DATABASE_URL=postgresql+psycopg://taskflow:taskflow@db:5432/taskflow
# Para local sin Docker: postgresql+psycopg://taskflow:taskflow@localhost:5432/taskflow

# Redis (opcional)
REDIS_URL=redis://redis:6379/0

# Rate limit (opcional)
RATE_LIMIT_PER_MINUTE=60

# Primer superusuario (se usa en seed opcional)
FIRST_SUPERUSER_EMAIL=admin@taskflow.dev
FIRST_SUPERUSER_PASSWORD=admin1234
```

---

## 🧱 Modelo de datos (resumen)

- **User**: id, email, hashed_password, role, is_active, timestamps
- **Board**: id, name, description, owner_id (FK User), timestamps, soft_delete
- **Column**: id, board_id, name, position
- **Task**: id, board_id, column_id, title, description, status, priority, labels[], assignee_id (FK User), due_date, timestamps, soft_delete, `search_vector`
- **Comment**: id, task_id, author_id, body, timestamps, soft_delete

Índices sugeridos: `(Task.board_id, column_id, status)`, GIN sobre `search_vector`.

---

## 🔐 Autenticación & Roles

- **Registro**: `POST /api/v1/auth/register`
- **Login** (OAuth2 Password): `POST /api/v1/auth/login` → `access_token` (JWT)
- Usa `Authorization: Bearer <token>` en endpoints protegidos.
- Rutas de administración requieren `role=admin`.

Ejemplo login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login   -H "Content-Type: application/x-www-form-urlencoded"   -d "username=admin@taskflow.dev&password=admin1234"
```

---

## 📚 Endpoints principales (v1)

- **Boards**: `/api/v1/boards`  
  - `POST` crear, `GET` listar (paginado), `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` (soft)
- **Columns**: `/api/v1/boards/{board_id}/columns`
- **Tasks**: `/api/v1/tasks`
  - Filtros: `status`, `priority`, `labels`, `assignee_id`, `board_id`, `column_id`
  - Paginación: `limit`, `offset` · Ordenación: `sort` (p.ej. `-created_at`, `priority`)
  - Búsqueda: `q` (texto libre)
- **Comments**: `/api/v1/tasks/{task_id}/comments`
- **Health**: `/health` · **Métricas**: `/metrics`

Ejemplo listado con filtros:

```bash
curl "http://localhost:8000/api/v1/tasks?board_id=1&status=todo&priority=high&labels=bug,backend&limit=20&offset=0&sort=-created_at"   -H "Authorization: Bearer $TOKEN"
```

---

## 🧪 Tests & Calidad

```bash
# tests
docker compose run --rm api pytest -q

# cobertura
docker compose run --rm api pytest --cov=app --cov-report=term-missing

# lint & format (si están configurados)
docker compose run --rm api ruff check .
docker compose run --rm api ruff format .
```

Opcional: hooks con **pre-commit** (`pre-commit install`).

---

## 📈 Observabilidad

- **/health**: OK si DB responde.
- **/metrics**: exposición para Prometheus (si habilitado).
- Logging estructurado JSON opcional via `LOG_LEVEL`.

---

## 🔁 Migraciones con Alembic (detalle)

Generar primera migración y aplicar:

```bash
# crear carpeta migrations + script inicial (si no existe)
alembic init migrations
# editar env.py para usar SQLAlchemy 2.x (app.db.base: Base)
# luego
alembic revision --autogenerate -m "init"
alembic upgrade head
```

**Docker** (asegura ruta correcta a alembic.ini):

```bash
docker compose run --rm api bash -lc "cd /app && alembic revision --autogenerate -m 'init'"
docker compose run --rm api bash -lc "cd /app && alembic upgrade head"
```

**Solución al error** `no configuration file provided: not found`:

- Estás ejecutando Alembic fuera del directorio que contiene `alembic.ini`.
- Ejecuta `cd /app` dentro del contenedor o usa `-c /app/alembic.ini`.

---

## 🧰 Makefile (opcional)

```Makefile
.PHONY: up down build logs api pytest migrate seed
up: ; docker compose up -d
down: ; docker compose down
build: ; docker compose build --no-cache
logs: ; docker compose logs -f api
migrate: ; docker compose run --rm api bash -lc "cd /app && alembic upgrade head"
seed: ; docker compose run --rm api python -m app.db.init_data
pytest: ; docker compose run --rm api pytest -q
api: ; docker compose run --rm --service-ports api bash
```

---

## 🤖 CI/CD (GitHub Actions)

`/.github/workflows/ci.yml` (ejemplo mínimo):

```yaml
name: CI
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: taskflow
          POSTGRES_PASSWORD: taskflow
          POSTGRES_DB: taskflow
        ports: ["5432:5432"]
        options: >-
          --health-cmd="pg_isready -U taskflow" --health-interval=10s --health-timeout=5s --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest -q
```

---

## 🗺️ Roadmap

- Adjuntos en tareas (S3/Local)
- WebSockets para actualizaciones en tiempo real
- Notificaciones (email/webhook)
- RBAC más granular por board
- Export/Import (JSON/CSV)

---

## 📄 Licencia

MIT © TuNombre

---

## 🙌 Agradecimientos

- Plantillas y buenas prácticas de la comunidad FastAPI y SQLAlchemy.

---

### Notas para el día 2 (contexto del proyecto)

- Foco: configurar DB, migraciones iniciales, endpoints de `Board` y `Task`, y resolver el issue de Alembic en Windows/PowerShell (usar `-c /app/alembic.ini`).
