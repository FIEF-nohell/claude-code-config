# Claude Code Custom Status Bar

A 4-line status bar for Claude Code CLI showing model info, project dir, git status, turn timing, cost, context usage, and rate limits at a glance.

## Preview

```
Opus 4.6 | /work/my-app | main +12 -3 | thinking 8s | $1.23
Context ███░░░░░░░░░░░░  2% session 12m 34s
Session ████░░░░░░░░░░░ 10% resets in 3h 12m
Weekly  █░░░░░░░░░░░░░░  5% resets in 2d 8h
```

## What it shows

**Line 1** — Model, project directory (last two path segments), git branch with insertions/deletions, current turn timer, cumulative session cost
**Line 2** — Context window usage bar, with cumulative API session time in place of a reset countdown
**Line 3** — 5-hour session rate limit with progress bar and reset countdown
**Line 4** — 7-day weekly rate limit with progress bar and reset countdown

### Turn timer

The `thinking Xs` / `last turn Xs` segment is derived from the session transcript: it finds the most recent real user prompt (as opposed to a tool-result message) and measures elapsed time from there. While Claude is still generating, it shows a live, growing `thinking` timer in yellow; once the turn completes, it freezes as a dimmed `last turn` duration.

## Color coding

- **Claude terracotta** (`#D97757`) — bar fill under 50% usage
- **Yellow** — bar fill at 50-80% usage; also the live "thinking" turn timer
- **Red** — bar fill above 80% usage
- **Cyan** — project directory, git branch name
- **Green/Red** — git insertions/deletions
- **Dim/gray** — session cost, completed turn time, cumulative session time
- Context percentage bar follows the same terracotta/yellow/red thresholds as the rate limit bars

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
- If you're not in a git repo, the branch/diff segment is skipped.
- The turn timer reads the last ~128KB of the session's transcript JSONL (path supplied by Claude Code); if it can't be parsed or no real user prompt is found, that segment is silently omitted.
- Paths are normalized with forward slashes for display, so the project dir segment looks the same on Windows and Linux/macOS.
- The status bar runs locally and does not consume API tokens.
