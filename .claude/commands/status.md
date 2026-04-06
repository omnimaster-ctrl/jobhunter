# /status — Show application pipeline summary

Display current state of all job applications and recent activity.

## Usage
`/status`

## Telegram Channel Integration

This command runs inside a Claude Code session with Telegram channel enabled.
**CRITICAL:** Your text output does NOT reach Telegram. Use the `reply` MCP tool to send the status report:
```
reply(chat_id: "<from inbound message>", text: "...")
```

## Process

1. **Query database** for application stats using `db.database.Database.get_stats()`

2. **Get recent applications** (last 10)

3. **Send summary via Telegram** using `reply` tool:
   ```
   reply(chat_id: "...", text: "📊 JobHunter Status\n\nPipeline:\n📝 Draft: X\n✅ Submitted: X\n👀 Viewed: X\n💬 Response: X\n🎤 Interview: X\n🎉 Offer: X\n❌ Rejected: X\n\nRecent Activity:\n- [date] [title] at [company] — [status]\n...\n\nMatch Score Avg: X/100\nTotal Jobs: X\nAutopilot: [on/off]")
   ```
