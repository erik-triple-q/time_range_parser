.PHONY: dev prod down logs shell test release clear-cache

# Start development omgeving (foreground, debug logs, poort 9000)
dev:
	docker compose up --build

# Start productie omgeving (background, poort 9000, info logs, auto-restart)
prod:
	docker compose --env-file .env.prod -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Stop containers
down:
	docker compose down

# Bekijk logs (volgen)
logs:
	docker compose logs -f

# Open shell in de draaiende container (voor debugging)
shell:
	docker compose exec date-textparser-mcp sh

# Run tests (lokaal via uv)
test:
	uv run pytest

# Maak een nieuwe release (versie bump + docker build)
release:
	./release.sh

# Clear the docker volume used for caching
clear-cache:
	docker volume rm dateparser_cache || true