# /apply-all — Apply to all presented jobs

Shortcut to apply to all jobs from the most recent search results.

## Usage
`/apply-all`

## Telegram Channel Integration

Same as `/apply` — all communication MUST go through the `reply` MCP tool. Your text output does NOT reach Telegram.

## Process

1. Get the most recent batch of jobs from the database (last search)
2. Use `reply` tool to confirm: "🚀 Starting applications for X jobs..."
3. Run the same process as `/apply` for all of them
4. Present each resume PDF via `reply` with `files` parameter for approval one by one
