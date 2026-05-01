import re

import requests
from bs4 import BeautifulSoup

from app.scraper.common import (
    INFORMATIK,
    build_semester_record,
    clean_text,
    format_semester_name,
    normalize_for_matching,
    parse_numeric_date_range,
    parse_numeric_german_date,
)


SOURCE_URL = "https://www.hslu.ch/de-ch/informatik/studium/termine-studienjahr/"


def fetch_page_text():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HSLU-Informatik-Scraper/1.0)",
    }

    response = requests.get(SOURCE_URL, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding

    soup = BeautifulSoup(response.text, "html.parser")
    return clean_text(soup.get_text(" ", strip=True))


def strip_weekday_prefixes(text: str) -> str:
    return re.sub(r"\b(?:Mo|Di|Mi|Do|Fr|Sa|So)\s+", "", clean_text(text))


def parse_single_date(text: str):
    stripped = strip_weekday_prefixes(text)
    match = re.search(r"(\d{2}\.\d{2}\.\d{4})", stripped)
    if not match:
        return None

    return parse_numeric_german_date(match.group(1))


def parse_date_range_with_weekdays(text: str):
    stripped = strip_weekday_prefixes(text)
    return parse_numeric_date_range(stripped)


def extract_semester_data(page_text: str):
    page_text = normalize_for_matching(page_text)
    semester_pattern = re.compile(
        r"(Herbstsemester\s+\d{4}/\d{4}|Fruhlingssemester\s+\d{4})(.*?)(?=(Herbstsemester\s+\d{4}/\d{4}|Fruhlingssemester\s+\d{4}|Feiertage Studienjahr|$))",
        re.IGNORECASE | re.DOTALL,
    )

    semesters = []

    for match in semester_pattern.finditer(page_text):
        semester_name = format_semester_name(clean_text(match.group(1)))
        block = clean_text(match.group(2))

        contact_start_match = re.search(
            r"Beginn Kontaktstudium\s+((?:Mo|Di|Mi|Do|Fr|Sa|So)\s+\d{2}\.\d{2}\.\d{4})",
            block,
            re.IGNORECASE,
        )
        contact_end_match = re.search(
            r"Ende Kontaktstudium\s+((?:Mo|Di|Mi|Do|Fr|Sa|So)\s+\d{2}\.\d{2}\.\d{4})",
            block,
            re.IGNORECASE,
        )
        exam_range_match = re.search(
            r"Prufungsvorbereitung\s+((?:Mo|Di|Mi|Do|Fr|Sa|So)\s+\d{2}\.\d{2}\.\d{4}\s*[–-]\s*(?:Mo|Di|Mi|Do|Fr|Sa|So)\s+\d{2}\.\d{2}\.\d{4})",
            block,
            re.IGNORECASE,
        )

        if not contact_start_match or not contact_end_match or not exam_range_match:
            continue

        contact_start = parse_single_date(contact_start_match.group(1))
        contact_end = parse_single_date(contact_end_match.group(1))
        exam_range = parse_date_range_with_weekdays(exam_range_match.group(1))

        if not contact_start or not contact_end or not exam_range:
            continue

        semesters.append(
            build_semester_record(
                department_name=INFORMATIK,
                semester_name=semester_name,
                contact_start=contact_start,
                contact_end=contact_end,
                exam_start=exam_range["start"],
                exam_end=exam_range["end"],
                source_url=SOURCE_URL,
            )
        )

    return semesters


def scrape_semesters():
    return extract_semester_data(fetch_page_text())
