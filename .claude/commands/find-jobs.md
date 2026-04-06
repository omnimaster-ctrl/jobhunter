# /find-jobs — Search LinkedIn for matching jobs

Search LinkedIn for jobs matching the given criteria, analyze each one, and present results ranked by match score.

## Usage
`/find-jobs <natural language criteria>`

Examples:
- `/find-jobs 10 senior data engineer remote US companies for Mexico`
- `/find-jobs top 5 ML engineer contractor positions this week`

## Telegram Channel Integration

This command runs inside a Claude Code session with Telegram channel enabled.
Messages from the user arrive as `<channel source="telegram" chat_id="..." message_id="...">`.

**CRITICAL:** Your text output does NOT reach Telegram. You MUST use the `reply` MCP tool to send all results, questions, and updates to the user:
```
reply(chat_id: "<from inbound message>", text: "...", reply_to: "<message_id>")
```

## Process

1. **Parse criteria** from the user's natural language input. Extract:
   - Role/keywords
   - Number of results wanted (default: 10)
   - Location preferences
   - Remote/on-site preference
   - Employment type (contractor, full-time)
   - Time filter (today, this week, this month)

2. **Build search URL** using `linkedin.linkedin_search.build_search_url()` with the parsed filters

3. **Check LinkedIn session** using `linkedin.session_manager.SessionManager`
   - If expired, use `reply` tool to notify user and wait for re-auth

4. **Scrape job listings** using `linkedin.linkedin_search.scrape_job_listings()`
   - Use `react(chat_id, message_id, emoji: "👀")` to acknowledge the search started

5. **Deduplicate** — Check each job URL against the database (`db.database.Database.job_exists()`)

6. **Analyze each new job** — Spawn a Job Analyzer sub-agent for each job to get match scores

7. **Store jobs** in the database with match scores

8. **Send results via Telegram** — Use `reply` tool to send ranked results:
   ```
   reply(chat_id: "...", text: "🎯 Found X new jobs (Y duplicates skipped)\n\n1. [92/100] Senior Data Engineer — Acme Corp\n   📍 Remote (Mexico) | 💰 $50-75/hr | ✅ Easy Apply\n\n2. [85/100] Data Engineer — Beta Inc\n   ...")
   ```

9. **Ask user** via `reply`: "Reply with job numbers to apply (e.g., '1,3,5') or 'all'"
