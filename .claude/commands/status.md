# /status — Show application pipeline summary

Display current state of all job applications and recent activity.

## Usage
`/status`

## Process

1. **Query database** for application stats using `db.database.Database.get_stats()`

2. **Get recent applications** (last 10)

3. **Present summary**:
   ```
   📊 JobHunter Status

   Pipeline:
   📝 Draft: X
   ✅ Submitted: X
   👀 Viewed: X
   💬 Response: X
   🎤 Interview: X
   🎉 Offer: X
   ❌ Rejected: X

   Recent Activity:
   - [date] Applied to [title] at [company] — [status]
   - [date] Applied to [title] at [company] — [status]
   ...

   Match Score Avg: X/100
   Total Jobs Scraped: X
   Autopilot: [on/off]
   ```
