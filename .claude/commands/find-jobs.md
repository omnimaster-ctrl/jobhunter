# /find-jobs — Search LinkedIn for matching jobs

Search LinkedIn for jobs matching the given criteria, analyze each one, and present results ranked by match score.

## Usage
`/find-jobs <natural language criteria>`

Examples:
- `/find-jobs 10 senior data engineer remote US companies for Mexico`
- `/find-jobs top 5 ML engineer contractor positions this week`

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
   - If expired, notify user and wait for re-auth

4. **Scrape job listings** using `linkedin.linkedin_search.scrape_job_listings()`

5. **Deduplicate** — Check each job URL against the database (`db.database.Database.job_exists()`)

6. **Analyze each new job** — Spawn a Job Analyzer sub-agent for each job to get match scores

7. **Store jobs** in the database with match scores

8. **Present results** to the user, ranked by match score:
   ```
   🎯 Found X new jobs (Y duplicates skipped)

   1. [92/100] Senior Data Engineer — Acme Corp
      📍 Remote (Mexico) | 💰 $50-75/hr | ✅ Easy Apply
      🔗 https://linkedin.com/jobs/view/123

   2. [85/100] Data Engineer — Beta Inc
      ...
   ```

9. **Ask user** which jobs to apply to: "Reply with job numbers to apply (e.g., '1,3,5') or 'all'"
