# Retrain the model on real lab traffic

When the model classifies real attacks as `Botnet` because it was trained on
the synthetic preset distributions rather than real CICFlowMeter output, this
script fixes that — it captures fresh traffic from each attack preset, labels
it, mixes it with the original synthetic dataset (so the FE "Send to /predict"
buttons still behave), retrains, and hot-reloads the model.

Total run time: ~8 categories × 30 seconds capture + ~1 minute training +
~1 second reload = **~5 minutes**.

## Pre-reqs

- Root compose `api` service up: `docker compose up -d api`
- Lab compose up: `docker compose -f lab/docker-compose.yml up -d`
- Python 3.9+ on the host (stdlib only — no extra pip installs)

## Run

```bash
bash lab/retrain/retrain.sh
```

Tunables (env vars):

| Var | Default | Meaning |
|---|---|---|
| `DURATION` | `30` | Seconds of attack traffic per category |
| `MIX` | `yes` | Mix lab captures with the original synthetic dataset (`no` for lab-only) |
| `ALGO` | `gradient_boosting` | Which algorithm to persist as the production model |

Example:

```bash
DURATION=60 MIX=no ALGO=random_forest bash lab/retrain/retrain.sh
```

## What it does

1. **Sanity check** all three containers are up.
2. **Pauses** the live flow_streamer so it doesn't compete with the capture.
3. **Flushes** any iptables blocks (otherwise re-runs of the same attack would be dropped).
4. For each of the 8 categories: spawns `tcpdump` in the defender, POSTs to the
   attacker's `/attack`, waits for the duration + 2 seconds, stops tcpdump,
   runs `cicflowmeter` on the pcap, copies the CSV into `data/raw/lab_captured/`.
5. **Resumes** the live flow_streamer.
6. **Merges** the 8 CSVs into `data/raw/lab_dataset.csv` via `merge.py`.
   With `MIX=yes`, down-samples the synthetic dataset to 500 rows/class and
   appends — gives the model both real and synthetic patterns to learn from.
7. **Trains** by `docker exec`-ing into `ad-api` and running
   `scripts/train.py` against the merged CSV.
8. **Reloads** the api: `POST /admin/reload`.
9. Prints the new `/health`.

## Verifying the result

Click any preset's **Run on lab** in the FE Examples tab and watch
`docker logs -f ad-defender` — the verdicts should now match the category most
of the time. Class confusion should drop a lot (especially DoS/WebAttack no
longer drifting into Botnet).

## Notes for the LO writeup

- This pipeline is the answer to the "domain shift" problem flagged in Phase 0:
  the synthetic training distribution didn't match real CICFlowMeter output.
- We retain the synthetic data in the mix so the "Send to /predict" feature
  vector buttons in the FE still produce expected verdicts — important for the
  evidence dossier, otherwise the recorded screenshots from week N stop
  matching the model on week N+1.
- The capture filter (`host attacker`) keeps the pcap focused on the attack
  flow — control-plane chatter between the defender and the api is filtered
  out, so the training data is clean.
- Per-category capture duration matters: 30 seconds gives the gradient
  boosting model ~50-300 flows per class. For an LO-grade dataset, run with
  `DURATION=120` to get ~200-1500 flows per class.
