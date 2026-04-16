import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from db import init_db, replace_current_semester, wait_for_db

URL = "https://www.hslu.ch/de-ch/technik-architektur/studium/bachelor/wirtschaftsingenieur-innovation/"

MONTHS = {
    "januar": "01",
    "februar": "02",
    "märz": "03",
    "april": "04",
    "mai": "05",
    "juni": "06",
    "juli": "07",
    "august": "08",
    "september": "09",
    "oktober": "10",
    "november": "11",
    "dezember": "12",
}


def clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def german_date_to_iso(date_str: str):
    date_str = clean_text(date_str)
    match = re.match(r"^(\d{1,2})\.\s+([A-Za-zäöüÄÖÜ]+)\s+(\d{4})$", date_str)
    if not match:
        return None

    day, month_name, year = match.groups()
    month = MONTHS.get(month_name.lower())

    if not month:
        return None

    return f"{year}-{month}-{int(day):02d}"


def parse_date_range(text: str):
    text = clean_text(text)

    match = re.search(
        r"(\d{1,2}\.\s+[A-Za-zäöüÄÖÜ]+(?:\s+\d{4})?)\s+bis\s+(\d{1,2}\.\s+[A-Za-zäöüÄÖÜ]+\s+\d{4})",
        text,
        re.IGNORECASE
    )

    if not match:
        return None

    start_raw, end_raw = match.groups()

    if not re.search(r"\d{4}", start_raw):
        year_match = re.search(r"(\d{4})", end_raw)
        if year_match:
            start_raw = f"{start_raw} {year_match.group(1)}"

    start_iso = german_date_to_iso(start_raw)
    end_iso = german_date_to_iso(end_raw)

    if not start_iso or not end_iso:
        return None

    return {
        "start": start_iso,
        "end": end_iso
    }


def fetch_page_text():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HSLU-Scraper/1.0)"
    }

    response = requests.get(URL, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    return clean_text(text)


def extract_semester_data(page_text: str):
    semester_pattern = re.compile(
        r"(Herbstsemester\s+\d{4}(?:/\d{2,4})?|Frühlingssemester\s+\d{4})(.*?)(?=(Herbstsemester\s+\d{4}(?:/\d{2,4})?|Frühlingssemester\s+\d{4}|$))",
        re.IGNORECASE | re.DOTALL
    )

    semesters = []

    for match in semester_pattern.finditer(page_text):
        semester_name = clean_text(match.group(1))
        block = clean_text(match.group(2))

        contact_match = re.search(
            r"Kontaktstudium:\s*(.*?)(?=Prüfungsphase|Weihnachtsferien|Osterferien|Sommerferien|Blockwochen|$)",
            block,
            re.IGNORECASE | re.DOTALL
        )

        exam_match = re.search(
            r"Prüfungsphase(?:\s*\([^)]*\))?:\s*(.*?)(?=Weihnachtsferien|Osterferien|Sommerferien|Blockwochen|$)",
            block,
            re.IGNORECASE | re.DOTALL
        )

        if not contact_match or not exam_match:
            continue

        contact_range = parse_date_range(contact_match.group(1))
        exam_range = parse_date_range(exam_match.group(1))

        if not contact_range or not exam_range:
            continue

        semesters.append({
            "semester_name": semester_name,
            "contact_start": contact_range["start"],
            "contact_end": contact_range["end"],
            "exam_start": exam_range["start"],
            "exam_end": exam_range["end"],
        })

    return semesters


def get_current_semester(data):
    today = datetime.now().date()

    for semester in data:
        contact_start = datetime.fromisoformat(semester["contact_start"]).date()
        exam_end = datetime.fromisoformat(semester["exam_end"]).date()

        if contact_start <= today <= exam_end:
            return semester

    return None


def save_to_db(semester):
    replace_current_semester(semester, URL)

def print_current_semester(semester):
    print("\nAKTUELLES SEMESTER:\n")
    print(f"Semester: {semester['semester_name']}")
    print(f"Kontaktstudium: {semester['contact_start']} bis {semester['contact_end']}")
    print(f"Prüfungsphase: {semester['exam_start']} bis {semester['exam_end']}")
    print("-" * 50)


def main():
    print("Warte auf PostgreSQL...")
    wait_for_db()

    print("Initialisiere Datenbank...")
    init_db()

    print("Lade HTML-Seite...")
    page_text = fetch_page_text()

    print("Extrahiere Semesterdaten...")
    semester_data = extract_semester_data(page_text)

    if not semester_data:
        print("Es konnten keine Semesterdaten gefunden werden.")
        return

    current_semester = get_current_semester(semester_data)

    if not current_semester:
        print("Kein aktuelles Semester gefunden.")
        return

    print("Speichere aktuelles Semester in PostgreSQL...")
    save_to_db(current_semester)

    print("Fertig.")
    print_current_semester(current_semester)


if __name__ == "__main__":
    main()
