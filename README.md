# HSLU Semester Countdown

Flask-App fuer einen Semester-Countdown mit Retro-UI. Die Anwendung ist fuer Docker Compose mit drei Containern vorbereitet und in eine kleine, uebersichtliche Projektstruktur aufgeteilt.

## Architektur

- `db`: PostgreSQL-Datenbank fuer die Semesterdaten
- `scraper`: Python-Scraper-Service, der mehrere HSLU-Quellen verarbeitet und Semesterdaten speichert
- `web`: Flask-Webservice, der Startseite, Countdown-Seite und API ausliefert

## Projektstruktur

```text
.
|-- app.py                         # lokaler Einstiegspunkt fuer Flask
|-- api/
|   `-- index.py                   # Vercel-Einstiegspunkt fuer Flask
|-- docker-compose.yml             # startet db, scraper und web
|-- vercel.json                    # Vercel-Routing fuer die Flask-App
|-- requirements.txt
|-- app/
|   |-- routes.py                  # Flask-Routen und API-Endpunkte
|   |-- database/
|   |   `-- db.py                  # PostgreSQL-Verbindung und DB-Zugriff
|   |-- services/
|   |   `-- countdown_service.py   # Countdown-Logik und get_countdown(mode)
|   |-- scraper/
|   |   |-- bf_code_for_db.py      # kompatibler Einstiegspunkt fuer den Scraper-Container
|   |   |-- common.py              # gemeinsames Datenformat und Parsing-Helfer
|   |   |-- technik_architektur.py # HTML-Scraper fuer Technik & Architektur
|   |   |-- wirtschaft_pdf.py      # PDF-Scraper fuer Wirtschaft
|   |   `-- run_all.py             # fuehrt alle Scraper nacheinander aus
|   |-- static/                    # bestehendes Frontend-CSS/JS
|   `-- templates/                 # bestehende HTML-Templates
|-- docker/
|   |-- Dockerfile.web
|   `-- Dockerfile.scraper
|-- data/                          # lokale Datenbankdateien, nicht fuer Docker
|-- docs/                          # Debug-/Hilfsdateien
`-- tests/                         # Platz fuer spaetere Tests
```

## Start mit Docker

Voraussetzung: Docker Desktop muss laufen.

```bash
docker compose up --build
```

Danach ist die App erreichbar unter:

```text
http://localhost:5000
```

Der Scraper-Container laeuft beim Start einmal, verarbeitet aktuell:

- `Technik & Architektur` ueber den bestehenden HTML-Scraper
- `Wirtschaft` ueber einen PDF-Scraper
- `Informatik` ueber einen HTML-Scraper

Beide liefern dieselbe Datenstruktur und werden gemeinsam in PostgreSQL gespeichert. Der Webservice liest standardmaessig weiterhin `Technik & Architektur` aus und liefert dieselben Routen aus.

## Wichtige Routen

```text
GET /
GET /countdown/contact
GET /countdown/exam
GET /api/countdown/contact
GET /api/countdown/exam
```

Optional akzeptiert die API bereits einen Query-Parameter fuer das Department:

```text
GET /api/countdown/contact?department=Wirtschaft
```

Ohne Parameter bleibt das Verhalten unveraendert und nutzt `Technik & Architektur`.

## Konfiguration

Die Container verwenden diese Datenbank-URL:

```text
DATABASE_URL=postgresql://postgres:postgres@db:5432/semester_countdown
```

Fuer lokale Ausfuehrung ohne Docker kann dieselbe Variable auf eine lokal laufende PostgreSQL-Datenbank zeigen.

## Scraper manuell ausfuehren

Wenn die Container bereits laufen:

```bash
docker compose run --rm scraper
```

## Lokale Ausfuehrung ohne Docker

Wenn du die App direkt mit Python starten willst, installiere zuerst die Abhaengigkeiten:

```bash
pip install -r requirements.txt
python app.py
```

Dabei muss eine PostgreSQL-Datenbank erreichbar sein, passend zur `DATABASE_URL`.

## Deployment mit Vercel

Das Projekt ist minimal fuer Vercel vorbereitet. Vercel fuehrt die bestehende Flask-App ueber `api/index.py` als Python Function aus.

Wichtig: Vercel startet keine Docker-Compose-Services. Fuer ein Deployment brauchst du deshalb eine externe PostgreSQL-Datenbank, zum Beispiel ueber einen gehosteten Postgres-Anbieter. In Vercel muss danach diese Environment Variable gesetzt werden:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

Deployment-Schritte:

```bash
vercel
```

oder ueber die Vercel-Weboberflaeche das Git-Repository importieren und die `DATABASE_URL` in den Project Settings setzen.

Der Scraper laeuft auf Vercel nicht automatisch als eigener Container. Um die Datenbank zu befuellen, kann der Scraper weiterhin lokal oder per Docker gegen die externe `DATABASE_URL` ausgefuehrt werden.

## Railway-Hinweis

Fuer Railway bleibt die Architektur dockerfreundlich:

- `web` nutzt `docker/Dockerfile.web`
- `scraper` nutzt `docker/Dockerfile.scraper`
- die PostgreSQL-URL kommt ueber `DATABASE_URL`

Wenn mehrere Departments aktuell gehalten werden sollen, sollte der Railway-Scraper als Cron Job laufen. Railway startet Cron-Services laut offizieller Doku zum konfigurierten Zeitpunkt, fuehrt den Start-Command aus und erwartet danach ein sauberes Beenden des Prozesses. Genau dafuer ist der bestehende Scraper-Runner geeignet.

Empfohlene Railway-Cron-Konfiguration:

```text
0 0 1 * *
```

Das bedeutet: einmal pro Monat am 1. Tag um 00:00 UTC.

Wichtig fuer den Semesterwechsel:

- Der Scraper speichert nicht mehr blind nur das gerade aktive Semester.
- Wenn kein aktives Semester gefunden wird, waehlt das Backend automatisch das naechste bevorstehende Semester.
- Falls es weder ein aktives noch ein kommendes Semester gibt, faellt es erst danach auf das zuletzt vergangene Semester zurueck.

Damit aktualisiert sich der gespeicherte Datensatz auch dann sinnvoll, wenn zwischen zwei Semestern gerade keine aktive Unterrichtsphase laeuft.

## Hinweise

- Das Frontend wurde bei der Umstrukturierung nur verschoben, nicht neu gestaltet.
- Das Frontend wurde fuer die Multi-Department-Erweiterung nicht angepasst.
- Die fruehere SQLite-Datei liegt unter `data/` und wird im Docker-Setup nicht mehr verwendet.
- PostgreSQL-Daten bleiben im Docker-Volume `postgres_data` erhalten.
- Falls beim ersten Laden noch keine Daten vorhanden sind, kurz warten oder den Scraper manuell erneut starten.
