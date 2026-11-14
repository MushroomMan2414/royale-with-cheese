.PHONY: up down logs ps csv

export CSV

up:
	docker compose build
	sh scripts/migrate-downloads.sh
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f mornye

ps:
	docker compose ps

csv:
	@test -n "$$CSV" || { printf '%s\n' 'Usage: make csv CSV="/path/to/file.csv"'; exit 2; }
	@test -f "$$CSV" && test -r "$$CSV" || { printf '%s\n' "Cannot read CSV: $$CSV"; exit 2; }
	$(MAKE) up
	docker compose exec -T mornye python /opt/csv-download.py "$$(basename "$$CSV")" < "$$CSV"
