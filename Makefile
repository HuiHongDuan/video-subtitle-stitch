.PHONY: backend-install frontend-install backend-dev frontend-dev test smoke docker-up docker-down docker-logs

backend-install:
	cd backend && python -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements.txt

frontend-install:
	cd frontend && npm install

backend-dev:
	cd backend && . .venv/bin/activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend-dev:
	cd frontend && npm run dev

test:
	cd backend && . .venv/bin/activate && pytest -q

smoke:
	bash scripts/smoke_test.sh


docker-up:
	bash scripts/docker_up.sh

docker-down:
	bash scripts/docker_down.sh

docker-logs:
	bash scripts/docker_logs.sh
