# Claude Code Custom Status Bar

A 3-line status bar for Claude Code CLI showing model info, git status, context usage, and rate limits at a glance.

## Preview

```
Opus 4.6 | main +12 -3 | ctx: 2%
Session ████░░░░░░░░░░░ 10% resets in 3h 12m
Weekly  █░░░░░░░░░░░░░░  5% resets in 2d 8h
```

## What it shows

**Line 1** — Model, git branch with insertions/deletions, context window usage  
**Line 2** — 5-hour session rate limit with progress bar and reset countdown  
**Line 3** — 7-day weekly rate limit with progress bar and reset countdown

## Color coding

- **Claude terracotta** (`#D97757`) — bar fill under 50% usage
- **Yellow** — bar fill at 50-80% usage
- **Red** — bar fill above 80% usage
- **Cyan** — git branch name
- **Green/Red** — git insertions/deletions
- Context percentage dims when low, turns yellow at 50%, red at 80%

## Requirements

- Python 3 (any recent version)
- `git` on PATH (for branch/diff info — gracefully skipped if not in a repo)
- Claude Code CLI
- Claude.ai Pro or Max subscription (for rate limit data)

## Installation

### 1. Copy the script

Copy `statusline.py` to your Claude config directory:

```bash
# macOS / Linux
cp statusline.py ~/.claude/statusline.py
chmod +x ~/.claude/statusline.py

# Windows (Git Bash)
cp statusline.py ~/.claude/statusline.py
```

### 2. Add to settings

Add the contents of `settings-snippet.json` to your `~/.claude/settings.json`. If you already have a settings file, merge the `statusLine` block into it:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python ~/.claude/statusline.py",
    "refreshInterval": 60
  }
}
```

The `refreshInterval: 60` re-runs the script every 60 seconds so the "resets in" countdowns stay current even when idle.

### 3. Verify

Send any message in Claude Code. The status bar should appear at the bottom of your terminal.

## Files

| File | Description |
|------|-------------|
| `statusline.py` | The status bar script (receives JSON on stdin from Claude Code) |
| `settings-snippet.json` | The settings.json config block to enable the status bar |
| `README.md` | This file |

## Notes

- Rate limit data (`Session` and `Weekly` lines) only appears for Claude.ai Pro/Max subscribers and only after the first API response in a session. Before that, the bars show 0%.
- The script forces UTF-8 output to avoid encoding issues on Windows (cp1252).
- If you're not in a git repo, the branch/diff segment is skipped and line 1 shows just the model and context.
- The status bar runs locally and does not consume API tokens.
