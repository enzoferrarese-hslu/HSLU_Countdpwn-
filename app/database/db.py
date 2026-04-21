import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/semester_countdown"


def get_database_url():
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


@contextmanager
def get_connection():
    conn = psycopg.connect(get_database_url(), row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()


def wait_for_db(max_attempts=30, delay_seconds=2):
    last_error = None

    for _ in range(max_attempts):
        try:
            with get_connection() as conn:
                conn.execute("SELECT 1")
                return
        except psycopg.OperationalError as error:
            last_error = error
            time.sleep(delay_seconds)

    raise RuntimeError("PostgreSQL ist nicht erreichbar.") from last_error


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS semester_dates (
                id SERIAL PRIMARY KEY,
                semester_name TEXT NOT NULL UNIQUE,
                contact_start DATE NOT NULL,
                contact_end DATE NOT NULL,
                exam_start DATE NOT NULL,
                exam_end DATE NOT NULL,
                source_url TEXT NOT NULL,
                scraped_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        conn.commit()


def fetch_current_semester():
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT semester_name, contact_start, contact_end, exam_start, exam_end
            FROM semester_dates
            ORDER BY scraped_at DESC
            LIMIT 1
            """
        ).fetchone()

    if row is None:
        return None

    return {
        "semester_name": row["semester_name"],
        "contact_start": row["contact_start"].isoformat(),
        "contact_end": row["contact_end"].isoformat(),
        "exam_start": row["exam_start"].isoformat(),
        "exam_end": row["exam_end"].isoformat(),
    }


def replace_current_semester(semester, source_url):
    scraped_at = datetime.now(timezone.utc)

    with get_connection() as conn:
        with conn.transaction():
            conn.execute("DELETE FROM semester_dates")
            conn.execute(
                """
                INSERT INTO semester_dates (
                    semester_name,
                    contact_start,
                    contact_end,
                    exam_start,
                    exam_end,
                    source_url,
                    scraped_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    semester["semester_name"],
                    semester["contact_start"],
                    semester["contact_end"],
                    semester["exam_start"],
                    semester["exam_end"],
                    source_url,
                    scraped_at,
                ),
            )
