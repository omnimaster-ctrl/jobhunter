# /apply — Apply to selected jobs

Start the application flow for selected jobs. For each job: tailor resume, send PDF for review via Telegram, wait for approval, then submit.

## Usage
`/apply <job_ids>`

Examples:
- `/apply 1,3,5`
- `/apply 1`

## Telegram Channel Integration

This command runs inside a Claude Code session with Telegram channel enabled.
Messages from the user arrive as `<channel source="telegram" chat_id="..." message_id="...">`.

**CRITICAL:** Your text output does NOT reach Telegram. You MUST use the `reply` MCP tool for ALL communication:
- Text messages: `reply(chat_id: "...", text: "...")`
- PDF delivery: `reply(chat_id: "...", text: "...", files: ["/absolute/path/to/resume.pdf"])`
- Progress updates: `edit_message(chat_id: "...", message_id: "...", text: "...")`
- Acknowledgments: `react(chat_id: "...", message_id: "...", emoji: "👍")`

## Process

For each selected job:

1. **Load job data** from the database

2. **Create application record** in database (status: 'draft')

3. **Notify user** via `reply`: "⏳ Tailoring resume for [Job Title] at [Company]..."

4. **Tailor resume** — Spawn Resume Tailor sub-agent with:
   - Job analysis (from database match_analysis)
   - Base resume template
   - Candidate profile

5. **Compile PDF** — Use `resume.compiler.ResumeCompiler` to:
   - Fill template with tailored content
   - Compile to PDF with pdflatex
   - If compilation fails, use fallback (base resume)
   - Update application status to 'ready'

6. **Send PDF for review via Telegram** — Use `reply` with files parameter:
   ```
   reply(
     chat_id: "...",
     text: "📄 Resume tailored for: [Job Title] at [Company]\nMatch Score: [X/100]\n\nKey changes:\n- [summary]\n\nReply: ✅ approve | ❌ reject | ✏️ edit [instructions]",
     files: ["/absolute/path/to/compiled/resume.pdf"]
   )
   ```

7. **Wait for approval** (user replies via Telegram):
   - ✅ approve → `react` with 👍, update status to 'approved', proceed to submit
   - ❌ reject → update status to 'skipped', move to next job
   - ✏️ edit → Re-run Resume Tailor with edit instructions, loop back to step 6

8. **Submit application** — Spawn Application Executor sub-agent
   - Upload approved PDF
   - Fill Easy Apply form
   - Take screenshot proof
   - Update status to 'submitted' or 'failed'
   - Send screenshot via `reply(chat_id, text: "✅ Submitted!", files: ["/path/to/screenshot.png"])`

9. **Wait between applications** — Random delay of 5-15 minutes (rate limiting)

10. **Send final summary via Telegram**:
    ```
    reply(chat_id: "...", text: "📊 Application Summary:\n✅ Submitted: 3\n❌ Rejected by you: 1\n⚠️ Failed (manual needed): 1")
    ```
