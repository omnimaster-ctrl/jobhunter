# /check-messages — Check LinkedIn inbox for job offers

Scan your LinkedIn messaging inbox for recruiter messages and job offers, evaluate each against your profile, and report matches via Telegram.

## Usage
- `/check-messages` — Scan recent conversations
- User says: "I got a message on LinkedIn with a job offer, go check it"
- User says: "Check my LinkedIn messages"

## Telegram Channel Integration

**CRITICAL:** Your text output does NOT reach Telegram. ALL responses MUST go through the `reply` MCP tool.

## Process

1. **Acknowledge** via `reply`:
   ```
   reply(chat_id, text: "👀 Checking your LinkedIn inbox for job offers...")
   ```

2. **Check LinkedIn session** using `linkedin.session_manager.SessionManager`
   - If expired, notify user via `reply` and wait for re-auth

3. **Scan inbox** using `linkedin.linkedin_messages.find_job_offers_in_inbox(page)`
   - This reads recent conversations, filters for job-related messages
   - Extracts LinkedIn job URLs from message bodies
   - Uses anti-detection delays between conversations

4. **For each job offer found:**

   a. **Check if already in database** via `db.database.Database.job_exists(url)`
      - If yes, retrieve existing score and skip analysis

   b. **Scrape job description** using `linkedin.linkedin_search.get_job_description()`

   c. **Analyze the job** — Spawn Job Analyzer sub-agent with:
      - Job description
      - Candidate profile from `config/profile.yaml`
      - Target criteria from `config/default_config.yaml`

   d. **Store in database** with match score

5. **Evaluate fit** for each job against target criteria:
   - Remote? (must be remote)
   - Contractor/freelancer? (preferred)
   - US company? (preferred)
   - Match score threshold: 60+ = good fit

6. **Send results via Telegram** using `reply`:

   **If job offers found:**
   ```
   reply(chat_id, text: "📬 Found X job offers in your LinkedIn inbox:\n\n✅ MATCHES:\n\n1. [85/100] Senior Data Engineer — Acme Corp\n   From: [Recruiter Name]\n   📍 Remote | 💼 Contract\n   💬 '[snippet of their message]'\n   → Reply 'apply 1' to start application\n\n❌ NOT A FIT:\n\n2. [42/100] Java Developer — Beta Inc\n   From: [Recruiter Name]\n   Reasons: On-site required, Java stack\n   → Reply 'apply 2 anyway' to override")
   ```

   **If no job offers found:**
   ```
   reply(chat_id, text: "📬 No new job offers found in your recent LinkedIn messages.")
   ```

7. **Handle follow-up** from user:
   - "apply 1" → Trigger `/apply` flow for that job
   - "apply 2 anyway" → Apply despite low score
   - "apply all" → Apply to all matches (score >= 60)

## Tools Used

- `linkedin.browser` — launch_browser, random_delay
- `linkedin.session_manager` — SessionManager
- `linkedin.linkedin_messages` — find_job_offers_in_inbox, scrape_conversations, read_conversation
- `linkedin.linkedin_search` — get_job_description
- `db.database` — Database (job storage, dedup)
- `config/profile.yaml` — Candidate profile
- Job Analyzer sub-agent — Match scoring
- MCP `reply` — Telegram responses
- MCP `react` — Acknowledge receipt
