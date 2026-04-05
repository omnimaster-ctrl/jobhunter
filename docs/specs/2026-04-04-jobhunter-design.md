# JobHunter — Design Specification

**Date:** 2026-04-04
**Status:** Approved
**Author:** David Tello + Claude

## Overview

JobHunter is a Claude Code-powered job hunting agent controlled via Telegram channel. It searches LinkedIn for jobs, tailors resumes using AI, sends PDFs for approval via Telegram, and submits applications via Playwright browser automation. A local web dashboard tracks analytics.

## Core Principles

- **Semi-autonomous**: Agent prepares everything, pauses for human approval before submission
- **Claude Code is the brain**: No separate backend or API costs — uses native Telegram channel plugin
- **LinkedIn-first MVP**: Architecture supports adding job sources later
- **Strategic tailoring**: AI acts as a career advisor, positioning the user as an ideal candidate per job

## User Flow

```
1. User commands via Telegram (or autopilot triggers on schedule)
2. Playwright scrapes LinkedIn with search criteria
3. Claude sub-agent analyzes each job, scores match against user profile
4. Results sent to user on Telegram, ranked by fit score
5. User selects which jobs to apply to
6. For each selected job:
   a. Sub-agent tailors LaTeX resume (template-based with replacement zones)
   b. Compiles to PDF with pdflatex
   c. Sends PDF via Telegram for review
   d. Optionally generates cover letter
7. User approves / rejects / requests edits per job
8. On approve → Playwright fills LinkedIn Easy Apply, uploads PDF, submits
9. Application logged to SQLite → Dashboard updates
```

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Telegram Channel                    │
│           (telegram@claude-plugins-official)           │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│              Claude Code Session                      │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Custom Skills│  │  Sub-Agents  │  │   Tools     │ │
│  │ /find-jobs   │  │ Job Analyzer │  │ Playwright  │ │
│  │ /apply       │  │ Resume Tailor│  │ pdflatex    │ │
│  │ /autopilot   │  │ Cover Letter │  │ SQLite      │ │
│  │ /status      │  │ App Executor │  │ File I/O    │ │
│  │ /profile     │  │              │  │             │ │
│  └─────────────┘  └──────────────┘  └─────────────┘ │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│              Data Layer (SQLite)                      │
│  jobs | applications | resumes | events               │
└──────────────────┬───────────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────────┐
│        Analytics Dashboard (FastAPI + Jinja2)         │
│        localhost:3000                                  │
└──────────────────────────────────────────────────────┘
```

## Components

### 1. Telegram Channel

Uses Claude Code's native Telegram channel plugin.

**Setup:**
1. Create bot via BotFather
2. `/plugin install telegram@claude-plugins-official`
3. `/telegram:configure <token>`
4. Run: `claude --channels plugin:telegram@claude-plugins-official`

**Capabilities:**
- Receive text commands from user
- Send job listings, match scores, status updates
- Send PDF files (tailored resumes) for review
- Receive approve/reject/edit responses

### 2. Custom Skills

Each skill follows the agent-skills SKILL.md anatomy (frontmatter, process, verification).

| Skill | Purpose |
|-------|---------|
| `/find-jobs <criteria>` | Search LinkedIn with natural language criteria |
| `/apply <job_ids>` | Start application flow for selected jobs |
| `/apply-all` | Apply to all presented jobs |
| `/status` | Pipeline summary and recent activity |
| `/autopilot <daily\|2days\|weekly\|off>` | Toggle scheduled scraping |
| `/profile` | Show/update base profile and preferences |

### 3. Sub-Agents

**Job Analyzer**
- Input: Job description URL or text
- Process: Extract requirements, tech stack, experience level, location policy, pay range
- Output: Match score (0-100), gap analysis, key talking points
- Scoring factors: tech stack overlap, experience match, location fit, seniority alignment

**Resume Tailor**
- Input: Base resume template + job analysis
- Process: Modify marked replacement zones in LaTeX template
- Replacement zones: `%%SUMMARY%%`, `%%EXPERIENCE_HIGHLIGHTS%%`, `%%SKILLS_ORDER%%`, `%%RELEVANT_PROJECTS%%`
- Output: Modified .tex file → compiled PDF
- Validation: Check .tex compiles before sending. Fallback to base resume on failure.
- Per-application choice: full tailor vs. master resume (user decides)

**Cover Letter Writer**
- Input: Job analysis + tailored resume
- Output: Targeted cover letter (optional, not default)
- Format: Professional, concise, highlights 2-3 key alignment points

**Application Executor**
- Input: Approved resume PDF + job URL
- Process: Drive Playwright to fill LinkedIn Easy Apply
- Handle: File upload, form fields, screening questions
- Unsupported forms: Send user the link to apply manually
- Output: Screenshot proof of submission

### 4. Playwright LinkedIn Engine

**Authentication:**
- Persistent Chrome profile at `~/.jobhunter/browser-profile/`
- Session health check before each run (visit LinkedIn, verify logged-in state)
- On session expiry: Telegram notification + launch browser for manual re-auth
- Never store LinkedIn credentials in code

**Job Search:**
- Navigate LinkedIn job search with filters (remote, location, experience level, etc.)
- Extract: title, company, URL, description, posted date, Easy Apply flag
- Rate limiting: Max 30 searches per hour, randomized delays (2-5s between actions)

**Application Submission:**
- Handle Easy Apply multi-step forms
- Upload tailored PDF resume
- Fill text fields, dropdowns, radio buttons
- Whitelisted form patterns (expand iteratively):
  - Basic info (name, email, phone)
  - Resume upload
  - Work authorization
  - Years of experience
  - Salary expectations
- Unsupported patterns: Skip, notify user with direct link
- Rate limiting: Max 2-3 applications per hour
- Human-like behavior: Random delays, scroll patterns

**Anti-Detection Measures:**
- Randomized delays between actions (2-8 seconds)
- Human-like mouse movements and scrolling
- No parallel browser sessions
- Respect LinkedIn's rate limits
- Session rotation awareness

### 5. LaTeX Resume Pipeline

**Base Template:**
- Source: User's existing `resume.tex` (from `~/.gemini/antigravity/scratch/resume_compile/`)
- Modified copy with replacement zones added
- Stored at `~/jobhunter/resume/templates/base_resume.tex`

**Replacement Zones:**
```latex
%%SUMMARY%%           — Professional summary paragraph
%%EXPERIENCE_HIGHLIGHTS%% — Reordered/emphasized bullet points
%%SKILLS_ORDER%%      — Skills section reordered by relevance
%%RELEVANT_PROJECTS%% — Project highlights relevant to this role
```

**Compilation:**
- `pdflatex` → PDF
- Validation: Check exit code, verify PDF is non-empty
- Fallback: Use base resume if compilation fails, notify user

**Storage:**
- `~/.jobhunter/resumes/<job_id>/resume.tex` — tailored source
- `~/.jobhunter/resumes/<job_id>/resume.pdf` — compiled PDF
- `~/.jobhunter/resumes/<job_id>/cover_letter.md` — optional cover letter

### 6. Scheduled Scraping (Autopilot)

**Options:**
- `daily` — runs every 24 hours
- `2days` — runs every 48 hours
- `weekly` — runs every 7 days
- `off` — manual only (default)

**Implementation:**
- System cron job triggers: `claude --channels plugin:telegram@claude-plugins-official --prompt "Run autopilot job search"`
- Each run is stateless — reads config and last search from SQLite
- Deduplication: URL-based, skip jobs already in database
- Results sent to Telegram, waits for user response

**User Config:**
```yaml
# ~/.jobhunter/config.yaml
autopilot:
  schedule: "off"  # daily | 2days | weekly | off
  search_criteria:
    role: "Senior Data Engineer"
    location: "Mexico"
    remote: true
    company_origin: "US"
    employment_type: "contractor"
    max_results: 10
```

### 7. Analytics Dashboard

**Tech Stack:**
- FastAPI backend
- Jinja2 HTML templates (no React — KISS)
- SQLite database
- Chart.js for visualizations
- Runs on `localhost:3000`

**Pages:**
- **Overview** — Total applied, response rate, active pipeline
- **Funnel** — Applied → Viewed → Response → Interview → Offer (manually updated statuses)
- **Match Scores** — Distribution of AI match scores, avg by company/role
- **Timeline** — Calendar view of applications, follow-up reminders
- **Breakdown** — Charts by company size, role type, salary range, tech stack
- **Resume Insights** — Most emphasized skills, keyword frequency, trending across jobs

### 8. Data Model (SQLite)

```sql
CREATE TABLE jobs (
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
    easy_apply BOOLEAN DEFAULT TRUE,
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE applications (
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

CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    tex_source TEXT NOT NULL,
    pdf_path TEXT,
    is_tailored BOOLEAN DEFAULT TRUE,
    approved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    application_id INTEGER NOT NULL REFERENCES applications(id),
    event_type TEXT NOT NULL,
    details TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Application State Machine:**
```
draft → tailoring → ready → approved → submitting → submitted
                                                       ↓
                                              viewed → response → interview → offer
                                                                      ↓
                                                                   rejected
                    failed (at any point after approved)
                    skipped (user rejected during review)
```

## Project Structure

```
~/jobhunter/
├── .claude/
│   └── commands/              # Slash commands
│       ├── find-jobs.md
│       ├── apply.md
│       ├── apply-all.md
│       ├── autopilot.md
│       ├── status.md
│       └── profile.md
├── skills/                    # SKILL.md files (agent-skills pattern)
│   ├── job-search/
│   ├── resume-tailoring/
│   ├── application-execution/
│   └── analytics-reporting/
├── agents/                    # Sub-agent definitions
│   ├── job-analyzer.md
│   ├── resume-tailor.md
│   ├── cover-letter-writer.md
│   └── application-executor.md
├── playwright/                # Browser automation (Python)
│   ├── __init__.py
│   ├── linkedin_auth.py
│   ├── linkedin_search.py
│   ├── linkedin_apply.py
│   └── session_manager.py
├── resume/                    # LaTeX engine
│   ├── __init__.py
│   ├── compiler.py
│   └── templates/
│       └── base_resume.tex
├── dashboard/                 # Analytics web app
│   ├── app.py                 # FastAPI
│   ├── templates/             # Jinja2
│   └── static/                # CSS, Chart.js
├── db/                        # Database
│   ├── __init__.py
│   ├── models.py
│   └── migrations.py
├── config/
│   └── default_config.yaml
├── tasks/
│   ├── todo.md
│   └── lessons.md
├── docs/
│   └── specs/
│       └── 2026-04-04-jobhunter-design.md
├── CLAUDE.md
├── requirements.txt
├── .gitignore
└── README.md
```

## Data Directory (User-specific)

```
~/.jobhunter/
├── browser-profile/           # Persistent Playwright Chrome profile
├── resumes/                   # Tailored PDFs per job
│   └── <job_id>/
│       ├── resume.tex
│       ├── resume.pdf
│       └── cover_letter.md
├── db/
│   └── jobhunter.db           # SQLite database
└── config.yaml                # User search preferences + schedule
```

## Security

- LinkedIn cookies: stored only in local browser profile, restrictive file permissions (700)
- Telegram bot: paired only to user's account via allowlist policy
- No credentials in code: all tokens via env vars or Claude Code channel config
- Resume PDFs: stored locally with restrictive permissions (contain PII)
- Dashboard: binds to 127.0.0.1 only, never 0.0.0.0

## Rate Limiting

| Action | Limit | Delay |
|--------|-------|-------|
| LinkedIn search | 30/hour | 2-5s between pages |
| Job description fetch | 60/hour | 1-3s between fetches |
| Application submission | 2-3/hour | 5-15min between apps |
| Telegram notifications | No limit | Batch if >5 jobs |

## Out of Scope (MVP)

- Multi-source job boards (Indeed, Turing, Toptal, etc.)
- Auto-updating application statuses from LinkedIn notifications
- AI-powered interview prep
- Salary negotiation assistant
- Mobile dashboard
- Multi-user support

## Future Expansion (Post-MVP)

- Add job sources as pluggable search modules
- LinkedIn notification scraping for status updates
- Interview prep agent (mock questions based on JD)
- Salary research agent
- Dashboard mobile-responsive redesign
