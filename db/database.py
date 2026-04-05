import sqlite3
from pathlib import Path

ALLOWED_STATUSES = (
    "draft", "tailoring", "ready", "approved", "submitting",
    "submitted", "viewed", "response", "interview", "offer",
    "rejected", "failed", "skipped",
)

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


class Database:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    def init(self) -> "Database":
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        schema = SCHEMA_PATH.read_text()
        self._conn.executescript(schema)
        self._conn.commit()
        return self

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Database not initialised — call .init() first")
        return self._conn

    def list_tables(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        return [r["name"] for r in rows]

    # ------------------------------------------------------------------
    # Jobs
    # ------------------------------------------------------------------

    def insert_job(
        self,
        title: str,
        company: str,
        url: str,
        description: str | None = None,
        source: str = "linkedin",
        location: str | None = None,
        salary_range: str | None = None,
        employment_type: str | None = None,
        match_score: int | None = None,
        match_analysis: str | None = None,
        easy_apply: bool = True,
    ) -> int:
        cur = self.conn.execute(
            """
            INSERT INTO jobs
                (title, company, url, description, source, location,
                 salary_range, employment_type, match_score, match_analysis, easy_apply)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (title, company, url, description, source, location,
             salary_range, employment_type, match_score, match_analysis, int(easy_apply)),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_job(self, job_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM jobs WHERE id = ?", (job_id,)
        ).fetchone()

    def get_jobs(self, source: str | None = None, limit: int = 100) -> list[sqlite3.Row]:
        if source:
            rows = self.conn.execute(
                "SELECT * FROM jobs WHERE source = ? LIMIT ?", (source, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM jobs LIMIT ?", (limit,)
            ).fetchall()
        return rows

    def job_exists(self, url: str) -> bool:
        row = self.conn.execute(
            "SELECT 1 FROM jobs WHERE url = ?", (url,)
        ).fetchone()
        return row is not None

    # ------------------------------------------------------------------
    # Applications
    # ------------------------------------------------------------------

    def create_application(self, job_id: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO applications (job_id) VALUES (?)", (job_id,)
        )
        self.conn.commit()
        return cur.lastrowid

    def get_application(self, app_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()

    def get_applications(
        self, status: str | None = None, limit: int = 100
    ) -> list[sqlite3.Row]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM applications WHERE status = ? LIMIT ?", (status, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM applications LIMIT ?", (limit,)
            ).fetchall()
        return rows

    def update_application_status(self, app_id: int, status: str):
        if status not in ALLOWED_STATUSES:
            raise ValueError(
                f"Invalid status '{status}'. Allowed: {ALLOWED_STATUSES}"
            )
        if status == "submitted":
            self.conn.execute(
                """
                UPDATE applications
                SET status = ?, applied_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, app_id),
            )
        else:
            self.conn.execute(
                """
                UPDATE applications
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, app_id),
            )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Resumes
    # ------------------------------------------------------------------

    def insert_resume(
        self, job_id: int, tex_source: str, is_tailored: bool = True
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO resumes (job_id, tex_source, is_tailored) VALUES (?, ?, ?)",
            (job_id, tex_source, int(is_tailored)),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_resume(self, resume_id: int) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM resumes WHERE id = ?", (resume_id,)
        ).fetchone()

    def approve_resume(self, resume_id: int, pdf_path: str):
        self.conn.execute(
            "UPDATE resumes SET approved = 1, pdf_path = ? WHERE id = ?",
            (pdf_path, resume_id),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    def log_event(
        self, application_id: int, event_type: str, details: str | None = None
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO events (application_id, event_type, details) VALUES (?, ?, ?)",
            (application_id, event_type, details),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_events(self, application_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM events WHERE application_id = ? ORDER BY timestamp",
            (application_id,),
        ).fetchall()

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_stats(self) -> dict:
        total_jobs = self.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        total_applications = self.conn.execute(
            "SELECT COUNT(*) FROM applications"
        ).fetchone()[0]
        avg_row = self.conn.execute(
            "SELECT AVG(match_score) FROM jobs WHERE match_score IS NOT NULL"
        ).fetchone()
        avg_match_score = avg_row[0]

        status_rows = self.conn.execute(
            "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"
        ).fetchall()
        status_counts = {r["status"]: r["cnt"] for r in status_rows}

        return {
            "total_jobs": total_jobs,
            "total_applications": total_applications,
            "avg_match_score": avg_match_score,
            "status_counts": status_counts,
        }
