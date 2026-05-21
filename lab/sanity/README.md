# Phase 0 — sanity test

**Goal:** prove the trained model can classify *real* CIC-flow features (not just the
synthetic preset bodies the dashboard sends today) before we invest in building the
attacker + detector + auto-block pipeline.

## What runs

```
                       ┌─────────────────────────┐
                       │  nginx target           │  port 80, anything else closed
                       │  (sanity-target)        │
                       └────────┬────────────────┘
                                ▲ SYN scan
                                │ (nmap -sS -p 1-1000)
                       ┌────────┴────────────────┐
                       │  sanity-runner          │
                       │  tcpdump → pcap         │
                       │  cicflowmeter → CSV     │
                       │  POST /predict ─────────┼──► existing FastAPI
                       └─────────────────────────┘   (anomalydetector_default network)
```

Three things share one container (`sanity-runner`):

1. **nmap** — generates a known port-scan footprint (SYN packets to many ports, tiny
   payloads, no completed handshakes). This is exactly what your `PortScan` preset
   describes, but produced by the real course tool.
2. **tcpdump** — captures the raw packets into `/tmp/sanity.pcap`.
3. **cicflowmeter** (Python port of UNB's tool) — re-assembles packets into
   bidirectional flows and computes the CIC feature set. Output: a CSV one row per
   flow, with columns that map (with renaming) onto the `/predict` schema.

The script (`sanity.py`) then POSTs the top-N flows by packet count to `/predict` and
prints each verdict. **Phase 0 passes** if at least one flow comes back as `PortScan`
or any non-BENIGN class with a meaningful score.

## Run it

**Pre-req:** the main `docker-compose.yml` at the project root must be up so the `api`
service is reachable. From the project root:

```bash
docker compose up -d api
```

Then build and run the sanity lab:

```bash
docker compose -f lab/sanity/docker-compose.yml build
docker compose -f lab/sanity/docker-compose.yml run --rm sanity
docker compose -f lab/sanity/docker-compose.yml down
```

`run --rm` is important — it runs the one-shot script and removes the container after.

## Expected output (abbreviated)

```
=== Phase 0 sanity test ===
[1/4] API health
  ✓ API up at http://api:8000 — {'status': 'ok', ...}
[2/4] tcpdump + nmap
  ▸ tcpdump -> /tmp/sanity.pcap
  ▸ nmap -sS -p 1-1000 -T4 target
      Starting Nmap ...
      Nmap scan report for target (172.x.x.x)
      80/tcp open  http
  ✓ pcap = 123,456 bytes
[3/4] cicflowmeter
  ▸ cicflowmeter -f /tmp/sanity.pcap -c /tmp/flows/flows.csv
  ✓ wrote /tmp/flows/flows.csv (~80 kB)
[4/4] POST /predict
  ▸ 145 flows extracted; sampling top 5 by packet count

  Flow #1: 172.18.0.3:54321 -> 172.18.0.2:80 (TCP, 4 pkts)
    verdict   = PortScan
    severity  = medium
    score     = 0.81
    top class = PortScan (0.81)
  ...
```

## Interpreting the result

| Outcome | What it means | Next |
|---|---|---|
| Some flows return `PortScan` / `ATTACK` with score ≥ 0.5 | Model handles real CICFlowMeter output. | Move to Phase 1 (attacker container) and Phase 2 (detector). |
| All flows return `BENIGN` with very low scores | Model was trained only on the synthetic preset distributions and doesn't generalise to real packet timing/sizes. | Decide between (a) retraining on real CICIDS2017 pcaps, or (b) keeping the demo as preset-only and stating that limit in the LO writeup. |
| `cicflowmeter` crashes or produces 0 rows | The pcap was empty (network mis-wired) or the tool version mismatches expectations. | Run `docker compose -f lab/sanity/docker-compose.yml run --rm sanity bash` and step through interactively. |

## Things I'd flag for the LO writeup

- The CIC-flow CSV → `/predict` field mapping is in `sanity.py` (`CICFLOW_TO_API`).
  Worth screenshotting for the report — it shows you understand which features the
  model actually consumes vs. which CICFlowMeter produces.
- `tcpdump` needs `cap_add: NET_RAW` inside Docker. That's the same capability you'll
  need for the detector container in Phase 2 — and is the only "extra privilege"
  required. Document it as the trust boundary.
- The synthetic-preset bodies in `frontend/src/data/examples.ts` were tuned to land in
  each class's region of feature space. Phase 0 tests whether real packets land in the
  same regions. If they don't, that's a real research finding worth noting (not a bug).
