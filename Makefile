# =============================================================================
# BrokerWeeklyIntel - Makefile
# Convenient commands for development and operations
# =============================================================================

.PHONY: help install install-backend install-frontend \
        dev-frontend dev-backend dev \
        weekly run-analysis generate-report \
        test test-backend lint format clean \
        db-upgrade db-downgrade \
        docker-up docker-down

# -----------------------------------------------------------------------------
# Help
# -----------------------------------------------------------------------------
help:
	@echo "BrokerWeeklyIntel - Available Make Targets"
	@echo ""
	@echo "  install              Install all dependencies (frontend + backend)"
	@echo "  install-backend      Install Python dependencies only"
	@echo "  install-frontend     Install Node dependencies only"
	@echo ""
	@echo "  dev-frontend         Start Next.js development server (port 3000)"
	@echo "  dev-backend          Start FastAPI development server (port 8000)"
	@echo "  dev                  Start both frontend and backend (requires tmux or manual)"
	@echo ""
	@echo "  weekly               Run the complete weekly intelligence pipeline (local)"
	@echo "  run-analysis         Alias for weekly"
	@echo "  generate-report      Generate report artifacts for the latest week"
	@echo ""
	@echo "  test                 Run backend test suite"
	@echo "  lint                 Run linters (ruff + eslint)"
	@echo "  format               Auto-format code"
	@echo ""
	@echo "  clean                Remove caches, build artifacts, and temp files"
	@echo "  docker-up            Start full stack via docker-compose"
	@echo "  docker-down          Stop docker services"
	@echo ""

# -----------------------------------------------------------------------------
# Installation
# -----------------------------------------------------------------------------
install: install-backend install-frontend
	@echo "✅ All dependencies installed"

install-backend:
	cd backend && python -m pip install --upgrade pip && \
	pip install -r requirements.txt

install-frontend:
	cd frontend && npm install

# -----------------------------------------------------------------------------
# Development Servers
# -----------------------------------------------------------------------------
dev-frontend:
	cd frontend && npm run dev

dev-backend:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Note: For simultaneous dev, run in separate terminals or use:
#   make dev-backend & make dev-frontend
dev:
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals"
	@echo "Or use: tmux new-session -d 'make dev-backend' \\; split-window -h 'make dev-frontend'"

# -----------------------------------------------------------------------------
# Core Intelligence Pipeline
# -----------------------------------------------------------------------------
weekly run-analysis:
	@echo "🚀 Running full weekly competitor intelligence analysis..."
	cd backend && python -m scripts.run_weekly

generate-report:
	@echo "📄 Generating reports (Markdown + PDF) for current week..."
	cd backend && python -m scripts.generate_report

# -----------------------------------------------------------------------------
# Quality & Testing
# -----------------------------------------------------------------------------
test:
	cd backend && python -m pytest tests/ -v --tb=short

lint:
	cd backend && ruff check app/ scripts/ tests/
	cd frontend && npm run lint || true

format:
	cd backend && ruff format app/ scripts/ tests/
	cd frontend && npm run format || true

# -----------------------------------------------------------------------------
# Database (Alembic)
# -----------------------------------------------------------------------------
db-upgrade:
	cd backend && alembic upgrade head

db-downgrade:
	cd backend && alembic downgrade -1

# -----------------------------------------------------------------------------
# Docker
# -----------------------------------------------------------------------------
docker-up:
	docker-compose up --build

docker-down:
	docker-compose down

# -----------------------------------------------------------------------------
# Maintenance
# -----------------------------------------------------------------------------
clean:
	@echo "🧹 Cleaning project artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "node_modules" -prune -o -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf backend/.venv frontend/.next 2>/dev/null || true
	rm -f *.log 2>/dev/null || true
	@echo "✅ Clean complete (note: this did not remove data/ or reports/)"
