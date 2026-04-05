# JobHunter — Claude Code Project Instructions

## Project Overview

JobHunter is a Claude Code-powered job hunting agent controlled via Telegram channel.
It searches LinkedIn, tailors resumes per job, sends PDFs for approval, and submits applications via Playwright.

## Architecture

- **Telegram Channel**: Native Claude Code plugin (`telegram@claude-plugins-official`)
- **Sub-Agents**: Job Analyzer, Resume Tailor, Cover Letter Writer, Application Executor
- **Playwright**: LinkedIn browser automation (Python)
- **LaTeX Pipeline**: Template-based resume tailoring with `pdflatex`
- **Dashboard**: FastAPI + Jinja2 + Chart.js on localhost:3000
- **Database**: SQLite at `~/.jobhunter/db/jobhunter.db`

## Development Workflow

This project uses [agent-skills](https://github.com/addyosmani/agent-skills) for engineering discipline:
- `/spec` before code
- `/plan` for task breakdown
- `/build` for incremental implementation
- `/test` for verification
- `/review` before merge
- `/ship` for deployment

## Key Design Decisions

1. **Claude Code is the orchestrator** — no separate backend, no extra API costs
2. **Template-based LaTeX** — replacement zones (`%%SUMMARY%%`, etc.), not free-form editing
3. **LinkedIn only for MVP** — architecture supports adding sources later
4. **Semi-autonomous** — agent prepares, human approves before submission
5. **Rate limiting is mandatory** — max 2-3 applications/hour, randomized delays
6. **Persistent browser profile** — session reuse, notify on expiry via Telegram

## File Organization

- `skills/` — SKILL.md files following agent-skills anatomy
- `agents/` — Sub-agent definition files (.md)
- `.claude/commands/` — Slash command definitions
- `playwright/` — Python browser automation
- `resume/` — LaTeX templates and compiler
- `dashboard/` — FastAPI app + Jinja2 templates
- `db/` — SQLite models and migrations
- `config/` — Default configuration files
- `docs/specs/` — Design specifications
- `tasks/` — todo.md and lessons.md

## Conventions

- Python 3.11+ with type hints
- Playwright for Python (not Node)
- All Playwright actions include randomized delays (anti-detection)
- SQLite for all persistence — no external databases
- Skills follow agent-skills SKILL.md pattern
- Sub-agents are .md files with clear input/output contracts
- Dashboard templates use Jinja2, charts use Chart.js
- Config in YAML at `~/.jobhunter/config.yaml`

## Security Rules

- NEVER store LinkedIn credentials in code
- Browser profile directory: permissions 700
- Dashboard binds to 127.0.0.1 ONLY
- Telegram bot uses allowlist policy (paired account only)
- Resume PDFs contain PII — restrictive file permissions

## Testing

- Playwright scripts: test against mock LinkedIn pages
- Database layer: unit tests with in-memory SQLite
- LaTeX pipeline: test compilation with sample templates
- Dashboard: test API endpoints and template rendering
