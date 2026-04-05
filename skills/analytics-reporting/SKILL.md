---
name: analytics-reporting
description: Use when showing application status, analytics, or pipeline insights — queries database and formats reports
---

# Analytics Reporting Skill

## Overview
Query the application database and present pipeline status, funnel metrics, and insights.

## When to Use
- User asks for status or progress
- User asks about application analytics
- Dashboard data needs to be summarized

## Process

1. **Query stats** — Use `db.database.Database.get_stats()` for aggregate metrics
2. **Query recent** — Get last 10 applications with job details
3. **Format report** — Present as structured summary:
   - Pipeline funnel (draft → submitted → interview → offer)
   - Recent activity timeline
   - Match score distribution
   - Autopilot status
4. **Suggest actions** — Based on data:
   - If many rejections: suggest broadening criteria
   - If low match scores: suggest different keywords
   - If no recent activity: remind about autopilot

## Verification
- [ ] Numbers match actual database counts
- [ ] Recent activity is sorted by date (newest first)
- [ ] All statuses accounted for in funnel
