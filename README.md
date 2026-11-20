# gta6-trophy-rarity-forecast-01 — v2

Forecast how many GTA VI players earn each trophy in week one.
Competition: https://make.fun/bounty/gta6-trophy-rarity-forecast-01

[![make.fun](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/Wahyukanzuro/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/Wahyukanzuro/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

## Model (v2)

Single-file Python 3.13 program (`main.py`), stdlib only, no network,
deterministic. It reads every `*.in` case in `$MAKEFUN_INPUT_DIR` (else
`/input`) and writes one `<id>.out` per case to `$MAKEFUN_OUTPUT_DIR`
(else `/output`).

Per trophy, the median is the last read's logit shifted by **0.50x the
per-trophy logit move across the most recent step** in the case's own
history (the step is the latest read whose rates list or
players-tracked count differs from its predecessor). The spread is a
**random walk only, s = 0.5 * sqrt(d)** in logit space (d = horizon in
days); the per-trophy spread term is disabled (`PER_TROPHY_C = 0.0`).
When the history contains no step at all, the spread widens to
**sqrt((0.5 * sqrt(d))^2 + 1.5^2)** to cover a refresh the case has
not seen yet. Quantiles are rounded half-up to 4 decimals and clamped
to [0.01, 99.99].

Worked example at the final horizon (d = 4.5208 days): Chapter 1
("Paradise Lost") last read 11.98%, most-recent step +0.086 logit, so
the median is **12.4422%** with quantiles
[2.4126, 6.4904, 12.4422, 22.5366, 44.9576].

v2 supersedes v1 (shift 0.75x, per-trophy spread): three refresh steps
were measured on the live Exophase trajectory and the later steps are
far smaller than the first, so the shift scale drops to 0.50 and the
spread drops to random-walk only. The expected edge over the house
baseline on the final case is small (about 0.005 in the central
scenario) — this is a calibration refinement, not a blowout.

## Run

```sh
python3 -P -s main.py
```

## License

MIT — see [LICENSE](LICENSE).
