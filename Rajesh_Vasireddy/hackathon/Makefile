.PHONY: install dev-api dev-frontend test lint format type-check docker-up docker-down clean

# ── Setup ─────────────────────────────────────────────────────────────────────
install:
	pip install -r requirements.txt

# ── Development servers ───────────────────────────────────────────────────────
dev-api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

dev-frontend:
	streamlit run frontend/app.py --server.port 8501

# ── Quality ───────────────────────────────────────────────────────────────────
lint:
	ruff check .

format:
	ruff format .

type-check:
	mypy agents/ orchestrator/ api/ integrations/

test:
	pytest -v

test-cov:
	pytest -v --cov=. --cov-report=term-missing

# ── Docker ────────────────────────────────────────────────────────────────────
docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

# ── Clean ─────────────────────────────────────────────────────────────────────
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache dist build *.egg-info
