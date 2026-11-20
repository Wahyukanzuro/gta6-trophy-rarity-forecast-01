#!/usr/bin/env python3
"""GTA VI week-one trophy rarity forecast (v2).

Model (model-fit-report-v3.md, section 6): for each trophy, the median
is the last read's logit shifted by SHIFT_SCALE times the per-trophy
logit move across the most recent step in the case's own history. The
spread is a random walk in logit space, s = 0.5 * sqrt(d); when the
history contains no step at all, the spread widens by REFRESH_NO_STEP
to cover a refresh the case has not seen yet. Stdlib only, no network,
deterministic.
"""

import json
import math
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

SHIFT_SCALE = 0.50
PER_TROPHY_C = 0.0
REFRESH_NO_STEP = 1.5
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]
RATE_LO = 0.01
RATE_HI = 99.99
_Z_BY_LEVEL = {0.05: -1.645, 0.25: -0.674, 0.5: 0.0, 0.75: 0.674, 0.95: 1.645}


def clamp_rate(x):
    if x < RATE_LO:
        return RATE_LO
    if x > RATE_HI:
        return RATE_HI
    return x


def logit_pct(x):
    p = clamp_rate(x) / 100.0
    return math.log(p / (1.0 - p))


def sigmoid(x):
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def round4_half_up(x):
    q = Decimal(str(x)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if q == q.to_integral_value():
        return int(q)
    return float(q)


def parse_time(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def find_step(history):
    """Latest index j >= 1 where read j differs from read j - 1.

    A read differs when its rates list differs (exact inequality, None
    counts as a value) or its players_tracked differs. Returns None
    when no read differs from its predecessor.
    """
    step = None
    for j in range(1, len(history)):
        prev = history[j - 1]
        cur = history[j]
        if cur.get("rates") != prev.get("rates"):
            step = j
        elif cur.get("players_tracked") != prev.get("players_tracked"):
            step = j
    return step


def last_rates(history, count):
    last = [None] * count
    for read in history:
        rates = read.get("rates") or []
        for i in range(min(count, len(rates))):
            if rates[i] is not None:
                last[i] = rates[i]
    return last

def forecast_case(case):
    trophies = case.get("trophies") or []
    history = case.get("history") or []
    levels = case.get("levels") or [0.05, 0.25, 0.5, 0.75, 0.95]
    try:
        cut = parse_time(case["at"])
        target = parse_time(case["target"])
        days = (target - cut).total_seconds() / 86400.0
    except Exception:
        days = float(case.get("horizon_minutes", 0)) / 1440.0
    if days < 0.0:
        days = 0.0
    rw = 0.5 * math.sqrt(days)
    step = find_step(history)
    last = last_rates(history, len(trophies))
    rows = []
    for i, trophy in enumerate(trophies):
        base = last[i] if last[i] is not None else RATE_LO
        delta = 0.0
        if step is not None:
            before = history[step - 1].get("rates") or []
            after = history[step].get("rates") or []
            b = before[i] if i < len(before) else None
            a = after[i] if i < len(after) else None
            if b is not None and a is not None:
                delta = logit_pct(a) - logit_pct(b)
        median_logit = logit_pct(base) + SHIFT_SCALE * delta
        if step is not None:
            spread = math.sqrt(rw * rw + (PER_TROPHY_C * abs(delta)) ** 2)
        else:
            spread = math.sqrt(rw * rw + REFRESH_NO_STEP * REFRESH_NO_STEP)
        qs = []
        for pos, level in enumerate(levels):
            z = _Z_BY_LEVEL.get(level, Z[pos] if pos < len(Z) else 0.0)
            q = 100.0 * sigmoid(median_logit + z * spread)
            qs.append(round4_half_up(clamp_rate(q)))
        fixed = []
        prev = None
        for q in qs:
            if prev is not None and q < prev:
                q = prev
            fixed.append(q)
            prev = q
        rows.append({"id": trophy.get("id"), "q": fixed})
    return {"trophies": rows}


def main():
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(output_dir, exist_ok=True)
    for name in sorted(os.listdir(input_dir)):
        if not name.endswith(".in"):
            continue
        with open(os.path.join(input_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        result = forecast_case(case)
        stem = name[:-3]
        text = json.dumps(result, separators=(",", ":")) + "\n"
        with open(os.path.join(output_dir, stem + ".out"), "w", encoding="utf-8") as fh:
            fh.write(text)


if __name__ == "__main__":
    main()
