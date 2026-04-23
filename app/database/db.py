import os
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.scraper.common import TECHNIK_ARCHITEKTUR


DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/semester_countdown"
DEFAULT_SQLITE_MIRROR_PATH = Path(__file__).resolve().parents[2] / "data" / "semester_dates.db"


def get_database_url():
    return os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_sqlite_mirror_path():
    return Path(os.environ.get("SQLITE_MIRROR_PATH", str(DEFAULT_SQLITE_MIRROR_PATH)))


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
                department_name TEXT,
                semester_name TEXT NOT NULL,
                contact_start DATE NOT NULL,
                contact_end DATE NOT NULL,
                exam_start DATE NOT NULL,
                exam_end DATE NOT NULL,
                source_url TEXT NOT NULL,
                scraped_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        conn.execute("ALTER TABLE semester_dates ADD COLUMN IF NOT EXISTS department_name TEXT")
        conn.execute(
            """
            UPDATE semester_dates
            SET department_name = %s
            WHERE department_name IS NULL
            """,
            (TECHNIK_ARCHITEKTUR,),
        )
        conn.execute("ALTER TABLE semester_dates ALTER COLUMN department_name SET NOT NULL")
        conn.execute("ALTER TABLE semester_dates DROP CONSTRAINT IF EXISTS semester_dates_semester_name_key")
        conn.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS semester_dates_department_semester_idx
            ON semester_dates (department_name, semester_name)
            """
        )
        conn.commit()


def fetch_current_semester(department_name=TECHNIK_ARCHITEKTUR):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT department_name, semester_name, contact_start, contact_end, exam_start, exam_end, source_url
            FROM semester_dates
            WHERE department_name = %s
              AND contact_start <= CURRENT_DATE
              AND exam_end >= CURRENT_DATE
            ORDER BY contact_start DESC, scraped_at DESC
            LIMIT 1
            """,
            (department_name,),
        ).fetchone()

        if row is None:
            row = conn.execute(
                """
                SELECT department_name, semester_name, contact_start, contact_end, exam_start, exam_end, source_url
                FROM semester_dates
                WHERE department_name = %s
                ORDER BY exam_end DESC, scraped_at DESC
                LIMIT 1
                """,
                (department_name,),
            ).fetchone()

    if row is None:
        return None

    return {
        "department_name": row["department_name"],
        "semester_name": row["semester_name"],
        "contact_start": row["contact_start"].isoformat(),
        "contact_end": row["contact_end"].isoformat(),
        "exam_start": row["exam_start"].isoformat(),
        "exam_end": row["exam_end"].isoformat(),
        "source_url": row["source_url"],
    }


def replace_current_semesters(semesters):
    with get_connection() as conn:
        with conn.transaction():
            departments = sorted({semester["department_name"] for semester in semesters})
            for department_name in departments:
                conn.execute(
                    "DELETE FROM semester_dates WHERE department_name = %s",
                    (department_name,),
                )

            for semester in semesters:
                scraped_at = datetime.now(timezone.utc)
                conn.execute(
                    """
                    INSERT INTO semester_dates (
                        department_name,
                        semester_name,
                        contact_start,
                        contact_end,
                        exam_start,
                        exam_end,
                        source_url,
                        scraped_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        semester["department_name"],
                        semester["semester_name"],
                        semester["contact_start"],
                        semester["contact_end"],
                        semester["exam_start"],
                        semester["exam_end"],
                        semester["source_url"],
                        scraped_at,
                    ),
                )


def mirror_semesters_to_sqlite(semesters):
    sqlite_path = get_sqlite_mirror_path()
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    if sqlite_path.exists():
        sqlite_path.unlink()

    with sqlite3.connect(sqlite_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS semester_dates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                department_name TEXT NOT NULL,
                semester_name TEXT NOT NULL,
                contact_start TEXT NOT NULL,
                contact_end TEXT NOT NULL,
                exam_start TEXT NOT NULL,
                exam_end TEXT NOT NULL,
                source_url TEXT NOT NULL,
                scraped_at TEXT NOT NULL
            )
            """
        )

        rows = []
        for semester in semesters:
            rows.append(
                (
                    semester["department_name"],
                    semester["semester_name"],
                    semester["contact_start"],
                    semester["contact_end"],
                    semester["exam_start"],
                    semester["exam_end"],
                    semester["source_url"],
                    datetime.now(timezone.utc).isoformat(),
                )
            )

        conn.executemany(
            """
            INSERT INTO semester_dates (
                department_name,
                semester_name,
                contact_start,
                contact_end,
                exam_start,
                exam_end,
                source_url,
                scraped_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
