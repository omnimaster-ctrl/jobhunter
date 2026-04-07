# /evaluate — Evaluate a job link

Analyze a LinkedIn job URL to determine if it matches your profile. Use this when you or someone else shares a specific job link.

## Usage
- `/evaluate <linkedin_url>`
- User pastes a LinkedIn job URL in chat
- User says: "Check this job: https://linkedin.com/jobs/view/..."

## Telegram Channel Integration

**CRITICAL:** Your text output does NOT reach Telegram. ALL responses MUST go through the `reply` MCP tool.

## Process

1. **Extract URL** from the message (match `linkedin.com/jobs/view/` or `lnkd.in/` patterns)

2. **Acknowledge** via react + reply:
   ```
   react(chat_id, message_id, emoji: "👀")
   reply(chat_id, text: "🔍 Evaluating this job...")
   ```

3. **Check if already in database** via `db.database.Database.job_exists(url)`
   - If yes, retrieve existing analysis and skip to step 6

4. **Scrape job description** using `linkedin.linkedin_search.get_job_description()`
   - Check LinkedIn session first

5. **Analyze** — Spawn Job Analyzer sub-agent with job description + candidate profile

6. **Store in database** with match score

7. **Reply with verdict** via `reply`:

   **Good match (score >= 60):**
   ```
   reply(chat_id, text: "✅ Good match! [Score]/100\n\n[Job Title] at [Company]\n📍 [Location] | 💼 [Type]\n\nStrengths:\n• [point 1]\n• [point 2]\n\nGaps:\n• [gap 1]\n\nReply 'apply' to tailor resume and submit", reply_to: message_id)
   ```

   **Poor match (score < 60):**
   ```
   reply(chat_id, text: "❌ Not a great fit — [Score]/100\n\n[Job Title] at [Company]\n\nReasons:\n• [reason 1]\n• [reason 2]\n\nReply 'apply anyway' to override", reply_to: message_id)
   ```
