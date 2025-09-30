up:
	docker compose up -d --build

logs:
	docker compose logs -f api

down:
	docker compose down -v

test:
	docker compose run --rm api pytest -q

lint:
	docker compose run --rm api ruff check .

format:
	docker compose run --rm api ruff format .

seed:
	docker compose build api
	docker compose run --rm api sh -c "alembic upgrade head && python -m app.db.seed"