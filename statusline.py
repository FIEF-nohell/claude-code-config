#!/usr/bin/env python3
import json, sys, subprocess, time, io

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

# --- Line 1: model | branch +ins -del | ctx ---
model = data.get('model', {}).get('display_name', '?')
pct = data.get('context_window', {}).get('used_percentage') or 0
pct_int = int(pct)

# Context color
if pct_int >= 80:
    ctx_color = RED
elif pct_int >= 50:
    ctx_color = YELLOW
else:
    ctx_color = DIM

# Git info
try:
    branch = subprocess.check_output(
        ['git', 'branch', '--show-current'], text=True, stderr=subprocess.DEVNULL
    ).strip()
    stat = subprocess.check_output(
        ['git', 'diff', '--stat'], text=True, stderr=subprocess.DEVNULL
    ).strip()
    # Parse last line of --stat: "X files changed, Y insertions(+), Z deletions(-)"
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
    line1 = f"{model} {DIM}|{RESET} {git_part} {DIM}|{RESET} {ctx_color}ctx: {pct_int}%{RESET}"
except Exception:
    line1 = f"{model} {DIM}|{RESET} {ctx_color}ctx: {pct_int}%{RESET}"

# --- Line 2: session limit bar + reset | weekly limit bar ---
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

rate = data.get('rate_limits', {})
five = rate.get('five_hour', {})
seven = rate.get('seven_day', {})

five_pct = five.get('used_percentage') or 0
five_reset = five.get('resets_at')
seven_pct = seven.get('used_percentage') or 0

five_int = int(five_pct)
seven_int = int(seven_pct)

line2 = f"Session {make_bar(five_pct)} {five_int}% {DIM}resets in {time_until(five_reset)}{RESET}"
line3 = f"Weekly  {make_bar(seven_pct)} {seven_int}% {DIM}resets in {time_until(seven.get('resets_at'))}{RESET}"

print(line1)
print(line2)
print(line3)
