.PHONY: dev backend frontend test lint

dev:
	docker-compose -f infra/docker-compose.dev.yml up --build

backend:
	cd backend && uvicorn app.main:app --reload --port 8000

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest

lint:
	cd backend && ruff check app/
	cd frontend && npm run lint
