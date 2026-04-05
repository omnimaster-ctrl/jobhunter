---
name: application-execution
description: Use when submitting a job application via LinkedIn Easy Apply — handles form automation, rate limiting, and result logging
---

# Application Execution Skill

## Overview
Submit an approved job application through LinkedIn Easy Apply using Playwright browser automation.

## When to Use
- After user approves a tailored resume
- During the /apply flow after approval step

## Process

1. **Verify session** — Check LinkedIn auth, notify if expired
2. **Rate limit check** — Ensure enough time has passed since last application (5-15 min)
3. **Navigate** — Go to job URL
4. **Submit** — Use `linkedin.linkedin_apply.submit_easy_apply()` with:
   - Approved resume PDF
   - Pre-filled screening answers
5. **Screenshot** — Save proof of submission
6. **Log result** — Update application status in database
7. **Handle failure** — If unsupported form, save URL for manual application and notify user

## Verification
- [ ] LinkedIn session was valid before submission
- [ ] Rate limiting was respected
- [ ] Resume PDF was uploaded
- [ ] Screenshot taken as proof
- [ ] Database updated with correct status (submitted/failed)
- [ ] User notified of result
