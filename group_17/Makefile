.DEFAULT_GOAL := help

# ─── Variables ────────────────────────────────────────────────────────────────
APP_PORT    ?= 8501
API_PORT    ?= 8000
APP_ENTRY   := app.py
API_ENTRY   := server:app

# ─── Help ─────────────────────────────────────────────────────────────────────
.PHONY: help
help: ## Show this help message with all available targets
	@echo ""
	@echo "  DevOps Incident Analysis Suite — Makefile Targets"
	@echo "  ─────────────────────────────────────────────────"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────
.PHONY: env
env: ## Copy .env_example to .env (only if .env does not already exist)
	@if [ ! -f .env ]; then \
		cp .env_example .env; \
		echo "  .env created from .env_example — fill in your credentials"; \
	else \
		echo "  .env already exists, skipping"; \
	fi

.PHONY: install
install: ## Install all runtime dependencies via uv (creates .venv automatically)
	uv sync

.PHONY: install-dev
install-dev: ## Install runtime + dev dependencies (ruff, pytest) via uv
	uv sync --group dev

.PHONY: lock
lock: ## Regenerate uv.lock from pyproject.toml without installing
	uv lock

.PHONY: add
add: ## Add a runtime dependency — usage: make add PKG=package-name
	uv add $(PKG)

.PHONY: add-dev
add-dev: ## Add a dev-only dependency — usage: make add-dev PKG=package-name
	uv add --dev $(PKG)

.PHONY: export-requirements
export-requirements: ## Export uv.lock to requirements.txt for compatibility
	uv export --format requirements-txt --no-dev -o requirements.txt
	@echo "  requirements.txt exported from uv.lock"

# ─── Run ──────────────────────────────────────────────────────────────────────
.PHONY: run
run: ## Start the Streamlit app on port $(APP_PORT) (default: 8501)
	uv run streamlit run $(APP_ENTRY) --server.port $(APP_PORT)

.PHONY: run-mock
run-mock: ## Start the Streamlit app with MOCK_MODE=true (no Slack/JIRA API calls)
	MOCK_MODE=true uv run streamlit run $(APP_ENTRY) --server.port $(APP_PORT)

.PHONY: run-headless
run-headless: ## Start the Streamlit app in headless mode (no browser auto-open)
	uv run streamlit run $(APP_ENTRY) --server.port $(APP_PORT) --server.headless true

.PHONY: run-api
run-api: ## Start the FastAPI server on port $(API_PORT) (default: 8000) with auto-reload
	uv run uvicorn $(API_ENTRY) --host 0.0.0.0 --port $(API_PORT) --reload

.PHONY: run-api-mock
run-api-mock: ## Start the FastAPI server with MOCK_MODE=true (no Slack/JIRA calls)
	MOCK_MODE=true uv run uvicorn $(API_ENTRY) --host 0.0.0.0 --port $(API_PORT) --reload

.PHONY: run-all
run-all: ## Start both Streamlit UI (8501) and FastAPI server (8000) concurrently
	@echo "  Starting FastAPI on :$(API_PORT) and Streamlit on :$(APP_PORT) ..."
	uv run uvicorn $(API_ENTRY) --host 0.0.0.0 --port $(API_PORT) --reload & \
	uv run streamlit run $(APP_ENTRY) --server.port $(APP_PORT)

# ─── Quality ──────────────────────────────────────────────────────────────────
.PHONY: lint
lint: ## Lint all Python files with ruff
	uv run ruff check .

.PHONY: lint-fix
lint-fix: ## Auto-fix lint issues with ruff
	uv run ruff check . --fix

.PHONY: format
format: ## Format all Python files with ruff formatter
	uv run ruff format .

.PHONY: test
test: ## Run test suite with pytest
	uv run pytest tests/ -v

# ─── Utilities ────────────────────────────────────────────────────────────────
.PHONY: check-jira
check-jira: ## Query your JIRA project and list available issue types
	uv run python check_jira.py

.PHONY: check-env
check-env: ## Verify all required environment variables are set in .env
	@uv run python -c "\
import os; from dotenv import load_dotenv; load_dotenv(); \
keys = ['ANTHROPIC_API_KEY','SLACK_BOT_TOKEN','SLACK_CHANNEL_ID', \
        'JIRA_SERVER','JIRA_EMAIL','JIRA_API_TOKEN','JIRA_PROJECT_KEY']; \
missing = [k for k in keys if not os.getenv(k)]; \
print('  All required env vars are set.') if not missing \
else [print(f'  MISSING: {k}') for k in missing]"

.PHONY: sample-run
sample-run: ## Run the full pipeline against the bundled sample.log (CLI output)
	uv run python -c "\
from orchestrator.graph import run_incident_analysis; \
log = open('orchestrator/sample_logs/sample.log').read(); \
result = run_incident_analysis(log); \
import json; print(json.dumps({k: v for k, v in result.items() if k != 'log_content'}, indent=2, default=str))"

# ─── Cleanup ──────────────────────────────────────────────────────────────────
.PHONY: clean
clean: ## Remove Python cache files and compiled bytecode
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	@echo "  Cache cleaned"

.PHONY: clean-all
clean-all: clean ## Remove cache, .venv, and .env (use with caution)
	@echo "  WARNING: This will delete .venv and .env."
	@read -p "  Are you sure? [y/N] " ans && [ "$$ans" = "y" ] \
		&& rm -rf .venv && rm -f .env \
		&& echo "  .venv and .env removed" || echo "  Aborted"
