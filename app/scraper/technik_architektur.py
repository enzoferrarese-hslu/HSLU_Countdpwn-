import re

import requests
from bs4 import BeautifulSoup

from app.scraper.common import (
    TECHNIK_ARCHITEKTUR,
    build_semester_record,
    clean_text,
    format_semester_name,
    normalize_for_matching,
    parse_textual_date_range,
)


SOURCE_URL = "https://www.hslu.ch/de-ch/technik-architektur/studium/bachelor/wirtschaftsingenieur-innovation/"


def fetch_page_text():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HSLU-Scraper/1.0)",
    }

    response = requests.get(SOURCE_URL, headers=headers, timeout=30)
    response.raise_for_status()
    response.encoding = response.apparent_encoding or response.encoding

    soup = BeautifulSoup(response.text, "html.parser")
    return clean_text(soup.get_text(" ", strip=True))


def extract_semester_data(page_text: str):
    page_text = normalize_for_matching(page_text)
    semester_pattern = re.compile(
        r"(Herbstsemester\s+\d{4}(?:/\d{2,4})?|Fruhlingssemester\s+\d{4})(.*?)(?=(Herbstsemester\s+\d{4}(?:/\d{2,4})?|Fruhlingssemester\s+\d{4}|$))",
        re.IGNORECASE | re.DOTALL,
    )

    semesters = []

    for match in semester_pattern.finditer(page_text):
        semester_name = format_semester_name(clean_text(match.group(1)))
        block = clean_text(match.group(2))

        contact_match = re.search(
            r"Kontaktstudium:\s*(.*?)(?=Prufungsphase|Weihnachtsferien|Osterferien|Sommerferien|Blockwochen|$)",
            block,
            re.IGNORECASE | re.DOTALL,
        )
        exam_match = re.search(
            r"Prufungsphase(?:\s*\([^)]*\))?:\s*(.*?)(?=Weihnachtsferien|Osterferien|Sommerferien|Blockwochen|$)",
            block,
            re.IGNORECASE | re.DOTALL,
        )

        if not contact_match or not exam_match:
            continue

        contact_range = parse_textual_date_range(contact_match.group(1))
        exam_range = parse_textual_date_range(exam_match.group(1))
        if not contact_range or not exam_range:
            continue

        semesters.append(
            build_semester_record(
                department_name=TECHNIK_ARCHITEKTUR,
                semester_name=semester_name,
                contact_start=contact_range["start"],
                contact_end=contact_range["end"],
                exam_start=exam_range["start"],
                exam_end=exam_range["end"],
                source_url=SOURCE_URL,
            )
        )

    return semesters


def scrape_semesters():
    return extract_semester_data(fetch_page_text())
