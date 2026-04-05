import pytest
import sqlite3
from pathlib import Path
from db.database import Database


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db(tmp_path):
    database = Database(tmp_path / "test.db")
    database.init()
    yield database
    database.close()


def _make_job(db: Database, url: str = "https://example.com/job/1") -> int:
    return db.insert_job(
        title="Software Engineer",
        company="Acme Corp",
        url=url,
        description="Build cool stuff",
        source="linkedin",
    )


def _make_application(db: Database, job_id: int | None = None) -> int:
    if job_id is None:
        job_id = _make_job(db)
    return db.create_application(job_id)


# ---------------------------------------------------------------------------
# TestDatabaseInit
# ---------------------------------------------------------------------------

class TestDatabaseInit:
    def test_creates_database_file(self, tmp_path):
        db_path = tmp_path / "new.db"
        db = Database(db_path)
        db.init()
        assert db_path.exists()
        db.close()

    def test_creates_all_tables(self, db):
        tables = set(db.list_tables())
        assert {"jobs", "applications", "resumes", "events"}.issubset(tables)


# ---------------------------------------------------------------------------
# TestJobsCRUD
# ---------------------------------------------------------------------------

class TestJobsCRUD:
    def test_insert_job(self, db):
        job_id = _make_job(db)
        assert isinstance(job_id, int)
        assert job_id > 0

    def test_get_job_by_id(self, db):
        job_id = _make_job(db)
        job = db.get_job(job_id)
        assert job is not None
        assert job["title"] == "Software Engineer"
        assert job["company"] == "Acme Corp"

    def test_duplicate_url_raises(self, db):
        _make_job(db, url="https://example.com/job/dup")
        with pytest.raises(sqlite3.IntegrityError):
            _make_job(db, url="https://example.com/job/dup")

    def test_get_jobs_by_source(self, db):
        db.insert_job(title="A", company="X", url="https://a.com", source="linkedin")
        db.insert_job(title="B", company="Y", url="https://b.com", source="indeed")
        linkedin_jobs = db.get_jobs(source="linkedin")
        assert all(j["source"] == "linkedin" for j in linkedin_jobs)
        assert len(linkedin_jobs) >= 1

    def test_job_exists_by_url(self, db):
        url = "https://example.com/job/exists"
        assert not db.job_exists(url)
        _make_job(db, url=url)
        assert db.job_exists(url)


# ---------------------------------------------------------------------------
# TestApplicationsCRUD
# ---------------------------------------------------------------------------

class TestApplicationsCRUD:
    def test_create_application(self, db):
        job_id = _make_job(db)
        app_id = db.create_application(job_id)
        assert isinstance(app_id, int)
        app = db.get_application(app_id)
        assert app is not None
        assert app["job_id"] == job_id
        assert app["status"] == "draft"

    def test_update_application_status(self, db):
        app_id = _make_application(db)
        db.update_application_status(app_id, "ready")
        app = db.get_application(app_id)
        assert app["status"] == "ready"

    def test_invalid_status_raises(self, db):
        app_id = _make_application(db)
        with pytest.raises(ValueError):
            db.update_application_status(app_id, "not_a_real_status")

    def test_get_applications_by_status(self, db):
        app_id = _make_application(db)
        db.update_application_status(app_id, "ready")
        results = db.get_applications(status="ready")
        assert len(results) >= 1
        assert all(r["status"] == "ready" for r in results)


# ---------------------------------------------------------------------------
# TestResumesCRUD
# ---------------------------------------------------------------------------

class TestResumesCRUD:
    def test_insert_resume(self, db):
        job_id = _make_job(db)
        resume_id = db.insert_resume(job_id, tex_source=r"\documentclass{article}")
        assert isinstance(resume_id, int)
        resume = db.get_resume(resume_id)
        assert resume is not None
        assert resume["job_id"] == job_id
        assert resume["approved"] == 0

    def test_approve_resume(self, db):
        job_id = _make_job(db)
        resume_id = db.insert_resume(job_id, tex_source=r"\documentclass{article}")
        db.approve_resume(resume_id, pdf_path="/tmp/resume.pdf")
        resume = db.get_resume(resume_id)
        assert resume["approved"] == 1
        assert resume["pdf_path"] == "/tmp/resume.pdf"


# ---------------------------------------------------------------------------
# TestEventsCRUD
# ---------------------------------------------------------------------------

class TestEventsCRUD:
    def test_log_event(self, db):
        app_id = _make_application(db)
        event_id = db.log_event(app_id, "status_change", details="draft -> ready")
        assert isinstance(event_id, int)

    def test_get_events_for_application(self, db):
        app_id = _make_application(db)
        db.log_event(app_id, "status_change", details="draft -> ready")
        db.log_event(app_id, "email_received", details="Recruiter reached out")
        events = db.get_events(app_id)
        assert len(events) == 2
        assert events[0]["event_type"] == "status_change"
        assert events[1]["event_type"] == "email_received"


# ---------------------------------------------------------------------------
# TestAnalyticsQueries
# ---------------------------------------------------------------------------

class TestAnalyticsQueries:
    def test_get_stats(self, db):
        job_id = _make_job(db)
        db.insert_job(
            title="Senior Engineer", company="Beta", url="https://beta.com",
            match_score=85
        )
        app_id = _make_application(db, job_id=job_id)
        db.update_application_status(app_id, "submitted")

        stats = db.get_stats()
        assert stats["total_jobs"] >= 2
        assert stats["total_applications"] >= 1
        assert stats["avg_match_score"] == 85.0
        assert "submitted" in stats["status_counts"]
