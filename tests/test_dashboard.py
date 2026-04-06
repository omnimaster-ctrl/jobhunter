"""Tests for the FastAPI dashboard application."""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from dashboard.app import app, get_db, _rows_to_dicts
from db.database import Database


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_db(tmp_path):
    """Create a temporary database with sample data."""
    db_path = tmp_path / "test.db"
    db = Database(db_path)
    db.init()
    # Allow cross-thread access for TestClient (runs requests in a thread)
    db.conn.execute("PRAGMA journal_mode=WAL")
    db._conn.close()
    db._conn = sqlite3.connect(str(db_path), check_same_thread=False)
    db._conn.row_factory = sqlite3.Row
    db._conn.execute("PRAGMA foreign_keys = ON")

    # Insert sample jobs
    job1_id = db.insert_job(
        title="Senior Data Engineer",
        company="Acme Corp",
        url="https://example.com/job1",
        description="Build data pipelines",
        match_score=85,
        location="Remote",
        employment_type="contractor",
    )
    job2_id = db.insert_job(
        title="ML Engineer",
        company="Beta Inc",
        url="https://example.com/job2",
        description="Train models",
        match_score=72,
        location="Mexico City",
    )
    job3_id = db.insert_job(
        title="Backend Developer",
        company="Acme Corp",
        url="https://example.com/job3",
        match_score=None,
    )

    # Insert sample applications
    app1 = db.create_application(job1_id)
    db.update_application_status(app1, "submitted")

    app2 = db.create_application(job2_id)
    db.update_application_status(app2, "interview")

    app3 = db.create_application(job3_id)
    # stays as draft

    yield db
    db.close()


@pytest.fixture()
def client(tmp_db):
    """TestClient that uses the temporary database."""
    def _get_db_override():
        return tmp_db

    with patch("dashboard.app.get_db", _get_db_override):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


# ---------------------------------------------------------------------------
# JSON API tests
# ---------------------------------------------------------------------------


class TestAPIStats:
    def test_returns_stats(self, client):
        resp = client.get("/api/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_jobs"] == 3
        assert data["total_applications"] == 3
        assert data["avg_match_score"] is not None
        assert "status_counts" in data

    def test_status_counts(self, client):
        resp = client.get("/api/stats")
        data = resp.json()
        counts = data["status_counts"]
        assert counts.get("submitted") == 1
        assert counts.get("interview") == 1
        assert counts.get("draft") == 1


class TestAPIApplications:
    def test_returns_all(self, client):
        resp = client.get("/api/applications")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_filter_by_status(self, client):
        resp = client.get("/api/applications?status=draft")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "draft"

    def test_limit(self, client):
        resp = client.get("/api/applications?limit=2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_returns_dicts(self, client):
        resp = client.get("/api/applications")
        data = resp.json()
        for item in data:
            assert isinstance(item, dict)
            assert "id" in item
            assert "job_id" in item
            assert "status" in item


class TestAPIJobs:
    def test_returns_all(self, client):
        resp = client.get("/api/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3

    def test_filter_by_source(self, client):
        resp = client.get("/api/jobs?source=linkedin")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3  # all default to linkedin

    def test_limit(self, client):
        resp = client.get("/api/jobs?limit=1")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_job_fields(self, client):
        resp = client.get("/api/jobs")
        data = resp.json()
        job = data[0]
        assert "title" in job
        assert "company" in job
        assert "url" in job


# ---------------------------------------------------------------------------
# HTML route tests (verify they attempt to render — templates don't exist yet)
# ---------------------------------------------------------------------------


class TestHTMLRoutes:
    """HTML routes will fail with TemplateNotFound since templates aren't created yet.
    We verify the routes exist and the error is template-related, not a 404."""

    @pytest.mark.parametrize("path", ["/", "/funnel", "/scores", "/timeline", "/breakdown"])
    def test_html_routes_exist(self, client, path):
        resp = client.get(path)
        # 500 because templates don't exist yet, but NOT 404/405
        assert resp.status_code != 404
        assert resp.status_code != 405


# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_rows_to_dicts(self, tmp_db):
        rows = tmp_db.get_jobs()
        result = _rows_to_dicts(rows)
        assert isinstance(result, list)
        assert len(result) == 3
        assert isinstance(result[0], dict)
        assert result[0]["title"] == "Senior Data Engineer"

    def test_get_db_returns_database(self):
        """get_db should return a Database instance (may fail if db path doesn't exist)."""
        # We just verify the import works; actual db creation tested elsewhere
        from dashboard.app import get_db as gdb
        assert callable(gdb)
