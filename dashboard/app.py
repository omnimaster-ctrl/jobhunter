"""FastAPI dashboard for JobHunter analytics."""

from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config.loader import Config
from db.database import Database

_DIR = Path(__file__).parent
_TEMPLATES_DIR = _DIR / "templates"
_STATIC_DIR = _DIR / "static"
_DB_PATH = Path.home() / ".jobhunter" / "db" / "jobhunter.db"

app = FastAPI(title="JobHunter Dashboard")

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))

if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_config() -> Config:
    """Return a Config instance."""
    return Config()


def get_db() -> Database:
    """Return an initialised Database instance."""
    db = Database(_DB_PATH)
    db.init()
    return db


def _rows_to_dicts(rows) -> list[dict]:
    """Convert sqlite3.Row objects to plain dicts."""
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# HTML routes (render Jinja2 templates)
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def overview(request: Request):
    db = get_db()
    try:
        stats = db.get_stats()
        return templates.TemplateResponse(
            request, "overview.html", {"stats": stats}
        )
    finally:
        db.close()


@app.get("/funnel", response_class=HTMLResponse)
async def funnel(request: Request):
    db = get_db()
    try:
        stats = db.get_stats()
        return templates.TemplateResponse(
            request, "funnel.html", {"status_counts": stats["status_counts"]}
        )
    finally:
        db.close()


@app.get("/scores", response_class=HTMLResponse)
async def scores(request: Request):
    db = get_db()
    try:
        jobs = db.get_jobs()
        score_data = [
            {"title": j["title"], "company": j["company"], "score": j["match_score"]}
            for j in jobs
            if j["match_score"] is not None
        ]
        return templates.TemplateResponse(
            request, "scores.html", {"score_data": score_data}
        )
    finally:
        db.close()


@app.get("/timeline", response_class=HTMLResponse)
async def timeline(request: Request):
    db = get_db()
    try:
        rows = db.conn.execute(
            """
            SELECT a.*, j.title AS job_title, j.company AS job_company
            FROM applications a
            JOIN jobs j ON a.job_id = j.id
            ORDER BY a.created_at DESC
            """
        ).fetchall()
        applications = _rows_to_dicts(rows)
        return templates.TemplateResponse(
            request, "timeline.html", {"applications": applications}
        )
    finally:
        db.close()


@app.get("/breakdown", response_class=HTMLResponse)
async def breakdown(request: Request):
    db = get_db()
    try:
        jobs = db.get_jobs()
        jobs_list = _rows_to_dicts(jobs)
        return templates.TemplateResponse(
            request, "breakdown.html", {"jobs": jobs_list}
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# JSON API routes
# ---------------------------------------------------------------------------


@app.get("/api/stats")
async def api_stats():
    db = get_db()
    try:
        return db.get_stats()
    finally:
        db.close()


@app.get("/api/applications")
async def api_applications(status: str | None = None, limit: int = 100):
    db = get_db()
    try:
        rows = db.get_applications(status=status, limit=limit)
        return _rows_to_dicts(rows)
    finally:
        db.close()


@app.get("/api/jobs")
async def api_jobs(source: str | None = None, limit: int = 100):
    db = get_db()
    try:
        rows = db.get_jobs(source=source, limit=limit)
        return _rows_to_dicts(rows)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def run():
    """Start the dashboard server via uvicorn."""
    cfg = get_config()
    host = cfg.get("dashboard.host", "127.0.0.1")
    port = cfg.get("dashboard.port", 3000)
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run()
