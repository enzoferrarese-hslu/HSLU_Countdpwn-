from datetime import datetime

from app.database.db import fetch_current_semester
from app.scraper.common import TECHNIK_ARCHITEKTUR


def get_current_semester(department_name=TECHNIK_ARCHITEKTUR):
    return fetch_current_semester(department_name)


def get_target_date(mode, department_name=TECHNIK_ARCHITEKTUR):
    semester = get_current_semester(department_name)

    if semester is None:
        raise ValueError("Keine Semesterdaten in der Datenbank gefunden.")

    if mode == "contact":
        return semester["contact_end"]
    if mode == "exam":
        return semester["exam_end"]

    raise ValueError("Ungültiger Modus. Verwende 'contact' oder 'exam'.")


def calculate_countdown(target_date_str):
    now = datetime.now()

    target_datetime = datetime.strptime(target_date_str, "%Y-%m-%d")
    target_datetime = target_datetime.replace(hour=23, minute=59, second=59)

    delta = target_datetime - now
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return {
            "expired": True,
            "total_seconds": 0,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
        }

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return {
        "expired": False,
        "total_seconds": total_seconds,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
    }


def get_countdown(mode, department_name=TECHNIK_ARCHITEKTUR):
    semester = get_current_semester(department_name)

    if semester is None:
        raise ValueError("Keine aktuellen Semesterdaten in der Datenbank gefunden.")

    target_date = get_target_date(mode, department_name)
    countdown = calculate_countdown(target_date)

    return {
        "department_name": semester["department_name"],
        "semester_name": semester["semester_name"],
        "mode": mode,
        "target_date": target_date,
        "countdown": countdown,
    }
