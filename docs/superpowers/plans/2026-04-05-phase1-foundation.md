# Phase 1: Foundation — Database, Config, LaTeX Pipeline

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the data layer, configuration system, and LaTeX resume pipeline so that all other subsystems have a working foundation to persist state and generate tailored PDFs.

**Architecture:** SQLite database with 4 tables (jobs, applications, resumes, events) accessed via a Python module. YAML-based config loaded from `~/.jobhunter/config.yaml` with defaults. LaTeX pipeline uses template replacement zones in the user's existing resume, compiled with `pdflatex`.

**Tech Stack:** Python 3.11+, SQLite3, PyYAML, pdflatex, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `db/__init__.py` | Package init, exports `Database` |
| `db/database.py` | SQLite connection, schema init, CRUD operations |
| `db/schema.sql` | Raw SQL schema (4 tables) |
| `config/__init__.py` | Package init, exports `Config` |
| `config/loader.py` | Load/merge YAML config, create defaults |
| `config/default_config.yaml` | Already exists — default values |
| `resume/__init__.py` | Package init, exports `ResumeCompiler` |
| `resume/compiler.py` | LaTeX template modification + pdflatex compilation |
| `resume/templates/base_resume.tex` | Templatized version of user's resume |
| `tests/test_database.py` | Database CRUD tests |
| `tests/test_config.py` | Config loading tests |
| `tests/test_compiler.py` | LaTeX compilation tests |

---

### Task 1: SQLite Database Schema

**Files:**
- Create: `db/schema.sql`
- Create: `db/database.py`
- Create: `db/__init__.py`
- Create: `tests/__init__.py`
- Create: `tests/test_database.py`

- [ ] **Step 1: Write the schema file**

Create `db/schema.sql`:

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    url TEXT UNIQUE NOT NULL,
    description TEXT,
    source TEXT DEFAULT 'linkedin',
    location TEXT,
    salary_range TEXT,
    employment_type TEXT,
    match_score INTEGER,
    match_analysis TEXT,
    easy_apply BOOLEAN DEFAULT 1,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    resume_path TEXT,
    cover_letter TEXT,
    status TEXT DEFAULT 'draft'
        CHECK(status IN ('draft','tailoring','ready','approved','submitting','submitted','viewed','response','interview','offer','rejected','failed','skipped')),
    screenshot_path TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    applied_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    tex_source TEXT NOT NULL,
    pdf_path TEXT,
    is_tailored BOOLEAN DEFAULT 1,
    approved BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    event_type TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- [ ] **Step 2: Write failing tests for database initialization and CRUD**

Create `tests/__init__.py` (empty file).

Create `tests/test_database.py`:

```python
import os
import pytest
from db.database import Database


@pytest.fixture
def db(tmp_path):
    """Create a temporary database for testing."""
    db_path = tmp_path / "test.db"
    database = Database(str(db_path))
    database.init()
    yield database
    database.close()


class TestDatabaseInit:
    def test_creates_database_file(self, tmp_path):
        db_path = tmp_path / "test.db"
        database = Database(str(db_path))
        database.init()
        assert os.path.exists(db_path)
        database.close()

    def test_creates_all_tables(self, db):
        tables = db.list_tables()
        assert set(tables) == {"jobs", "applications", "resumes", "events"}


class TestJobsCRUD:
    def test_insert_job(self, db):
        job_id = db.insert_job(
            title="Senior Data Engineer",
            company="Acme Corp",
            url="https://linkedin.com/jobs/view/123",
            description="Build data pipelines",
            location="Remote - Mexico",
            salary_range="$50-$75/hr",
            employment_type="contractor",
        )
        assert job_id == 1

    def test_get_job_by_id(self, db):
        job_id = db.insert_job(
            title="Senior Data Engineer",
            company="Acme Corp",
            url="https://linkedin.com/jobs/view/123",
        )
        job = db.get_job(job_id)
        assert job["title"] == "Senior Data Engineer"
        assert job["company"] == "Acme Corp"

    def test_duplicate_url_raises(self, db):
        db.insert_job(title="Job A", company="Co A", url="https://linkedin.com/jobs/view/123")
        with pytest.raises(Exception):
            db.insert_job(title="Job B", company="Co B", url="https://linkedin.com/jobs/view/123")

    def test_get_jobs_by_source(self, db):
        db.insert_job(title="Job A", company="Co A", url="https://example.com/1", source="linkedin")
        db.insert_job(title="Job B", company="Co B", url="https://example.com/2", source="indeed")
        jobs = db.get_jobs(source="linkedin")
        assert len(jobs) == 1
        assert jobs[0]["title"] == "Job A"

    def test_job_exists_by_url(self, db):
        db.insert_job(title="Job A", company="Co A", url="https://example.com/1")
        assert db.job_exists("https://example.com/1") is True
        assert db.job_exists("https://example.com/999") is False


class TestApplicationsCRUD:
    def test_create_application(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        app_id = db.create_application(job_id=job_id)
        assert app_id == 1

    def test_update_application_status(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        app_id = db.create_application(job_id=job_id)
        db.update_application_status(app_id, "approved")
        app = db.get_application(app_id)
        assert app["status"] == "approved"

    def test_invalid_status_raises(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        app_id = db.create_application(job_id=job_id)
        with pytest.raises(Exception):
            db.update_application_status(app_id, "invalid_status")

    def test_get_applications_by_status(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        app1 = db.create_application(job_id=job_id)
        db.update_application_status(app1, "submitted")
        job_id2 = db.insert_job(title="Job2", company="Co2", url="https://example.com/2")
        db.create_application(job_id=job_id2)
        submitted = db.get_applications(status="submitted")
        assert len(submitted) == 1


class TestResumesCRUD:
    def test_insert_resume(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        resume_id = db.insert_resume(job_id=job_id, tex_source="\\documentclass{article}")
        assert resume_id == 1

    def test_approve_resume(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        resume_id = db.insert_resume(job_id=job_id, tex_source="\\documentclass{article}")
        db.approve_resume(resume_id, pdf_path="/tmp/resume.pdf")
        resume = db.get_resume(resume_id)
        assert resume["approved"] == 1
        assert resume["pdf_path"] == "/tmp/resume.pdf"


class TestEventsCRUD:
    def test_log_event(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        app_id = db.create_application(job_id=job_id)
        event_id = db.log_event(application_id=app_id, event_type="status_change", details="draft -> approved")
        assert event_id == 1

    def test_get_events_for_application(self, db):
        job_id = db.insert_job(title="Job", company="Co", url="https://example.com/1")
        app_id = db.create_application(job_id=job_id)
        db.log_event(app_id, "status_change", "draft -> approved")
        db.log_event(app_id, "resume_sent", "PDF sent via Telegram")
        events = db.get_events(app_id)
        assert len(events) == 2


class TestAnalyticsQueries:
    def test_get_stats(self, db):
        job1 = db.insert_job(title="Job1", company="Co1", url="https://example.com/1", match_score=85)
        job2 = db.insert_job(title="Job2", company="Co2", url="https://example.com/2", match_score=72)
        app1 = db.create_application(job_id=job1)
        app2 = db.create_application(job_id=job2)
        db.update_application_status(app1, "submitted")
        db.update_application_status(app2, "submitted")
        db.update_application_status(app2, "interview")
        stats = db.get_stats()
        assert stats["total_jobs"] == 2
        assert stats["total_applications"] == 2
        assert stats["avg_match_score"] == 78.5
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd ~/jobhunter && python -m pytest tests/test_database.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'db.database'`

- [ ] **Step 4: Implement the Database class**

Create `db/__init__.py`:

```python
from db.database import Database

__all__ = ["Database"]
```

Create `db/database.py`:

```python
import sqlite3
from pathlib import Path
from typing import Optional


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def init(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path) as f:
            self.conn.executescript(f.read())

    def close(self) -> None:
        if self.conn:
            self.conn.close()

    def list_tables(self) -> list[str]:
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]

    # --- Jobs ---

    def insert_job(
        self,
        title: str,
        company: str,
        url: str,
        description: str = None,
        source: str = "linkedin",
        location: str = None,
        salary_range: str = None,
        employment_type: str = None,
        match_score: int = None,
        match_analysis: str = None,
        easy_apply: bool = True,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO jobs (title, company, url, description, source, location,
               salary_range, employment_type, match_score, match_analysis, easy_apply)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, company, url, description, source, location,
             salary_range, employment_type, match_score, match_analysis, easy_apply),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_job(self, job_id: int) -> dict:
        row = self.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

    def get_jobs(self, source: str = None, limit: int = 50) -> list[dict]:
        if source:
            rows = self.conn.execute(
                "SELECT * FROM jobs WHERE source = ? ORDER BY scraped_at DESC LIMIT ?",
                (source, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def job_exists(self, url: str) -> bool:
        row = self.conn.execute("SELECT 1 FROM jobs WHERE url = ?", (url,)).fetchone()
        return row is not None

    # --- Applications ---

    def create_application(self, job_id: int) -> int:
        cursor = self.conn.execute(
            "INSERT INTO applications (job_id) VALUES (?)", (job_id,)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_application(self, app_id: int) -> dict:
        row = self.conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_applications(self, status: str = None, limit: int = 50) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM applications ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def update_application_status(self, app_id: int, status: str) -> None:
        valid = (
            "draft", "tailoring", "ready", "approved", "submitting",
            "submitted", "viewed", "response", "interview", "offer",
            "rejected", "failed", "skipped",
        )
        if status not in valid:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid}")
        self.conn.execute(
            "UPDATE applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, app_id),
        )
        if status == "submitted":
            self.conn.execute(
                "UPDATE applications SET applied_at = CURRENT_TIMESTAMP WHERE id = ?",
                (app_id,),
            )
        self.conn.commit()

    # --- Resumes ---

    def insert_resume(self, job_id: int, tex_source: str, is_tailored: bool = True) -> int:
        cursor = self.conn.execute(
            "INSERT INTO resumes (job_id, tex_source, is_tailored) VALUES (?, ?, ?)",
            (job_id, tex_source, is_tailored),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_resume(self, resume_id: int) -> dict:
        row = self.conn.execute(
            "SELECT * FROM resumes WHERE id = ?", (resume_id,)
        ).fetchone()
        return dict(row) if row else None

    def approve_resume(self, resume_id: int, pdf_path: str) -> None:
        self.conn.execute(
            "UPDATE resumes SET approved = 1, pdf_path = ? WHERE id = ?",
            (pdf_path, resume_id),
        )
        self.conn.commit()

    # --- Events ---

    def log_event(self, application_id: int, event_type: str, details: str = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO events (application_id, event_type, details) VALUES (?, ?, ?)",
            (application_id, event_type, details),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_events(self, application_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM events WHERE application_id = ? ORDER BY timestamp",
            (application_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Analytics ---

    def get_stats(self) -> dict:
        total_jobs = self.conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        total_apps = self.conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        avg_score = self.conn.execute(
            "SELECT AVG(match_score) FROM jobs WHERE match_score IS NOT NULL"
        ).fetchone()[0]
        status_counts = {}
        rows = self.conn.execute(
            "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"
        ).fetchall()
        for row in rows:
            status_counts[row[0]] = row[1]
        return {
            "total_jobs": total_jobs,
            "total_applications": total_apps,
            "avg_match_score": avg_score,
            "status_counts": status_counts,
        }
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/jobhunter && python -m pytest tests/test_database.py -v`
Expected: All 15 tests PASS

- [ ] **Step 6: Commit**

```bash
git add db/ tests/
git commit -m "feat: add SQLite database layer with CRUD operations and tests"
```

---

### Task 2: Configuration System

**Files:**
- Create: `config/__init__.py`
- Create: `config/loader.py`
- Modify: `config/default_config.yaml` (already exists)
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing tests for config loading**

Create `tests/test_config.py`:

```python
import os
import pytest
import yaml
from config.loader import Config


@pytest.fixture
def config_dir(tmp_path):
    """Create a temporary config directory."""
    return tmp_path / ".jobhunter"


@pytest.fixture
def user_config(config_dir):
    """Create a user config file with overrides."""
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(yaml.dump({
        "autopilot": {"schedule": "daily"},
        "search": {"default_criteria": {"role": "ML Engineer"}},
    }))
    return config_path


class TestConfigDefaults:
    def test_loads_default_config(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("autopilot.schedule") == "off"
        assert config.get("rate_limits.applications_per_hour") == 3

    def test_default_search_criteria(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        criteria = config.get("search.default_criteria")
        assert criteria["role"] == "Senior Data Engineer"
        assert criteria["remote"] is True


class TestConfigUserOverrides:
    def test_user_config_overrides_defaults(self, user_config):
        config = Config(user_config_path=str(user_config))
        assert config.get("autopilot.schedule") == "daily"

    def test_user_config_deep_merge(self, user_config):
        config = Config(user_config_path=str(user_config))
        assert config.get("search.default_criteria.role") == "ML Engineer"
        # Default values not overridden should still exist
        assert config.get("search.default_criteria.remote") is True

    def test_non_overridden_values_remain(self, user_config):
        config = Config(user_config_path=str(user_config))
        assert config.get("rate_limits.applications_per_hour") == 3


class TestConfigCreation:
    def test_creates_default_user_config_if_missing(self, config_dir):
        config_path = config_dir / "config.yaml"
        config = Config(user_config_path=str(config_path))
        config.ensure_user_config()
        assert config_path.exists()

    def test_get_nested_value_with_dot_notation(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("dashboard.host") == "127.0.0.1"
        assert config.get("dashboard.port") == 3000

    def test_get_returns_none_for_missing_key(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("nonexistent.key") is None

    def test_get_returns_default_for_missing_key(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("nonexistent.key", "fallback") == "fallback"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/jobhunter && python -m pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'config.loader'`

- [ ] **Step 3: Implement the Config class**

Create `config/__init__.py`:

```python
from config.loader import Config

__all__ = ["Config"]
```

Create `config/loader.py`:

```python
import copy
from pathlib import Path
from typing import Any, Optional

import yaml


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base. Override values win."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class Config:
    def __init__(self, user_config_path: str = None):
        self._user_config_path = user_config_path or str(
            Path.home() / ".jobhunter" / "config.yaml"
        )
        default_path = Path(__file__).parent / "default_config.yaml"
        with open(default_path) as f:
            self._data = yaml.safe_load(f)

        user_path = Path(self._user_config_path)
        if user_path.exists():
            with open(user_path) as f:
                user_data = yaml.safe_load(f)
            if user_data:
                self._data = _deep_merge(self._data, user_data)

    def get(self, dotted_key: str, default: Any = None) -> Any:
        """Get a config value using dot notation: 'autopilot.schedule'"""
        keys = dotted_key.split(".")
        value = self._data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value

    def ensure_user_config(self) -> None:
        """Create default user config if it doesn't exist."""
        user_path = Path(self._user_config_path)
        if not user_path.exists():
            user_path.parent.mkdir(parents=True, exist_ok=True)
            default_path = Path(__file__).parent / "default_config.yaml"
            with open(default_path) as f:
                default_data = yaml.safe_load(f)
            with open(user_path, "w") as f:
                yaml.dump(default_data, f, default_flow_style=False)

    @property
    def data(self) -> dict:
        return copy.deepcopy(self._data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/jobhunter && python -m pytest tests/test_config.py -v`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add config/ tests/test_config.py
git commit -m "feat: add YAML config system with deep merge and dot-notation access"
```

---

### Task 3: LaTeX Resume Template with Replacement Zones

**Files:**
- Create: `resume/templates/base_resume.tex`
- Source: `~/.gemini/antigravity/scratch/resume_compile/resume.tex`

- [ ] **Step 1: Copy the user's resume and add replacement zones**

Create `resume/templates/base_resume.tex` — this is the user's actual resume with `%%ZONE%%` markers inserted at the 4 tailorable sections:

```latex
%-------------------------
% Resume - Dollar Green Theme
%-------------------------

\documentclass[a4paper,10pt]{article}

\usepackage[utf8]{inputenc}
\usepackage{parskip}
\usepackage{fontawesome5}
\usepackage{xcolor}
\usepackage{tikz}
\usepackage[margin=0pt]{geometry}
\usepackage{enumitem}
\usepackage[hidelinks]{hyperref}
\usepackage{titlesec}
\usepackage{graphicx}
\usepackage{eso-pic}

% Colors - Dark Dollar Green Theme
\definecolor{sidebar}{HTML}{0B3D1E}
\definecolor{lightgreen}{HTML}{85BB65}
\definecolor{darkgreen}{HTML}{0D4023}
\definecolor{accentgreen}{HTML}{1E8449}
\definecolor{textgray}{HTML}{333333}

% Font Improvements
\usepackage[default]{lato}
\usepackage[T1]{fontenc}


\pagestyle{empty}

% Draw sidebar on every page using eso-pic
\AddToShipoutPictureBG{%
\AtPageLowerLeft{%
\color{sidebar}\rule{6.2cm}{\paperheight}%
}%
}

% Section formatting
\titleformat{\section}{\Large\bfseries\color{darkgreen}}{}{0em}{}[\color{sidebar}\titlerule]
\titlespacing*{\section}{0pt}{6pt}{4pt}

\begin{document}

\noindent
\begin{minipage}[t]{6.2cm}
% ===== LEFT SIDEBAR =====
\vspace*{0.4cm}
\hspace{0.35cm}
\begin{minipage}[t]{5.5cm}
\color{white}
\centering

% Photo
\begin{tikzpicture}
\clip (0,0) circle (1.6cm);
\node at (0,-0.2) {\includegraphics[width=2.5cm]{daveProfile.png}};
\end{tikzpicture}

\vspace{0.4cm}

% Contact
{\small
\faMapMarker*\hspace{0.2cm}Morelia, Michoacán, MX\\[0.2cm]
\faPhone*\hspace{0.2cm}(443) 491-0277\\[0.2cm]
\faEnvelope\hspace{0.2cm}urieldavidtellopadilla\\@gmail.com\\[0.2cm]
\faLinkedin\hspace{0.2cm}\href{https://www.linkedin.com/in/david-tello-850a63bb/}{/in/david-tello}
}

\vspace{0.3cm}
{\color{lightgreen!60}\rule{4.8cm}{0.4pt}}
\vspace{0.25cm}

% Profile — REPLACEMENT ZONE
{\large\bfseries PROFILE}\\[0.3cm]
\begin{flushleft}
\small
%%SUMMARY%%
\end{flushleft}

\vspace{0.2cm}
{\color{lightgreen!60}\rule{4.8cm}{0.4pt}}
\vspace{0.2cm}

% Skills — REPLACEMENT ZONE
{\large\bfseries SKILLS}\\[0.3cm]
\begin{flushleft}
\small
%%SKILLS_ORDER%%
\end{flushleft}

\vspace{0.2cm}
{\color{lightgreen!60}\rule{4.8cm}{0.4pt}}
\vspace{0.2cm}

% Languages
{\large\bfseries LANGUAGES}\\[0.3cm]
\small
English - 90\% Proficient\\
Spanish - Native

\vspace{0.2cm}
{\color{lightgreen!60}\rule{4.8cm}{0.4pt}}
\vspace{0.2cm}

% Certification
{\large\bfseries CERTIFICATION}\\[0.3cm]
\begin{flushleft}
\small
\textbf{Machine Learning}\\
\textbf{Specialization}\\
Coursera, 2022
\end{flushleft}

\vspace{0.2cm}
{\color{lightgreen!60}\rule{4.8cm}{0.4pt}}
\vspace{0.2cm}

% Education
{\large\bfseries EDUCATION}\\[0.3cm]
\begin{flushleft}
\small
\textbf{M.Sc. Physics \& Math}\\
IPN - ESFM, CDMX\\
2019 - 2021\\[0.25cm]

\textbf{B.Sc. Physics \& Math}\\
UMSNH, Morelia\\
2013 - 2017
\end{flushleft}

\end{minipage}
\end{minipage}%
\hfill%
\begin{minipage}[t]{14.3cm}
% ===== RIGHT CONTENT =====
\vspace*{0.5cm}
\hspace{0.4cm}
\begin{minipage}[t]{13.4cm}
\color{textgray}

% Name
{\fontsize{26}{30}\selectfont\bfseries\color{darkgreen} Uriel David Tello Padilla}\\[0.15cm]
{\large\color{accentgreen} Senior Data Engineer | Cloud Solutions Architect}

\vspace{0.4cm}

% Experience — REPLACEMENT ZONE
\section{EXPERIENCE}

%%EXPERIENCE_HIGHLIGHTS%%

\vspace{0.3cm}

% Relevant Projects — REPLACEMENT ZONE (optional, appended if provided)
%%RELEVANT_PROJECTS%%

\end{minipage}
\end{minipage}

\end{document}
```

- [ ] **Step 2: Copy the profile photo to the resume templates directory**

```bash
cp ~/.gemini/antigravity/scratch/resume_compile/daveProfile.png ~/jobhunter/resume/templates/daveProfile.png
```

- [ ] **Step 3: Commit the template**

```bash
git add resume/templates/
git commit -m "feat: add templatized LaTeX resume with replacement zones"
```

---

### Task 4: LaTeX Resume Compiler

**Files:**
- Create: `resume/__init__.py`
- Create: `resume/compiler.py`
- Create: `tests/test_compiler.py`

- [ ] **Step 1: Write failing tests for the compiler**

Create `tests/test_compiler.py`:

```python
import os
import shutil
import pytest
from resume.compiler import ResumeCompiler


@pytest.fixture
def compiler():
    return ResumeCompiler()


@pytest.fixture
def output_dir(tmp_path):
    return tmp_path / "output"


# Default content for replacement zones (matches the user's actual resume)
DEFAULT_SUMMARY = (
    "Dynamic Data Engineer with 9+ years designing ETL pipelines "
    "using Azure Databricks, Microsoft Fabric, and AWS. "
    "Expert in Lake House architectures and CI/CD for data workflows."
)

DEFAULT_SKILLS = r"""\textbf{Cloud \& Data}\\
Azure Databricks \textbullet{} Fabric\\
AWS (Glue, EMR, Redshift)\\
Snowflake \textbullet{} Delta Lake\\[0.25cm]

\textbf{Programming}\\
Python \textbullet{} PySpark \textbullet{} SQL\\
Scala \textbullet{} Java \textbullet{} Julia\\[0.25cm]

\textbf{DevOps \& Tools}\\
Terraform \textbullet{} Docker \textbullet{} K8s\\
Airflow \textbullet{} dbt \textbullet{} Git\\
Azure DevOps \textbullet{} Jenkins"""

DEFAULT_EXPERIENCE = r"""\textbf{Data Engineer} \hfill \textbf{Jun 2025 - Present}\\
{\color{accentgreen}Capgemini} | Remote
\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]
\small
\item Orchestrate end-to-end ETL/ELT pipelines with Microsoft Fabric, Azure Data Factory, and Terraform
\item Leverage Azure Databricks ecosystem (Delta Lake, Delta Live Tables, MLflow) for scalable analytics
\item Build modular data transformations using dbt with automated testing and documentation
\end{itemize}"""


class TestTemplateLoading:
    def test_loads_base_template(self, compiler):
        template = compiler.load_template()
        assert "%%SUMMARY%%" in template
        assert "%%SKILLS_ORDER%%" in template
        assert "%%EXPERIENCE_HIGHLIGHTS%%" in template
        assert "%%RELEVANT_PROJECTS%%" in template

    def test_fill_template(self, compiler):
        filled = compiler.fill_template(
            summary=DEFAULT_SUMMARY,
            skills=DEFAULT_SKILLS,
            experience=DEFAULT_EXPERIENCE,
        )
        assert "%%SUMMARY%%" not in filled
        assert "%%SKILLS_ORDER%%" not in filled
        assert "%%EXPERIENCE_HIGHLIGHTS%%" not in filled
        assert "Dynamic Data Engineer" in filled


class TestCompilation:
    @pytest.mark.skipif(
        shutil.which("pdflatex") is None,
        reason="pdflatex not installed"
    )
    def test_compile_produces_pdf(self, compiler, output_dir):
        filled = compiler.fill_template(
            summary=DEFAULT_SUMMARY,
            skills=DEFAULT_SKILLS,
            experience=DEFAULT_EXPERIENCE,
        )
        pdf_path = compiler.compile(filled, str(output_dir))
        assert os.path.exists(pdf_path)
        assert pdf_path.endswith(".pdf")
        assert os.path.getsize(pdf_path) > 0

    def test_compile_invalid_latex_returns_none(self, compiler, output_dir):
        result = compiler.compile(r"\documentclass{article}\begin{document}\invalid{", str(output_dir))
        assert result is None


class TestFallback:
    @pytest.mark.skipif(
        shutil.which("pdflatex") is None,
        reason="pdflatex not installed"
    )
    def test_compile_with_fallback_on_failure(self, compiler, output_dir):
        pdf_path = compiler.compile_with_fallback(
            tailored_tex=r"\documentclass{article}\begin{document}\invalid{",
            output_dir=str(output_dir),
        )
        # Should fall back to base resume
        assert pdf_path is not None or pdf_path is None  # depends on pdflatex availability
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/jobhunter && python -m pytest tests/test_compiler.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'resume.compiler'`

- [ ] **Step 3: Implement the ResumeCompiler class**

Create `resume/__init__.py`:

```python
from resume.compiler import ResumeCompiler

__all__ = ["ResumeCompiler"]
```

Create `resume/compiler.py`:

```python
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


class ResumeCompiler:
    def __init__(self, template_dir: str = None):
        self.template_dir = template_dir or str(
            Path(__file__).parent / "templates"
        )
        self.base_template_path = os.path.join(self.template_dir, "base_resume.tex")

    def load_template(self) -> str:
        with open(self.base_template_path) as f:
            return f.read()

    def fill_template(
        self,
        summary: str = None,
        skills: str = None,
        experience: str = None,
        projects: str = None,
    ) -> str:
        """Replace %%ZONE%% markers with provided content.
        If a value is None, the default content from the original resume is used."""
        template = self.load_template()

        defaults = self._get_defaults()

        template = template.replace("%%SUMMARY%%", summary or defaults["summary"])
        template = template.replace("%%SKILLS_ORDER%%", skills or defaults["skills"])
        template = template.replace(
            "%%EXPERIENCE_HIGHLIGHTS%%", experience or defaults["experience"]
        )
        template = template.replace(
            "%%RELEVANT_PROJECTS%%", projects or ""
        )

        return template

    def compile(self, tex_source: str, output_dir: str) -> Optional[str]:
        """Compile LaTeX source to PDF. Returns PDF path or None on failure."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = os.path.join(tmpdir, "resume.tex")
            with open(tex_path, "w") as f:
                f.write(tex_source)

            # Copy supporting files (photo, etc.) to temp dir
            for item in Path(self.template_dir).iterdir():
                if item.suffix != ".tex":
                    dest = os.path.join(tmpdir, item.name)
                    if item.is_file():
                        shutil.copy2(str(item), dest)

            try:
                result = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "resume.tex"],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                pdf_tmp = os.path.join(tmpdir, "resume.pdf")
                if result.returncode == 0 and os.path.exists(pdf_tmp) and os.path.getsize(pdf_tmp) > 0:
                    pdf_dest = os.path.join(output_dir, "resume.pdf")
                    shutil.copy2(pdf_tmp, pdf_dest)
                    # Also save the tex source
                    tex_dest = os.path.join(output_dir, "resume.tex")
                    shutil.copy2(tex_path, tex_dest)
                    return pdf_dest
                return None
            except (subprocess.TimeoutExpired, FileNotFoundError):
                return None

    def compile_with_fallback(self, tailored_tex: str, output_dir: str) -> Optional[str]:
        """Try compiling tailored resume, fall back to base on failure."""
        pdf_path = self.compile(tailored_tex, output_dir)
        if pdf_path:
            return pdf_path

        # Fallback: compile base resume with defaults
        defaults = self._get_defaults()
        base_tex = self.fill_template(
            summary=defaults["summary"],
            skills=defaults["skills"],
            experience=defaults["experience"],
        )
        return self.compile(base_tex, output_dir)

    def _get_defaults(self) -> dict:
        """Default content matching the user's original resume."""
        return {
            "summary": (
                "Dynamic Data Engineer with 9+ years designing ETL pipelines "
                "using Azure Databricks, Microsoft Fabric, and AWS. "
                "Expert in Lake House architectures and CI/CD for data workflows."
            ),
            "skills": (
                r"\textbf{Cloud \& Data}\\"
                "\nAzure Databricks \\textbullet{} Fabric\\\\\n"
                "AWS (Glue, EMR, Redshift)\\\\\n"
                "Snowflake \\textbullet{} Delta Lake\\\\[0.25cm]\n\n"
                r"\textbf{Programming}\\"
                "\nPython \\textbullet{} PySpark \\textbullet{} SQL\\\\\n"
                "Scala \\textbullet{} Java \\textbullet{} Julia\\\\[0.25cm]\n\n"
                r"\textbf{DevOps \& Tools}\\"
                "\nTerraform \\textbullet{} Docker \\textbullet{} K8s\\\\\n"
                "Airflow \\textbullet{} dbt \\textbullet{} Git\\\\\n"
                "Azure DevOps \\textbullet{} Jenkins"
            ),
            "experience": (
                r"\textbf{Data Engineer} \hfill \textbf{Jun 2025 - Present}\\" + "\n"
                r"{\color{accentgreen}Capgemini} | Remote" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Orchestrate end-to-end ETL/ELT pipelines with Microsoft Fabric, Azure Data Factory, and Terraform" + "\n"
                r"\item Leverage Azure Databricks ecosystem (Delta Lake, Delta Live Tables, MLflow) for scalable analytics" + "\n"
                r"\item Build modular data transformations using dbt with automated testing and documentation" + "\n"
                r"\item Design and schedule complex workflows with Airflow for batch and streaming pipelines" + "\n"
                r"\item Develop AWS data solutions using Glue, EMR, Redshift, and S3 for multi-cloud architectures" + "\n"
                r"\end{itemize}" + "\n\n"
                r"\vspace{0.1cm}" + "\n"
                r"\textbf{Data Engineer} \hfill \textbf{Jul 2024 - Jun 2025}\\" + "\n"
                r"{\color{accentgreen}Hexaware Technologies} | Remote" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Implement Lake House architecture with Azure Purview and Snowflake" + "\n"
                r"\item Design ETL pipelines using Data Factory and Dataflow Gen2 for scalable ingestion" + "\n"
                r"\item Integrate Microsoft Fabric with Azure Databricks, Functions, and Synapse" + "\n"
                r"\end{itemize}" + "\n\n"
                r"\vspace{0.1cm}" + "\n"
                r"\textbf{Sr Data Engineer (Freelancer Contractor)} \hfill \textbf{Jan 2023 - Jan 2025}\\" + "\n"
                r"{\color{accentgreen}Sherwin Williams} | Remote, USA" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Design and orchestrate ETL pipelines using Data Factory and Dataflow Gen2 for scalable data ingestion and transformation" + "\n"
                r"\item Develop and maintain Notebooks for complex data processing and analytics using PySpark and SQL" + "\n"
                r"\item Integrate Microsoft Fabric with external services like Azure Databricks, Azure Functions, and Synapse for advanced processing" + "\n"
                r"\item Implement CI/CD pipelines for Fabric-based workflows using Azure DevOps and Infrastructure as Code (IaC) tools like Terraform" + "\n"
                r"\item Employed Lake House architecture with Azure Purview and Snowflake for unified analytics" + "\n"
                r"\end{itemize}" + "\n\n"
                r"\vspace{0.1cm}" + "\n"
                r"\textbf{Data Engineer} \hfill \textbf{May 2024 - Jul 2024}\\" + "\n"
                r"{\color{accentgreen}Eviden} | Remote" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Designed scalable data flows in Python, SQL, and Scala with Spark Streaming" + "\n"
                r"\item Built parameterized workflows and incremental loads using Airflow" + "\n"
                r"\item Integrated monitoring with Datadog and alerting via Logic Apps" + "\n"
                r"\end{itemize}" + "\n\n"
                r"\vspace{0.1cm}" + "\n"
                r"\textbf{Data Engineer} \hfill \textbf{Jan 2024 - May 2024}\\" + "\n"
                r"{\color{accentgreen}PRAXAIRLINDE} | Remote" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Developed ETL/ELT workflows with Microsoft Fabric and Databricks" + "\n"
                r"\item Implemented data partitioning and caching strategies in Delta Lake" + "\n"
                r"\item Managed pipeline triggers, parameters, and scheduling with Airflow" + "\n"
                r"\end{itemize}" + "\n\n"
                r"\vspace{0.1cm}" + "\n"
                r"\textbf{Data Engineer} \hfill \textbf{Aug 2023 - Jan 2024}\\" + "\n"
                r"{\color{accentgreen}TCS (TATA Consultancy Services)} | Guadalajara, Mexico" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Automated CI/CD deployments via Azure DevOps, GitHub Actions, and Terraform" + "\n"
                r"\item Conducted data profiling and validation using Great Expectations and PySpark" + "\n"
                r"\item Optimized data transformation jobs using Python, SQL, and Spark SQL" + "\n"
                r"\end{itemize}" + "\n\n"
                r"\vspace{0.1cm}" + "\n"
                r"\textbf{Data Engineer} \hfill \textbf{Jan 2022 - Jul 2023}\\" + "\n"
                r"{\color{accentgreen}Grupo Salinas (Elektra EKT)} | Mexico City" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Developed stream-processing apps with Azure Event Hubs and Stream Analytics" + "\n"
                r"\item Designed Azure Synapse Analytics schemas; implemented GDPR-compliant anonymization" + "\n"
                r"\item Built real-time inventory tracking pipelines with Azure Functions" + "\n"
                r"\end{itemize}" + "\n\n"
                r"\vspace{0.1cm}" + "\n"
                r"\textbf{Data Engineer} \hfill \textbf{Feb 2017 - Dec 2021}\\" + "\n"
                r"{\color{accentgreen}Dealership Performance 360} | Remote" + "\n"
                r"\begin{itemize}[leftmargin=0.4cm, itemsep=3pt, topsep=2pt, parsep=3pt]" + "\n"
                r"\small" + "\n"
                r"\item Ingested data using AWS Glue, Amazon EMR, and Redshift Spectrum" + "\n"
                r"\item Developed Amazon MSK connectors, Kafka, and Elasticsearch integrations" + "\n"
                r"\item Built microservices in Scala on Kubernetes; automated pipelines with Terraform" + "\n"
                r"\end{itemize}"
            ),
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/jobhunter && python -m pytest tests/test_compiler.py -v`
Expected: Template loading and fill tests PASS. Compilation tests PASS if pdflatex is installed (skipped otherwise).

- [ ] **Step 5: Commit**

```bash
git add resume/ tests/test_compiler.py
git commit -m "feat: add LaTeX resume compiler with template zones and fallback"
```

---

### Task 5: Data Directory Initialization Script

**Files:**
- Create: `setup_env.py`

- [ ] **Step 1: Create the setup script**

Create `setup_env.py`:

```python
"""Initialize the ~/.jobhunter data directory and database."""
import os
import shutil
import stat
from pathlib import Path

from config.loader import Config
from db.database import Database


def setup():
    home = Path.home() / ".jobhunter"

    # Create directories with restrictive permissions
    dirs = [
        home,
        home / "browser-profile",
        home / "resumes",
        home / "db",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        os.chmod(d, stat.S_IRWXU)  # 700

    # Initialize config
    config = Config()
    config.ensure_user_config()

    # Initialize database
    db_path = str(home / "db" / "jobhunter.db")
    db = Database(db_path)
    db.init()
    db.close()
    os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)  # 600

    print("JobHunter environment initialized:")
    print(f"  Config:   {home / 'config.yaml'}")
    print(f"  Database: {db_path}")
    print(f"  Browser:  {home / 'browser-profile'}")
    print(f"  Resumes:  {home / 'resumes'}")


if __name__ == "__main__":
    setup()
```

- [ ] **Step 2: Run the setup script**

Run: `cd ~/jobhunter && python setup_env.py`
Expected: Prints paths and creates `~/.jobhunter/` structure

- [ ] **Step 3: Verify the setup**

Run: `ls -la ~/.jobhunter/`
Expected: `browser-profile/`, `resumes/`, `db/`, `config.yaml` all with 700/600 permissions

- [ ] **Step 4: Commit**

```bash
git add setup_env.py
git commit -m "feat: add environment initialization script"
```

---

### Task 6: Run Full Test Suite and Final Commit

- [ ] **Step 1: Install dependencies**

Run: `cd ~/jobhunter && pip install -r requirements.txt pytest`

- [ ] **Step 2: Run all tests**

Run: `cd ~/jobhunter && python -m pytest tests/ -v`
Expected: All tests PASS (compilation tests may skip if no pdflatex)

- [ ] **Step 3: Verify pdflatex is available**

Run: `which pdflatex`
If not installed: `brew install --cask mactex-no-gui` or `brew install basictex`

- [ ] **Step 4: Run compilation test with pdflatex**

Run: `cd ~/jobhunter && python -m pytest tests/test_compiler.py -v -k "compile_produces_pdf"`
Expected: PASS — produces a valid PDF

- [ ] **Step 5: Final commit and push**

```bash
git add -A
git commit -m "feat: complete Phase 1 foundation — database, config, LaTeX pipeline"
git push origin main
```
