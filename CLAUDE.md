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

## Telegram Channel Integration

**Launch command:**
```bash
cd ~/jobhunter && claude --channels plugin:telegram@claude-plugins-official
```

**Setup guide:** See `docs/telegram-setup.md` for full BotFather → pair → launch instructions.

**CRITICAL RULE:** When running via Telegram channel, your text output does NOT reach the user.
ALL user-facing communication MUST go through MCP tools:

| Tool | Purpose | Example |
|------|---------|---------|
| `reply` | Send text + files | `reply(chat_id, text, files: ["/path/to.pdf"])` |
| `react` | Emoji reaction | `react(chat_id, message_id, emoji: "👍")` |
| `edit_message` | Update sent message | `edit_message(chat_id, message_id, text)` |
| `download_attachment` | Get user-sent file | `download_attachment(file_id)` |

**Inbound messages** arrive as: `<channel source="telegram" chat_id="..." message_id="...">`
Always pass `chat_id` back when calling reply/react/edit_message.

**Sending PDFs for review:**
```
reply(chat_id: "...", text: "📄 Resume for [Job]", files: ["/absolute/path/resume.pdf"])
```

**Autopilot cron** launches Claude Code with `--channels` flag so scheduled searches also notify via Telegram.

## File Organization

- `skills/` — SKILL.md files following agent-skills anatomy
- `agents/` — Sub-agent definition files (.md)
- `.claude/commands/` — Slash command definitions
- `linkedin/` — Python browser automation (LinkedIn scraping + Easy Apply)
- `resume/` — LaTeX templates and compiler
- `dashboard/` — FastAPI app + Jinja2 templates
- `autopilot/` — Cron-based scheduled job searching
- `db/` — SQLite models and migrations
- `config/` — Default configuration files
- `docs/` — Design specs and setup guides
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
