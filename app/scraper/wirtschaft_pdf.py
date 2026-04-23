import re
from datetime import datetime
from io import BytesIO

import requests
from pypdf import PdfReader

from app.scraper.common import (
    WIRTSCHAFT,
    build_semester_record,
    clean_text,
    format_semester_name,
    normalize_for_matching,
    parse_numeric_date_range,
)


PDF_URL_TEMPLATE = "https://www.hslu.ch/-/media/campus/common/files/dokumente/w/studium/bsc-in-business-administration/eckdaten-bachelor-{study_year}.pdf?sc_lang=de-ch"


def build_candidate_urls(reference_date=None):
    reference_date = reference_date or datetime.now().date()
    years = [reference_date.year - 1, reference_date.year, reference_date.year + 1]

    urls = []
    for start_year in years:
        study_year = f"{str(start_year)[-2:]}{str(start_year + 1)[-2:]}"
        urls.append(PDF_URL_TEMPLATE.format(study_year=study_year))

    return urls


def fetch_pdf_text(url: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; HSLU-PDF-Scraper/1.0)",
    }

    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    reader = PdfReader(BytesIO(response.content))
    page_texts = []
    for page in reader.pages:
        page_texts.append(page.extract_text() or "")

    return clean_text(" ".join(page_texts))


def build_single_day_range(date_text: str):
    return parse_numeric_date_range(f"{date_text} - {date_text}")


def extract_semesters_from_pdf(pdf_text: str, source_url: str):
    text = normalize_for_matching(pdf_text)

    semester_specs = [
        (
            "Herbstsemester",
            r"Beginn Herbstsemester (\d{4})",
            r"Beginn Herbstsemester \d{4}\s+(\d{2}\.\d{2}\.\d{2,4})",
            r"Ende Kontaktstudium Herbstsemester \d{4}\s+(\d{2}\.\d{2}\.\d{2,4})",
            r"Modulprufungen Herbstsemester \d{4}\s+(\d{2}\.\d{2}\.\d{2,4}\s*[–-]\s*\d{2}\.\d{2}\.\d{2,4})",
        ),
        (
            "Frühlingssemester",
            r"Beginn Fruhlingssemester (\d{4})",
            r"Beginn Fruhlingssemester \d{4}\s+(\d{2}\.\d{2}\.\d{2,4})",
            r"Ende Kontaktstudium Fruhlingssemester \d{4}\s+(\d{2}\.\d{2}\.\d{2,4})",
            r"Modulprufungen Fruhlingssemester \d{4}\s+(\d{2}\.\d{2}\.\d{2,4}\s*[–-]\s*\d{2}\.\d{2}\.\d{2,4})",
        ),
    ]

    semesters = []

    for label, year_pattern, start_pattern, contact_end_pattern, exam_pattern in semester_specs:
        year_match = re.search(year_pattern, text)
        start_match = re.search(start_pattern, text)
        contact_end_match = re.search(contact_end_pattern, text)
        exam_match = re.search(exam_pattern, text)

        if not year_match or not start_match or not contact_end_match or not exam_match:
            continue

        contact_start = build_single_day_range(start_match.group(1))
        contact_end = build_single_day_range(contact_end_match.group(1))
        exam_range = parse_numeric_date_range(exam_match.group(1))

        if not contact_start or not contact_end or not exam_range:
            continue

        semester_name = format_semester_name(f"{label} {year_match.group(1)}")
        semesters.append(
            build_semester_record(
                department_name=WIRTSCHAFT,
                semester_name=semester_name,
                contact_start=contact_start["start"],
                contact_end=contact_end["start"],
                exam_start=exam_range["start"],
                exam_end=exam_range["end"],
                source_url=source_url,
            )
        )

    return semesters


def scrape_semesters(reference_date=None):
    all_semesters = []

    for url in build_candidate_urls(reference_date):
        try:
            pdf_text = fetch_pdf_text(url)
        except requests.HTTPError as error:
            if error.response is not None and error.response.status_code == 404:
                continue
            raise

        all_semesters.extend(extract_semesters_from_pdf(pdf_text, url))

    deduplicated = {}
    for semester in all_semesters:
        key = (semester["department_name"], semester["semester_name"])
        deduplicated[key] = semester

    return list(deduplicated.values())
