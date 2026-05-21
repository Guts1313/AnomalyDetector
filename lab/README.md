# Lab — bringing the AnomalyDetector into a real attack/defend environment

This folder turns the AnomalyDetector PRP from a feature-vector demo into a real lab:
attacker container generates traffic with `nmap` / `hping3` / `hydra` / `sqlmap`,
packets cross a Docker bridge network, the defender container captures them, extracts
CIC-flow features, classifies with the trained model, and adds an `iptables DROP` rule
for the attacker's IP — all triggered by clicking a preset on the FE Examples tab.

## Phases

| Phase | Goal | Folder | Status |
|------:|------|--------|--------|
| 0 | Prove the model classifies real CICFlowMeter output sensibly | `lab/sanity/` | ✅ passed |
| 1 | Attacker container running each course tool, behind `POST /attack` | `lab/attacker/` | ✅ built |
| 2 | Defender container: live capture + flow extraction + auto-block via iptables | `lab/defender/` | ✅ built |
| 3 | FE wiring: "Run on lab" button next to each preset | `frontend/src/tabs/Examples.tsx` | ✅ built |
| 4 | Integrate the same pipeline into CYBERGROUP IAM (feasibility proof) | `..` | not started |

## Topology

```
                ┌──────────────────────────────────────────┐
                │  FE (Vite dev / nginx prod)              │
                │  "Run on lab" → POST attacker:8001/attack│
                └──────────────────────┬───────────────────┘
                                       │ JSON
                                       ▼
        ┌─ ad-attacker ───────────────────────┐
        │ apt: nmap, hping3, hydra, sqlmap    │
        │ FastAPI /attack runs the right tool │
        └─────────────────┬───────────────────┘
                          │ real packets
                          ▼
        ┌─ ad-defender ───────────────────────────────────┐
        │ nginx :80, sshd :22  (victim services)          │
        │ tcpdump → cicflowmeter -i eth0 → /tmp/live.csv  │
        │ flow_streamer.py:                               │
        │   tail csv → POST api:8000/predict              │
        │   verdict.is_attack → iptables -A INPUT -s …    │
        │ /blocks endpoint (read-only iptables view)      │
        └─────────────────┬───────────────────────────────┘
                          │ POST /predict
                          ▼
                  ad-api (existing)
                          │
                          ▼
                     alerts.db → /alerts → FE Alerts tab
```

## Run it

**Step 1 — backend up:**

```bash
docker compose up -d api
```

**Step 2 — lab up (one-time build is ~3 min for the apt packages):**

```bash
docker compose -f lab/docker-compose.yml up --build -d
docker compose -f lab/docker-compose.yml ps      # both should be Up
docker logs -f ad-defender                       # follow flow_streamer + nginx + sshd
```

**Step 3 — drive it from the FE:**

Open the React FE (`npm run dev` or your nginx container), go to the **Request examples** tab, expand any category, and click **Run on lab**. Behind the scenes:

1. FE POSTs `{preset, target: "defender", duration_s: 8}` to `http://localhost:8001/attack`.
2. Attacker container runs the matching tool (eg. `nmap -sS -p 1-1024 defender`).
3. Packets traverse the `lab` bridge → defender's eth0.
4. Defender's cicflowmeter assembles flows in real-time → `/tmp/live.csv`.
5. `flow_streamer.py` POSTs each new row to `api:8000/predict`.
6. `/predict` records to `alerts.db`. FE Alerts tab will show them on next refresh.
7. If `is_attack` and `score >= 0.7`, defender runs `iptables -A INPUT -s <attacker_ip> -j DROP`.
8. Subsequent probes from the attacker time out — proof the block landed.

**Step 4 — see the block:**

```bash
curl http://localhost:8002/blocks
# {
#   "raw": "Chain INPUT ...\n1   DROP all -- 172.21.0.3 0.0.0.0/0",
#   "dropped": [{"source": "172.21.0.3", "destination": "0.0.0.0/0"}],
#   "count": 1
# }
```

Or inside the defender container:

```bash
docker exec ad-defender iptables -L INPUT -n --line-numbers
```

**Tear down:**

```bash
docker compose -f lab/docker-compose.yml down
```

## Tunables (env vars on the `defender` service)

| Var | Default | Effect |
|---|---|---|
| `ATTACK_SCORE_MIN` | `0.7` | Below this, log but don't block. |
| `BLOCK_TTL_S` | `120` | iptables rule auto-removed after this many seconds. |
| `BLOCK_ENABLED` | `1` | Set to `0` to detect-only (great for first demo recording). |
| `BLOCK_IGNORE` | `127.0.0.1` | Comma-separated IPs to never block (api, your dev box). |

## How each preset maps to a tool

| Preset | Tool | Argv |
|---|---|---|
| BENIGN | `curl` | 30 GETs / 0.3s |
| DDoS | `hping3 --flood -S` | port 80, no delay |
| DoS | `hping3 -i u500 -S` | port 80, throttled |
| PortScan | `nmap -sS -p 1-1024` | SYN scan |
| BruteForce | `hydra -L users.txt -P pass.txt ssh://` | port 22 |
| WebAttack | `sqlmap -u http://target/?id=1 --batch` | port 80 |
| Botnet | `curl …/c2/checkin?id=$i; sleep 1` | low-rate beacon |
| Infiltration | `head -c 1MB /dev/urandom \| curl --data-binary @-` | sustained outbound |

## Caveats for the LO writeup

- **Target + IDS share a container.** A real-world IDS sits inline (the IDS *is* the gateway) or behind a SPAN port. Docker bridge networks don't provide SPAN — the simplest architecture that still demonstrates the full ML → firewall loop is to put nginx/sshd and the capture in the same container. State this trade-off in your report.
- **`cap_add: NET_RAW, NET_ADMIN`** is the trust boundary. tcpdump needs raw sockets; iptables needs admin. These are scoped to the defender container's network namespace, so the host firewall is untouched.
- **Block TTL is a safety net, not a policy.** In a real deployment you'd persist blocks, age them by recent activity, and let an analyst confirm. 120s is just long enough to demonstrate during a recording.
- **The feature-name mapping (`CICFLOW_TO_API`) lives in both `lab/sanity/sanity.py` and `lab/defender/flow_streamer.py`.** Keep them in sync. If you find yourself updating it a third time, lift it into a shared Python module under `src/anomaly_detector/`.
