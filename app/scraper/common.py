import re
import unicodedata
from datetime import date, datetime


TECHNIK_ARCHITEKTUR = "Technik & Architektur"
WIRTSCHAFT = "Wirtschaft"
INFORMATIK = "Informatik"

MONTHS = {
    "januar": "01",
    "februar": "02",
    "marz": "03",
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


def normalize_for_matching(text: str) -> str:
    text = clean_text(text)
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(char for char in normalized if not unicodedata.combining(char))


def format_semester_name(semester_name: str) -> str:
    return semester_name.replace("Fruhlingssemester", "Frühlingssemester")


def build_semester_record(
    department_name: str,
    semester_name: str,
    contact_start: str,
    contact_end: str,
    exam_start: str,
    exam_end: str,
    source_url: str,
):
    return {
        "department_name": department_name,
        "semester_name": semester_name,
        "contact_start": contact_start,
        "contact_end": contact_end,
        "exam_start": exam_start,
        "exam_end": exam_end,
        "source_url": source_url,
    }


def parse_textual_german_date(date_str: str):
    date_str = normalize_for_matching(date_str)
    match = re.match(r"^(\d{1,2})\.\s+([A-Za-z]+)\s+(\d{4})$", date_str)
    if not match:
        return None

    day, month_name, year = match.groups()
    month = MONTHS.get(month_name.lower())
    if not month:
        return None

    return f"{year}-{month}-{int(day):02d}"


def parse_numeric_german_date(date_str: str):
    date_str = clean_text(date_str)
    match = re.match(r"^(\d{2})\.(\d{2})\.(\d{2,4})$", date_str)
    if not match:
        return None

    day, month, year = match.groups()
    if len(year) == 2:
        year = f"20{year}"

    return f"{year}-{month}-{day}"


def parse_textual_date_range(text: str):
    text = normalize_for_matching(text)
    match = re.search(
        r"(\d{1,2}\.\s+[A-Za-z]+(?:\s+\d{4})?)\s+bis\s+(\d{1,2}\.\s+[A-Za-z]+\s+\d{4})",
        text,
        re.IGNORECASE,
    )
    if not match:
        return None

    start_raw, end_raw = match.groups()
    if not re.search(r"\d{4}", start_raw):
        year_match = re.search(r"(\d{4})", end_raw)
        if year_match:
            start_raw = f"{start_raw} {year_match.group(1)}"

    start_iso = parse_textual_german_date(start_raw)
    end_iso = parse_textual_german_date(end_raw)
    if not start_iso or not end_iso:
        return None

    return {"start": start_iso, "end": end_iso}


def parse_numeric_date_range(text: str):
    text = clean_text(text)
    match = re.search(r"(\d{2}\.\d{2}\.\d{2,4})\s*[–-]\s*(\d{2}\.\d{2}\.\d{2,4})", text)
    if not match:
        return None

    start_iso = parse_numeric_german_date(match.group(1))
    end_iso = parse_numeric_german_date(match.group(2))
    if not start_iso or not end_iso:
        return None

    return {"start": start_iso, "end": end_iso}


def find_current_semester(semesters, today: date | None = None):
    today = today or datetime.now().date()

    for semester in semesters:
        contact_start = datetime.fromisoformat(semester["contact_start"]).date()
        exam_end = datetime.fromisoformat(semester["exam_end"]).date()
        if contact_start <= today <= exam_end:
            return semester

    return None


def find_relevant_semester(semesters, today: date | None = None):
    today = today or datetime.now().date()

    current_semester = find_current_semester(semesters, today)
    if current_semester:
        return current_semester

    upcoming_semesters = []
    past_semesters = []

    for semester in semesters:
        contact_start = datetime.fromisoformat(semester["contact_start"]).date()
        exam_end = datetime.fromisoformat(semester["exam_end"]).date()

        if contact_start > today:
            upcoming_semesters.append((contact_start, semester))
        else:
            past_semesters.append((exam_end, semester))

    if upcoming_semesters:
        upcoming_semesters.sort(key=lambda item: item[0])
        return upcoming_semesters[0][1]

    if past_semesters:
        past_semesters.sort(key=lambda item: item[0], reverse=True)
        return past_semesters[0][1]

    return None
