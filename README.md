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
- **Salud & Métricas**: `GET /api/v1/health` y `GET /metrics` para Prometheus.
- **OpenAPI**: `/docs` (Swagger) y `/redoc`.

---

## 🗺️ Arquitectura

```mermaid
flowchart LR
  A[Cliente] --> B[FastAPI (Routers)]
  B --> C[Servicios (Dominio)]
  C --> D[Repositorios (SQLAlchemy)]
  D --> E[(PostgreSQL)]
  C --> F[(Redis - Caché)]
```

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
│  └─ seed.py          # seed opcional
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

1) Crea o edita `.env` con POSTGRES_HOST=db:

```env
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=taskflow
POSTGRES_USER=taskflow
POSTGRES_PASSWORD=taskflow
REDIS_URL=redis://redis:6379/0
ENV=dev
DEBUG=True
```

2) Build + levantar servicios:

```bash
cd taskflow-api
docker compose up -d --build
```

3) Aplicar migraciones e (opcional) seed de datos:

```bash
# crear estructura (si aún no existen migraciones)
docker compose run --rm api bash -lc "alembic revision --autogenerate -m 'init'"
# aplicar migraciones (normalmente se aplican automáticamente al levantar la API)
docker compose run --rm api bash -lc "alembic upgrade head"
# seed de datos (opcional)
docker compose run --rm api python -m app.db.seed
```

4) Abre la API:

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Salud: http://localhost:8000/api/v1/health

### Colección Postman/Insomnia

- Se incluye una colección lista para usar: `taskflow-api-collection.json` en la raíz del repo.
- Base URL por defecto: `http://localhost:8000` (variable `base_url`) y `http://localhost:8000/api/v1` (variable `api_base`).
- Flujo sugerido:
  1. Ejecuta `POST /api/v1/auth/register` y luego `POST /api/v1/auth/login`.
  2. El login guarda automáticamente `{{token}}` en variables de colección.
  3. Usa los endpoints protegidos (añaden `Authorization: Bearer {{token}}`).
  4. Ajusta variables `board_id`, `column_id`, `task_id`, `comment_id` si deseas probar rutas específicas.

> **Windows/PowerShell**: Si ves `no configuration file provided: not found`, ejecuta Alembic **desde /app** dentro del contenedor, o indica el archivo con `-c`:
>
> ```powershell
> docker compose run --rm api bash -lc "cd /app && alembic -c alembic.ini upgrade head"
> # o
> docker compose run --rm api bash -lc "alembic -c /app/alembic.ini upgrade head"
> # seed opcional
> docker compose run --rm api python -m app.db.seed
> ```

### Opción B) Local (sin Docker)

1) Crear entorno y deps

```bash
cd taskflow-api
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Crea `.env` para entorno local (sin Docker):

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=taskflow
POSTGRES_USER=taskflow
POSTGRES_PASSWORD=taskflow
REDIS_URL=redis://localhost:6379/0
ENV=dev
DEBUG=True
```

3) Levanta Postgres (local o con Docker):

```bash
docker run --name taskflow-db -e POSTGRES_USER=taskflow -e POSTGRES_PASSWORD=taskflow   -e POSTGRES_DB=taskflow -p 5432:5432 -d postgres:16
```

4) Migraciones:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

5) Ejecuta la API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🚢 Despliegue a producción

Recomendado usar Docker Compose con Postgres y Redis gestionados.

- Establece `ENV=prod`, `DEBUG=false` y un `SECRET_KEY` fuerte y único.
- Revisa los `ports` publicados en `docker-compose.yml` y usa un proxy reverso (Nginx/Caddy) con TLS.
- Ajusta CORS si vas a exponer la API públicamente (ver nota más abajo).
- Considera aumentar workers: `uvicorn --workers 2` o usar `gunicorn -k uvicorn.workers.UvicornWorker -w 2`.
- Configura backups de Postgres y retención de logs.

Ejemplo mínimo:

```bash
cd taskflow-api
SECRET_KEY=$(openssl rand -hex 32) \
ENV=prod DEBUG=false docker compose up -d --build
```

## 🔑 Variables de entorno (`.env`)

Ejemplos mínimos según el modo de ejecución:

Docker (compose):

```env
# App
APP_NAME=TaskFlow
ENV=dev
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=changeme-super-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# DB (Docker)
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=taskflow
POSTGRES_USER=taskflow
POSTGRES_PASSWORD=taskflow

# Redis (opcional, Docker)
REDIS_URL=redis://redis:6379/0

# Rate limit (opcional)
RATE_LIMIT_PER_MINUTE=60

# Primer superusuario (seed opcional)
FIRST_SUPERUSER_EMAIL=admin@taskflow.dev
FIRST_SUPERUSER_PASSWORD=admin1234
```

Local (sin Docker):

```env
# App
APP_NAME=TaskFlow
ENV=dev
DEBUG=true
LOG_LEVEL=INFO
SECRET_KEY=changeme-super-secret
ACCESS_TOKEN_EXPIRE_MINUTES=60
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# DB (Local)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=taskflow
POSTGRES_USER=taskflow
POSTGRES_PASSWORD=taskflow

# Redis (opcional, Local)
REDIS_URL=redis://localhost:6379/0

# Rate limit (opcional)
RATE_LIMIT_PER_MINUTE=60

# Primer superusuario (seed opcional)
FIRST_SUPERUSER_EMAIL=admin@taskflow.dev
FIRST_SUPERUSER_PASSWORD=admin1234
```

Nota: si ves el error "[Errno 11001] getaddrinfo failed" al ejecutar Alembic en local, revisa que `POSTGRES_HOST=localhost`. Cuando corras con Docker, debe ser `POSTGRES_HOST=db`.

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

### Ejemplos rápidos

```bash
# Registro
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@taskflow.dev","password":"user1234"}'

# Login (OAuth2 Password)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@taskflow.dev&password=user1234" | jq -r .access_token)

# Crear tablero
curl -X POST http://localhost:8000/api/v1/boards \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name":"Proyecto Demo"}'
```

Ejemplo login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login   -H "Content-Type: application/x-www-form-urlencoded"   -d "username=admin@taskflow.dev&password=admin1234"
```

---

## 📚 Tabla de Endpoints (v1)

| Método | Ruta | Descripción | Auth | Roles |
|---|---|---|---|---|
| GET | `/api/v1/health` | Ping de salud | No | N/A |
| GET | `/metrics` | Métricas Prometheus | No | N/A |
| POST | `/api/v1/auth/register` | Registrar usuario | No | N/A |
| POST | `/api/v1/auth/login` | Login (OAuth2 Password) → JWT | No | N/A |
| POST | `/api/v1/boards` | Crear tablero | Sí (Bearer) | USER, ADMIN |
| GET | `/api/v1/boards` | Listar tableros del usuario (paginado) | Sí | USER, ADMIN |
| GET | `/api/v1/boards/{board_id}` | Obtener tablero (propio) | Sí | USER, ADMIN |
| PATCH | `/api/v1/boards/{board_id}` | Actualizar tablero (propio) | Sí | USER, ADMIN |
| DELETE | `/api/v1/boards/{board_id}` | Eliminar tablero (soft, propio) | Sí | USER, ADMIN |
| GET | `/api/v1/boards/{board_id}/columns` | Listar columnas de un tablero | Sí | USER, ADMIN |
| POST | `/api/v1/columns` | Crear columna en tablero propio | Sí | USER, ADMIN |
| GET | `/api/v1/columns/{column_id}` | Obtener columna (propia) | Sí | USER, ADMIN |
| PATCH | `/api/v1/columns/{column_id}` | Actualizar columna (propia) | Sí | USER, ADMIN |
| DELETE | `/api/v1/columns/{column_id}` | Eliminar columna (propia) | Sí | USER, ADMIN |
| GET | `/api/v1/columns/{column_id}/tasks` | Listar tareas de la columna | Sí | USER, ADMIN |
| GET | `/api/v1/tasks?q=...` | Buscar tareas del usuario (paginado) | Sí | USER, ADMIN |
| POST | `/api/v1/tasks` | Crear tarea | Sí | USER, ADMIN |
| GET | `/api/v1/tasks/{task_id}` | Obtener tarea (propia) | Sí | USER, ADMIN |
| PATCH | `/api/v1/tasks/{task_id}` | Actualizar tarea (propia) | Sí | USER, ADMIN |
| DELETE | `/api/v1/tasks/{task_id}` | Eliminar tarea (propia) | Sí | USER, ADMIN |
| POST | `/api/v1/comments` | Crear comentario (autor=usuario actual) | Sí | USER, ADMIN |
| GET | `/api/v1/comments/{comment_id}` | Obtener comentario (autor o dueño del tablero) | Sí | USER, ADMIN |
| PATCH | `/api/v1/comments/{comment_id}` | Actualizar comentario (solo autor) | Sí | USER, ADMIN |
| DELETE | `/api/v1/comments/{comment_id}` | Eliminar comentario (solo autor) | Sí | USER, ADMIN |

### Paginación

- Esquema de respuesta: `Page[T]` con campos `items`, `total`, `page`, `size`.
- Parámetros: `skip` (offset) y `limit` (tamaño de página). Cálculo de `page` basado en `skip/limit`.

### Rate limiting

- Límite por endpoint usando `slowapi` (ver decoradores `@limiter.limit`).
- Clave de rate limit: IP remota; en `DEBUG` puede usar `X-RateLimit-Key` o `X-Request-ID`.
- Respuesta al exceder: 429 Too Many Requests.

### Caché HTTP (aplicación)

- Caché de respuestas con `fastapi-cache`: ver decorador `@cache` en listados/búsquedas.
- TTL típico 60s; la clave incluye `path`, `query` y `user.id` (si autenticado).
- Invalidación tras cambios de tareas: se limpian namespaces `tasks:get` y `tasks:search`.

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

### Convenciones de errores

- 400: validación de entrada o reglas de dominio (por ejemplo, email duplicado).
- 401: sin token válido (`WWW-Authenticate: Bearer`).
- 403: sin permisos (si se implementa distinción futura admin/propietario).
- 404: recurso inexistente o sin acceso (evita filtrar información).
- 429: límite de peticiones excedido.

Formato de error típico:

```json
{ "detail": "Mensaje de error" }
```

---

## 📈 Observabilidad

- **/api/v1/health**: OK si DB responde (chequeo ligero).
- **/metrics**: exposición para Prometheus (si habilitado).
- Logging estructurado JSON opcional via `LOG_LEVEL`.

Cabeceras útiles:

- `X-Request-ID`: ID de correlación por petición (útil para trazas/logs).

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
up: ; cd taskflow-api && docker compose up -d
down: ; cd taskflow-api && docker compose down
build: ; cd taskflow-api && docker compose build --no-cache
logs: ; cd taskflow-api && docker compose logs -f api
migrate: ; cd taskflow-api && docker compose run --rm api bash -lc "cd /app && alembic upgrade head"
seed: ; cd taskflow-api && docker compose run --rm api python -m app.db.seed
pytest: ; cd taskflow-api && docker compose run --rm api pytest -q
api: ; cd taskflow-api && docker compose run --rm --service-ports api bash
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

## 🤝 Contribución

1. Haz fork y crea una rama: `feat/nombre-corto`.
2. Instala dependencias y levanta servicios con Docker.
3. Asegura que los tests pasan y añade nuevos si corresponde.
4. Ejecuta linters/formatters si están configurados.
5. Abre PR describiendo el cambio, motivación y capturas si aplica.

## 🔒 Seguridad

- Nunca commitees `.env` con secretos reales.
- Cambia `SECRET_KEY` en producción.
- Limita orígenes en CORS (`CORS_ORIGINS`) para frontend conocido.
- Usa HTTPS en despliegues públicos.

---

## 📄 Licencia

MIT © TuNombre

---

## 🙌 Agradecimientos

- Plantillas y buenas prácticas de la comunidad FastAPI y SQLAlchemy.

---

### Notas para el día 2 (contexto del proyecto)

- Foco: configurar DB, migraciones iniciales, endpoints de `Board` y `Task`, y resolver el issue de Alembic en Windows/PowerShell (usar `-c /app/alembic.ini`).
