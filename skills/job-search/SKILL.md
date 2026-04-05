---
name: job-search
description: Use when searching for jobs on LinkedIn — handles URL construction, scraping, deduplication, and scoring
---

# Job Search Skill

## Overview
Search LinkedIn for jobs matching natural language criteria, deduplicate against existing database entries, score each job with the Job Analyzer agent, and present ranked results.

## When to Use
- User asks to find or search for jobs
- Autopilot triggers a scheduled search
- User provides a list of criteria or job URLs

## Process

1. **Parse criteria** — Extract keywords, filters (remote, location, experience, job type, time posted) from natural language
2. **Build URL** — Use `linkedin.linkedin_search.build_search_url()` with parsed filters
3. **Check session** — Verify LinkedIn auth via `linkedin.session_manager.SessionManager`
4. **Scrape** — Use `linkedin.linkedin_search.scrape_job_listings()` with rate-limiting delays
5. **Deduplicate** — Check each URL against `db.database.Database.job_exists()`
6. **Analyze** — Spawn Job Analyzer sub-agent for each new job
7. **Store** — Insert jobs with scores into database
8. **Present** — Show ranked results with scores, ask user for selection

## Verification
- [ ] Search URL contains correct filter parameters
- [ ] No duplicate jobs in results (all URLs unique in database)
- [ ] Each job has a match score
- [ ] Results presented in descending score order
- [ ] Rate limiting respected (delays between page loads)
