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


def format_tokens(n):
    n = int(n)
    if n >= 1_000_000:
        m = n / 1_000_000
        return f"{m:.0f}M" if m == int(m) else f"{m:.1f}M"
    if n >= 1000:
        return f"{round(n / 1000)}k"
    return str(n)


# --- Values ---
model = data.get('model', {}).get('display_name', '?')
ctx = data.get('context_window', {})
pct = ctx.get('used_percentage') or 0
pct_int = int(pct)

project_dir = data.get('workspace', {}).get('project_dir') or data.get('cwd') or ''
norm = project_dir.replace('\\', '/')
parts = [p for p in norm.split('/') if p]
dir_display = '/' + '/'.join(parts[-2:]) if parts else '?'

ctx_used = ctx.get('total_input_tokens') or 0
ctx_size = ctx.get('context_window_size') or 200000

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
    git_part = f"{CYAN}↳ {branch}{RESET}"
    if ins or dels:
        git_part += f" {GREEN}+{ins}{RESET} {RED}-{dels}{RESET}"
    has_git = True
except Exception:
    git_part = None
    has_git = False

# --- Line 1: model | dir | branch +ins -del ---
segments = [f"{CYAN}{model}{RESET}"]
segments.append(f"{CYAN}{dir_display}{RESET}")
if has_git:
    segments.append(git_part)

line1 = f" {DIM}|{RESET} ".join(segments)

# --- Line 2: context bar (same style as Session/Weekly), tokens used / window size ---
line2 = f"Context {make_bar(pct_int)} {pct_int}% {DIM}{format_tokens(ctx_used)} / {format_tokens(ctx_size)}{RESET}"

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
