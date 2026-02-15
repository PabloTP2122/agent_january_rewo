install:
	@echo "Sincrónizando con uv"
	uv sync

help:
	@echo "Estos son los comandos permitidos"

docker-up:
	docker compose up -d

docker-stop:
	docker compose stop

docker-show:
	docker compose ps

server-run-d:
	docker compose up -d
	CHECKPOINTER_TYPE=postgres uv run fastapi dev src/api/main.py --port 8123

server-run:
	uv run fastapi dev src/api/main.py --port 8123

server-prod:
	docker compose up -d
	CHECKPOINTER_TYPE=postgres uv run fastapi dev src/api/main.py --port 8123

lang-dev:
	uv run langgraph dev

#delete-all-docker:
#	docker system prune -a --volumes
