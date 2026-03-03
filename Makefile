.PHONY: up down logs test migrate shell lint format typecheck clean

COMPOSE := docker compose -f infra/docker/docker-compose.yml
BACKEND := backend/.venv/bin

# --- Docker ---
up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

down-volumes:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

rebuild:
	$(COMPOSE) up -d --build

# --- Database ---
migrate:
	cd backend && $(BACKEND)/alembic upgrade head

migrate-create:
	cd backend && $(BACKEND)/alembic revision --autogenerate -m "$(msg)"

migrate-downgrade:
	cd backend && $(BACKEND)/alembic downgrade -1

# --- Testing ---
test:
	cd backend && $(BACKEND)/pytest tests/ -v --tb=short

test-cov:
	cd backend && $(BACKEND)/pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

test-unit:
	cd backend && $(BACKEND)/pytest tests/unit/ -v

test-integration:
	cd backend && $(BACKEND)/pytest tests/integration/ -v

# --- Code Quality ---
lint:
	cd backend && $(BACKEND)/ruff check .

format:
	cd backend && $(BACKEND)/ruff format .

typecheck:
	cd backend && $(BACKEND)/mypy .

quality: lint typecheck

# --- Shell ---
shell:
	$(COMPOSE) exec api bash

redis-cli:
	$(COMPOSE) exec redis redis-cli

psql:
	$(COMPOSE) exec postgres psql -U verifid -d verifid

# --- Cleanup ---
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	rm -rf backend/.pytest_cache backend/.mypy_cache backend/htmlcov backend/.coverage
