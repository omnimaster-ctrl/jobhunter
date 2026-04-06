# Telegram Channel Setup Guide

Set up the Telegram channel so you can control JobHunter from your phone.

## Prerequisites

- Claude Code v2.1.80 or later (`claude --version`)
- [Bun](https://bun.sh) installed (`bun --version`)
- A Telegram account

## Step 1: Create a Telegram Bot

1. Open [BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot`
3. Choose a display name (e.g., "JobHunter Bot")
4. Choose a username ending in `bot` (e.g., `jobhunter_david_bot`)
5. Copy the token BotFather gives you — you'll need it next

## Step 2: Install the Telegram Plugin

In Claude Code, run:

```
/plugin install telegram@claude-plugins-official
```

If it says the plugin isn't found:
```
/plugin marketplace update claude-plugins-official
```
Then retry the install. After installing:
```
/reload-plugins
```

## Step 3: Configure Your Token

```
/telegram:configure <YOUR_BOT_TOKEN>
```

This saves the token to `~/.claude/channels/telegram/.env`.

Alternatively, set `TELEGRAM_BOT_TOKEN` in your shell environment before launching Claude Code.

## Step 4: Launch with Channel Enabled

Exit Claude Code and restart with the channel flag:

```bash
claude --channels plugin:telegram@claude-plugins-official
```

For JobHunter specifically, launch from the project directory:

```bash
cd ~/jobhunter && claude --channels plugin:telegram@claude-plugins-official
```

## Step 5: Pair Your Account

1. Send a direct message to your bot on Telegram (any message)
2. The bot responds with a pairing code
3. Back in Claude Code, run:

```
/telegram:access pair <CODE>
```

4. Lock access to your account only:

```
/telegram:access policy allowlist
```

Now only YOUR Telegram account can send messages to this bot.

## Step 6: Test It

Send a message to your bot on Telegram:

```
What's in my working directory?
```

Claude should respond through the bot.

## Using JobHunter via Telegram

Once set up, you can send commands like:

- **Search for jobs:** "Find me 10 senior data engineer remote contractor positions at US companies"
- **Check status:** "Show me my application status"
- **Set autopilot:** "Set autopilot to daily"
- **View profile:** "Show my profile"

When applying to jobs, the bot will:
1. Send you tailored resume PDFs for review
2. Wait for your approval (reply with "approve" or "reject")
3. Submit approved applications
4. Send screenshots as proof

## Autopilot (Cron) Setup

The autopilot scheduler creates cron entries that launch Claude Code with the Telegram channel:

```bash
# In a Claude Code session:
/autopilot daily     # Search every day at 9 AM
/autopilot 2days     # Every 2 days
/autopilot weekly    # Every Monday
/autopilot off       # Disable
/autopilot status    # Check current schedule
```

The cron job runs:
```
cd ~/jobhunter && claude --channels plugin:telegram@claude-plugins-official --prompt "Run autopilot: search for jobs using saved criteria and notify me of new matches via Telegram reply tool"
```

Results are sent to your Telegram automatically.

## Telegram MCP Tools Available

When running with `--channels`, Claude has access to these tools:

| Tool | Purpose |
|------|---------|
| `reply(chat_id, text, files?, reply_to?)` | Send a message (and optional file attachments) |
| `react(chat_id, message_id, emoji)` | Add an emoji reaction |
| `edit_message(chat_id, message_id, text)` | Edit a previous bot message |
| `download_attachment(file_id)` | Download a file the user sent |

### Sending PDFs
```
reply(chat_id: "123", text: "Resume for Senior Data Engineer at Acme Corp", files: ["/abs/path/to/resume.pdf"])
```

### Threading
```
reply(chat_id: "123", text: "Here are the results...", reply_to: "456")
```

## Troubleshooting

- **Bot doesn't respond:** Make sure Claude Code is running with `--channels` flag
- **"Plugin not found":** Run `/plugin marketplace update claude-plugins-official` first
- **Pairing fails:** Send a new message to the bot and try pairing again
- **Permission prompts:** The Telegram channel can relay permission prompts to your phone — approve/deny tool usage remotely
