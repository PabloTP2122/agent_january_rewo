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
	uv run fastapi dev src/api/main.py

server-run:
	uv run fastapi dev src/api/main.py

lang-dev:
	uv run langgraph dev

#delete-all-docker:
#	docker system prune -a --volumes
