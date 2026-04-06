# /autopilot — Configure scheduled job scraping

Toggle automatic job searching on a schedule.

## Usage
`/autopilot <schedule>`

Options:
- `/autopilot daily` — Search every 24 hours
- `/autopilot 2days` — Search every 48 hours
- `/autopilot weekly` — Search every 7 days
- `/autopilot off` — Disable (default)
- `/autopilot status` — Show current schedule

## Telegram Channel Integration

**CRITICAL:** Your text output does NOT reach Telegram. Use the `reply` MCP tool for all responses.

## Process

1. **Update config** — Write the schedule to `~/.jobhunter/config.yaml`

2. **Manage cron job** using `autopilot.scheduler.AutopilotScheduler`:
   - `daily`: `0 9 * * *` (9 AM daily)
   - `2days`: `0 9 */2 * *` (9 AM every 2 days)
   - `weekly`: `0 9 * * 1` (9 AM every Monday)
   - `off`: Remove cron entry

   Cron command launches Claude Code with Telegram channel:
   ```
   claude --channels plugin:telegram@claude-plugins-official --prompt "Run autopilot: search for jobs using saved criteria and notify me of new matches" --allowedTools "Bash,Read,Write,Edit,Glob,Grep,mcp__telegram__reply,mcp__telegram__react"
   ```

3. **Confirm** via `reply` tool:
   ```
   reply(chat_id: "...", text: "🤖 Autopilot set to: [schedule]\nNext search: [date/time]\nSearch criteria: [from config]")
   ```
