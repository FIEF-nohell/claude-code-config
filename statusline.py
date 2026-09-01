#!/usr/bin/env python3
import json, sys, subprocess, time, io, os
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

data = json.load(sys.stdin)

# --- Colors ---
CLAUDE = '\033[38;2;217;119;87m'  # Claude orange/terracotta
GREEN = '\033[32m'
RED = '\033[31m'
YELLOW = '\033[33m'
CYAN = '\033[36m'
DIM = '\033[2m'
RESET = '\033[0m'


# --- Helpers ---
def make_bar(used_pct, width=15):
    used_pct = min(max(used_pct, 0), 100)
    filled = int(used_pct * width / 100)
    empty = width - filled
    if used_pct >= 80:
        color = RED
    elif used_pct >= 50:
        color = YELLOW
    else:
        color = CLAUDE
    return f"{color}{'█' * filled}{DIM}{'░' * empty}{RESET}"


def time_until(epoch):
    if not epoch:
        return '?'
    diff = int(epoch - time.time())
    if diff <= 0:
        return 'now'
    h, m = diff // 3600, (diff % 3600) // 60
    if h > 0:
        return f"{h}h {m}m"
    return f"{m}m"


def format_duration(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}h {m}m"
    if m > 0:
        return f"{m}m {s}s"
    return f"{s}s"


def parse_ts(ts):
    return datetime.fromisoformat(ts.replace('Z', '+00:00'))


def is_real_prompt(entry):
    """True if this 'user' transcript entry is an actual typed prompt,
    not a tool_result being fed back to the model."""
    content = entry.get('message', {}).get('content')
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        return any(isinstance(c, dict) and c.get('type') == 'text' for c in content)
    return False


def turn_timing(transcript_path):
    """Returns (elapsed_seconds, still_active) for the most recent turn,
    or None if it can't be determined."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return None
    try:
        # Tail the last chunk of the file rather than reading it whole.
        with open(transcript_path, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 131072))
            chunk = f.read().decode('utf-8', errors='ignore')
        lines = chunk.splitlines()

        entries = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue
        if not entries:
            return None

        last_entry = entries[-1]
        last_type = last_entry.get('type')
        last_ts = last_entry.get('timestamp')
        if not last_ts:
            return None

        start_ts = None
        for entry in reversed(entries):
            if entry.get('type') == 'user' and is_real_prompt(entry):
                start_ts = entry.get('timestamp')
                break
        if not start_ts:
            return None

        start_dt = parse_ts(start_ts)
        if last_type == 'assistant':
            end_dt = parse_ts(last_ts)
            return (end_dt - start_dt).total_seconds(), False
        else:
            now_dt = datetime.now(timezone.utc)
            return (now_dt - start_dt).total_seconds(), True
    except Exception:
        return None


# --- Values ---
model = data.get('model', {}).get('display_name', '?')
pct = data.get('context_window', {}).get('used_percentage') or 0
pct_int = int(pct)

project_dir = data.get('workspace', {}).get('project_dir') or data.get('cwd') or ''
norm = project_dir.replace('\\', '/')
parts = [p for p in norm.split('/') if p]
dir_display = '/' + '/'.join(parts[-2:]) if parts else '?'

cost = data.get('cost', {})
total_cost = cost.get('total_cost_usd') or 0
api_seconds = (cost.get('total_api_duration_ms') or 0) / 1000

timing = turn_timing(data.get('transcript_path'))

# --- Git info ---
try:
    branch = subprocess.check_output(
        ['git', 'branch', '--show-current'], text=True, stderr=subprocess.DEVNULL
    ).strip()
    stat = subprocess.check_output(
        ['git', 'diff', '--stat'], text=True, stderr=subprocess.DEVNULL
    ).strip()
    ins, dels = 0, 0
    if stat:
        last = stat.split('\n')[-1]
        for part in last.split(','):
            part = part.strip()
            if 'insertion' in part:
                ins = int(part.split()[0])
            elif 'deletion' in part:
                dels = int(part.split()[0])
    git_part = f"{CYAN}{branch}{RESET}"
    if ins or dels:
        git_part += f" {GREEN}+{ins}{RESET} {RED}-{dels}{RESET}"
    has_git = True
except Exception:
    git_part = None
    has_git = False

# --- Turn timing display ---
if timing is not None:
    elapsed, active = timing
    if active:
        turn_part = f"{YELLOW}thinking {format_duration(elapsed)}{RESET}"
    else:
        turn_part = f"{DIM}last turn {format_duration(elapsed)}{RESET}"
else:
    turn_part = None

# --- Line 1: model | dir | branch +ins -del | cost | turn time ---
segments = [model]
segments.append(f"{CYAN}{dir_display}{RESET}")
if has_git:
    segments.append(git_part)
if turn_part:
    segments.append(turn_part)
segments.append(f"{DIM}${total_cost:.2f}{RESET}")

line1 = f" {DIM}|{RESET} ".join(segments)

# --- Line 2: context bar (same style as Session/Weekly), session time where "resets in" would go ---
line2 = f"Context {make_bar(pct_int)} {pct_int}% {DIM}session {format_duration(api_seconds)}{RESET}"

# --- Line 3 & 4: session limit bar + reset | weekly limit bar ---
rate = data.get('rate_limits', {})
five = rate.get('five_hour', {})
seven = rate.get('seven_day', {})

five_pct = five.get('used_percentage') or 0
five_reset = five.get('resets_at')
seven_pct = seven.get('used_percentage') or 0

five_int = int(five_pct)
seven_int = int(seven_pct)

line3 = f"Session {make_bar(five_pct)} {five_int}% {DIM}resets in {time_until(five_reset)}{RESET}"
line4 = f"Weekly  {make_bar(seven_pct)} {seven_int}% {DIM}resets in {time_until(seven.get('resets_at'))}{RESET}"

print(line1)
print(line2)
print(line3)
print(line4)
