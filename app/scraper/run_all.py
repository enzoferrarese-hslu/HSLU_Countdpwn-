from collections import defaultdict

from app.database.db import init_db, mirror_semesters_to_sqlite, replace_current_semesters, wait_for_db
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

    current_semesters = []
    errors = []

    for label, scraper in SCRAPERS:
        print(f"Starte Scraper fuer {label}...")
        try:
            semesters = scraper()
            if not semesters:
                raise RuntimeError(f"Keine Semesterdaten fuer {label} gefunden.")
            print(f"{label}: {len(semesters)} Semester gefunden.")

            current_semester = find_current_semester(semesters)
            if not current_semester:
                raise RuntimeError(f"Kein aktuelles Semester fuer {label} gefunden.")

            current_semesters.append(current_semester)
            print(
                f"{label}: aktuelles Semester {current_semester['semester_name']} "
                f"({current_semester['contact_start']} bis {current_semester['exam_end']})"
            )
        except Exception as error:
            errors.append((label, error))
            print(f"Warnung: {label} konnte nicht gescrapt werden: {error}")

    if not current_semesters:
        raise RuntimeError("Kein Scraper konnte Semesterdaten liefern.")

    print("Speichere aktuelle Semesterdaten in PostgreSQL...")
    replace_current_semesters(current_semesters)

    print("Aktualisiere lokalen SQLite-Spiegel...")
    mirror_semesters_to_sqlite(current_semesters)

    by_department = defaultdict(list)
    for semester in current_semesters:
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
