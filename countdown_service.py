import sqlite3
from datetime import datetime
from pathlib import Path

DB_NAME = Path(__file__).resolve().with_name("semester_dates.db")


def get_current_semester():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT semester_name, contact_start, contact_end, exam_start, exam_end
        FROM semester_dates
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "semester_name": row["semester_name"],
        "contact_start": row["contact_start"],
        "contact_end": row["contact_end"],
        "exam_start": row["exam_start"],
        "exam_end": row["exam_end"],
    }


def get_target_date(mode):
    semester = get_current_semester()

    if semester is None:
        raise ValueError("Keine Semesterdaten in der Datenbank gefunden.")

    if mode == "contact":
        return semester["contact_end"]
    elif mode == "exam":
        return semester["exam_end"]
    else:
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


def get_countdown(mode):
    semester = get_current_semester()

    if semester is None:
        raise ValueError("Keine aktuellen Semesterdaten in der Datenbank gefunden.")

    target_date = get_target_date(mode)
    countdown = calculate_countdown(target_date)

    return {
        "semester_name": semester["semester_name"],
        "mode": mode,
        "target_date": target_date,
        "countdown": countdown,
    }
