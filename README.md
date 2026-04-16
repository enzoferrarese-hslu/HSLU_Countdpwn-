# HSLU Semester Countdown

Flask-App fuer einen Semester-Countdown mit Retro-UI. Die Anwendung ist fuer Docker Compose mit drei Containern vorbereitet:

- `db`: PostgreSQL-Datenbank fuer die Semesterdaten
- `scraper`: Python/BeautifulSoup-Scraper, der einmal startet und das aktuelle Semester speichert
- `web`: Flask-Webservice, der Startseite, Countdown-Seite und API ausliefert

## Projektstruktur

```text
.
|-- app.py                  # Flask-Routen und API-Endpunkte
|-- countdown_service.py    # Countdown-Logik und get_countdown(mode)
|-- db.py                   # PostgreSQL-Verbindung und DB-Zugriff
|-- bf_code_for_db.py       # BeautifulSoup-Scraper
|-- docker-compose.yml      # db, scraper, web
|-- Dockerfile.web
|-- Dockerfile.scraper
|-- static/
|   |-- script.js
|   `-- style.css
`-- templates/
    |-- index.html
    `-- countdown.html
```

## Start Mit Docker

Voraussetzung: Docker Desktop muss laufen.

```bash
docker compose up --build
```

Danach ist die App erreichbar unter:

```text
http://localhost:5000
```

Der Scraper-Container laeuft beim Start einmal, liest die HSLU-Seite und schreibt das aktuelle Semester in PostgreSQL. Der Webservice startet parallel, liest aus PostgreSQL und liefert weiterhin dieselben Routen aus.

## Wichtige Routen

```text
GET /
GET /countdown/contact
GET /countdown/exam
GET /api/countdown/contact
GET /api/countdown/exam
```

## Konfiguration

Die Container verwenden diese Datenbank-URL:

```text
DATABASE_URL=postgresql://postgres:postgres@db:5432/semester_countdown
```

Fuer lokale Ausfuehrung ohne Docker kann dieselbe Variable auf eine lokal laufende PostgreSQL-Datenbank zeigen.

## Scraper Manuell Ausfuehren

Wenn die Container bereits laufen:

```bash
docker compose run --rm scraper
```

## Hinweise

- Das Frontend wurde fuer die Dockerisierung nicht angepasst.
- Die fruehere SQLite-Datei `semester_dates.db` wird im Docker-Setup nicht mehr verwendet.
- PostgreSQL-Daten bleiben im Docker-Volume `postgres_data` erhalten.
- Falls beim ersten Laden noch keine Daten vorhanden sind, kurz warten oder den Scraper manuell erneut starten.
