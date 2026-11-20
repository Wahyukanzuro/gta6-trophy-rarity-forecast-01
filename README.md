# gta6-trophy-rarity-forecast-01

[![make.fun](https://make.fun/badge/gta6-trophy-rarity-forecast-01.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![rank](https://make.fun/badge/gta6-trophy-rarity-forecast-01/Wahyukanzuro/gta6-trophy-rarity-forecast-01/rank.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)
[![reward](https://make.fun/badge/gta6-trophy-rarity-forecast-01/Wahyukanzuro/gta6-trophy-rarity-forecast-01/reward.svg)](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

Forecast how many GTA VI players earn each trophy in week one.
[Competition](https://make.fun/bounty/gta6-trophy-rarity-forecast-01)

## Entry

`main.py` (Python 3.13, stdlib only) reads every `*.in` case from
`$MAKEFUN_INPUT_DIR` (else `/input`) and writes `<id>.out` per case to
`$MAKEFUN_OUTPUT_DIR` (else `/output`):

```json
{"trophies": [{"id": 1, "q": [q05, q25, q50, q75, q95]}, ...]}
```

Run it the way the grader does:

```sh
python3 -P -s main.py
```

Deterministic, no network, no clock, no randomness. One file, no
dependencies.

## Model

Per trophy, the median is the logit of its last read rate, shifted by
**0.75x the trophy's logit move across the most recent refresh step**
visible in the case history. The spread is the random-walk term
`0.5*sqrt(d)` combined with half the absolute move:
`s_i = sqrt(RW^2 + (0.5*|Δ_i|)^2)`. When the history contains no step, a
wide refresh-aware spread `s = sqrt(RW^2 + 1.5^2)` is used for every trophy.

Why: Exophase refreshes in lumps. The Nov 20 refresh (players 14,028 →
36,080) moved rates systematically, not uniformly: early-story trophies
rose hard (Chapter 1 +2.47 logit, earners x28) while rare trophies diluted
toward zero (Δ ≈ −1.10). A symmetric spread cannot capture a directional
move — only a median shift can. The 0.75 scale is the minimax-regret pick
from final-horizon scenario expected values, not from a backtest (the
backtest cannot rank median rules: every origin's history is a single
pre-refresh plateau).

Practice is not the selection criterion: the practice histories contain no
step, so this model scores there by spread alone (~0.8 expected, vs the
house baseline ~1.5). The final case's history will contain the Nov 20
refresh, so the shift fires there.
