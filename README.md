# HSLU Semester Countdown

Retro-inspirierte Flask-App, die die verbleibende Zeit bis zum Ende des Kontaktstudiums oder der Prüfungsphase anzeigt. Die Countdown-Daten werden aus einer lokalen SQLite-Datenbank gelesen.

## Projektstruktur

```text
.
├── app.py                  # Flask-Routen und API-Endpunkt
├── countdown_service.py    # SQLite-Zugriff und get_countdown(mode)
├── bf_code_for_db.py       # Scraper/Importer für Semesterdaten
├── semester_dates.db       # lokale SQLite-Datenbank
├── static/
│   ├── script.js           # Countdown-Update im Browser
│   └── style.css           # Retro-UI
└── templates/
    ├── index.html
    └── countdown.html
```

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Lokal starten

```bash
python app.py
```

Die App läuft standardmäßig auf `http://127.0.0.1:5000`.

Für Debug-Modus:

```bash
$env:FLASK_DEBUG="1"
python app.py
```

## Daten aktualisieren

```bash
python bf_code_for_db.py
```

Das Skript liest die Semestertermine von der HSLU-Seite und schreibt das aktuelle Semester in `semester_dates.db`.

## API

```text
GET /api/countdown/contact
GET /api/countdown/exam
```

Beide Endpunkte nutzen weiterhin `get_countdown(mode)` aus `countdown_service.py`.

## Deployment-Hinweise

- `PORT` kann per Umgebungsvariable gesetzt werden.
- `FLASK_DEBUG` sollte im Deployment nicht auf `1` stehen.
- Für Linux-basierte Deployments kann `gunicorn app:app` verwendet werden.
- Die SQLite-Datei muss beim Deployment mitgeliefert oder vor dem Start per Import-Skript erzeugt werden.
