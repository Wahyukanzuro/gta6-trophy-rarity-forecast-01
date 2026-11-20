#!/usr/bin/env python3
"""gta6-trophy-rarity-forecast-01: week-one trophy-rate forecaster.

Model (fit report v2): each trophy's median is the logit of its last read
rate, shifted by 0.75x the trophy's logit move across the most recent
refresh step visible in the case history; the spread is the random-walk term
combined with half the absolute move. When the history has no step, a wide
refresh-aware spread is used instead. Stdlib only, deterministic, no
network, no clock, no randomness.
"""

import json
import math
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

SHIFT_SCALE = 0.75
PER_TROPHY_C = 0.5
REFRESH_NO_STEP = 1.5
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]
RATE_LO = 0.01
RATE_HI = 99.99
EXPECTED_LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]


def clamp_rate(rate):
    """Clamp a percent rate into the scorer's [0.01, 99.99] window."""
    if rate < RATE_LO:
        return RATE_LO
    if rate > RATE_HI:
        return RATE_HI
    return rate


def logit_pct(rate):
    """Logit of a percent rate: ln(r / (100 - r)), clamped first."""
    r = clamp_rate(rate)
    return math.log(r / (100.0 - r))


def logistic_pct(x):
    """Inverse logit in percent: 100 / (1 + exp(-x)), overflow-safe."""
    if x >= 0.0:
        return 100.0 / (1.0 + math.exp(-x))
    ex = math.exp(x)
    return 100.0 * ex / (1.0 + ex)


def round4_number(value):
    """Round to 4 decimals, half-up; whole numbers come out as ints."""
    q = Decimal(repr(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    if q == q.to_integral_value():
        return int(q)
    return float(q)


def rate_at_or_before(history, index, trophy_pos):
    """Newest non-null rate for a trophy at or before a history index."""
    for k in range(index, -1, -1):
        rates = history[k].get("rates") or []
        if trophy_pos < len(rates) and rates[trophy_pos] is not None:
            return rates[trophy_pos]
    return RATE_LO


def last_rate(history, trophy_pos):
    """Newest non-null rate for a trophy in the whole history."""
    return rate_at_or_before(history, len(history) - 1, trophy_pos)


def find_step(history):
    """Latest history index j >= 1 where the read changed vs j-1.

    A change is an exact difference of the whole rates list (None counts
    as a value) or a difference in players_tracked. Returns None when the
    history is a single plateau.
    """
    for j in range(len(history) - 1, 0, -1):
        if history[j].get("rates") != history[j - 1].get("rates"):
            return j
        if history[j].get("players_tracked") != history[j - 1].get("players_tracked"):
            return j
    return None


def forecast_case(case):
    """Forecast one case dict into the output dict."""
    levels = case.get("levels")
    if levels != EXPECTED_LEVELS:
        raise ValueError("unexpected levels: %r" % (levels,))
    trophies = case.get("trophies")
    if not trophies:
        raise ValueError("case has no trophies")
    history = case.get("history")
    if not history:
        raise ValueError("case has no history")
    horizon = case.get("horizon_minutes")
    if horizon is None:
        raise ValueError("case has no horizon_minutes")
    days = float(horizon) / 1440.0
    rw = 0.5 * math.sqrt(days)
    step = find_step(history)
    rows = []
    for pos, trophy in enumerate(trophies):
        last = last_rate(history, pos)
        if step is None:
            delta = 0.0
            spread = math.sqrt(rw * rw + REFRESH_NO_STEP * REFRESH_NO_STEP)
        else:
            after = rate_at_or_before(history, step, pos)
            before = rate_at_or_before(history, step - 1, pos)
            delta = logit_pct(after) - logit_pct(before)
            spread = math.sqrt(rw * rw + (PER_TROPHY_C * abs(delta)) ** 2)
        median_logit = logit_pct(last) + SHIFT_SCALE * delta
        quantiles = []
        for z in Z:
            value = clamp_rate(logistic_pct(median_logit + z * spread))
            quantiles.append(round4_number(value))
        rows.append({"id": trophy["id"], "q": quantiles})
    return {"trophies": rows}


def main(argv):
    input_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    output_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(output_dir, exist_ok=True)
    names = sorted(n for n in os.listdir(input_dir) if n.endswith(".in"))
    for name in names:
        stem = name[:-3]
        with open(os.path.join(input_dir, name), "r", encoding="utf-8") as fh:
            case = json.load(fh)
        result = forecast_case(case)
        text = json.dumps(result, separators=(",", ":")) + "\n"
        with open(os.path.join(output_dir, stem + ".out"), "w", encoding="utf-8") as fh:
            fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
