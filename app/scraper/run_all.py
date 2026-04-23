from collections import defaultdict

from app.database.db import init_db, upsert_semesters, wait_for_db
from app.scraper.common import find_current_semester
from app.scraper.technik_architektur import scrape_semesters as scrape_technik_architektur
from app.scraper.wirtschaft_pdf import scrape_semesters as scrape_wirtschaft


SCRAPERS = [
    ("Technik & Architektur", scrape_technik_architektur),
    ("Wirtschaft", scrape_wirtschaft),
]


def main():
    print("Warte auf PostgreSQL...")
    wait_for_db()

    print("Initialisiere Datenbank...")
    init_db()

    all_semesters = []
    errors = []

    for label, scraper in SCRAPERS:
        print(f"Starte Scraper fuer {label}...")
        try:
            semesters = scraper()
            if not semesters:
                raise RuntimeError(f"Keine Semesterdaten fuer {label} gefunden.")
            all_semesters.extend(semesters)
            print(f"{label}: {len(semesters)} Semester gefunden.")
        except Exception as error:
            errors.append((label, error))
            print(f"Warnung: {label} konnte nicht gescrapt werden: {error}")

    if not all_semesters:
        raise RuntimeError("Kein Scraper konnte Semesterdaten liefern.")

    print("Speichere Semesterdaten in PostgreSQL...")
    upsert_semesters(all_semesters)

    by_department = defaultdict(list)
    for semester in all_semesters:
        by_department[semester["department_name"]].append(semester)

    for department_name, semesters in by_department.items():
        current = find_current_semester(semesters)
        if current:
            print(
                f"{department_name}: aktuelles Semester {current['semester_name']} "
                f"({current['contact_start']} bis {current['exam_end']})"
            )
        else:
            print(f"{department_name}: kein aktuelles Semester im gescrapten Datensatz gefunden.")

    if errors:
        print("Scraperlauf mit Warnungen abgeschlossen:")
        for label, error in errors:
            print(f"- {label}: {error}")


if __name__ == "__main__":
    main()
