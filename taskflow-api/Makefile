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