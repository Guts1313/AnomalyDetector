#!/usr/bin/env bash
# Retrain the model on real lab traffic.
#
# For each of 8 categories:
#   1. start tcpdump inside ad-defender (background)
#   2. trigger the matching attack via the FE attacker API
#   3. wait for it to complete, stop tcpdump
#   4. run cicflowmeter on the pcap -> CSV of labeled flow features
# Then:
#   5. merge all 8 CSVs into a single labeled training set
#   6. (optional) mix with the existing synthetic_flows.csv
#   7. copy into the api container and run scripts/train.py
#   8. POST /admin/reload so the new model goes live
#
# Run from project root:
#   bash lab/retrain/retrain.sh
#
# Tunables (env vars):
#   DURATION  — seconds per category (default: 30)
#   MIX       — "yes" to mix with synthetic_flows.csv (default), "no" for lab-only
#   ALGO      — algorithm to persist as the production model (default: gradient_boosting)

set -euo pipefail

# Disable MSYS / Git-Bash path conversion. Without this, paths like
# /tmp/cap_BENIGN.pcap that we send to `docker exec` get rewritten to
# C:/Users/.../AppData/Local/Temp/cap_BENIGN.pcap before docker sees them,
# tcpdump inside the container tries to write to a Windows path that
# doesn't exist, and every pcap comes back 0 bytes.
export MSYS_NO_PATHCONV=1
export MSYS2_ARG_CONV_EXCL="*"

DURATION="${DURATION:-30}"
MIX="${MIX:-yes}"
ALGO="${ALGO:-gradient_boosting}"

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$ROOT/data/raw/lab_captured"
mkdir -p "$OUT_DIR"

# MSYS_NO_PATHCONV=1 keeps /tmp/foo intact for `docker exec`, but it ALSO stops
# docker cp from converting host paths to native Windows form, which breaks
# host-side targets. So we explicitly convert host paths via cygpath when
# they're going to docker cp. On Linux cygpath isn't installed; fall back to
# the original path.
host_path() {
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -w "$1"
    else
        printf '%s\n' "$1"
    fi
}

DEFAULT_CATS=(BENIGN PortScan DDoS DoS BruteForce WebAttack Botnet Infiltration)
# CATS env var can override: `CATS="WebAttack Infiltration" bash retrain.sh`
if [ -n "${CATS:-}" ]; then
    # shellcheck disable=SC2206
    CATS=($CATS)
else
    CATS=("${DEFAULT_CATS[@]}")
fi
echo "[setup] categories to re-capture: ${CATS[*]}"

# --- Sanity: lab must be up ---------------------------------------------------
if ! docker ps --format '{{.Names}}' | grep -q '^ad-defender$'; then
    echo "ad-defender not running. Bring up the lab first:"
    echo "  docker compose -f lab/docker-compose.yml up -d"
    exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -q '^ad-attacker$'; then
    echo "ad-attacker not running. Bring up the lab first:"
    exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -q '^ad-api$'; then
    echo "ad-api not running. Start it: docker compose up -d api"
    exit 1
fi

# --- Stop the live IDS streamer so it doesn't compete for the pcap file -------
echo "[setup] pausing flow_streamer so capture runs cleanly"
docker exec ad-defender supervisorctl stop flow_streamer || true

# Also clear any existing iptables blocks — otherwise some attacks will be
# dropped before the capture sees them.
echo "[setup] flushing iptables INPUT chain on defender"
docker exec ad-defender iptables -F INPUT || true

# --- Capture phase ------------------------------------------------------------
for CAT in "${CATS[@]}"; do
    echo
    echo "================================================================="
    echo "[$CAT] capturing ${DURATION}s of traffic"
    echo "================================================================="

    PCAP=/tmp/cap_${CAT}.pcap
    docker exec ad-defender rm -f "$PCAP" || true

    # tcpdump in background — host filter so we only see attacker traffic.
    # -c 100000 caps the capture at 100k packets so an unexpectedly loud
    # preset (e.g. --flood) can't dump 10M packets that cicflowmeter then
    # can't parse without eating 20+ GB of RAM.
    docker exec -d ad-defender bash -c "tcpdump -i eth0 -U -c 100000 -w $PCAP host attacker"
    sleep 1.5

    # Fire the attack via the FE's HTTP control plane
    echo "[$CAT] POST /attack"
    curl -s -X POST "http://localhost:8001/attack" \
        -H "Content-Type: application/json" \
        -d "{\"preset\":\"$CAT\",\"target\":\"defender\",\"duration_s\":$DURATION}" \
        -o "/tmp/attack_${CAT}.json" --max-time $((DURATION + 30)) || true

    # tcpdump catches the tail of late packets
    sleep 2
    docker exec ad-defender pkill -INT tcpdump || true
    sleep 1

    SIZE=$(docker exec ad-defender stat -c %s "$PCAP" 2>/dev/null || echo 0)
    echo "[$CAT] pcap = $SIZE bytes"

    if [ "$SIZE" -lt 1024 ]; then
        echo "[$CAT] pcap too small — skipping (probably attack tool failed)"
        continue
    fi

    echo "[$CAT] running cicflowmeter (capped at 120s)"
    # `timeout 120` so a runaway preset can't keep cicflowmeter spinning.
    docker exec ad-defender bash -c \
        "rm -rf /tmp/flows_${CAT} && mkdir -p /tmp/flows_${CAT} && \
         timeout 120 cicflowmeter -f $PCAP -c /tmp/flows_${CAT}/flows.csv" \
        || { echo "[$CAT] cicflowmeter failed or timed out — skipping"; continue; }

    docker cp "ad-defender:/tmp/flows_${CAT}/flows.csv" "$(host_path "$OUT_DIR/${CAT}.csv")"
    ROWS=$(wc -l < "$OUT_DIR/${CAT}.csv")
    echo "[$CAT] wrote $OUT_DIR/${CAT}.csv  (${ROWS} rows)"
done

# --- Restart the live streamer ------------------------------------------------
echo
echo "[teardown] resuming flow_streamer"
docker exec ad-defender supervisorctl start flow_streamer || true

# --- Merge phase --------------------------------------------------------------
echo
echo "[merge] combining into a single labeled dataset"
MERGED="$ROOT/data/raw/lab_dataset.csv"
SYNTH_ARG=""
if [ "$MIX" = "yes" ] && [ -f "$ROOT/data/raw/synthetic_flows.csv" ]; then
    SYNTH_ARG="yes"
    echo "[merge] mixing with synthetic_flows.csv (down-sampled per category)"
fi
LAB_CAP="${LAB_CAP:-3000}"
SYNTH_CAP="${SYNTH_CAP:-1500}"
echo "[merge] lab cap = $LAB_CAP/class, synthetic cap = $SYNTH_CAP/class"
python "$(host_path "$ROOT/lab/retrain/merge.py")" \
    --captures-dir "$(host_path "$OUT_DIR")" \
    --out "$(host_path "$MERGED")" \
    --lab-cap "$LAB_CAP" \
    --synthetic-cap "$SYNTH_CAP" \
    ${SYNTH_ARG:+--synthetic "$(host_path "$ROOT/data/raw/synthetic_flows.csv")"}

# --- Train phase --------------------------------------------------------------
echo
echo "[train] copying dataset into ad-api and retraining ($ALGO)"
docker cp "$(host_path "$MERGED")" ad-api:/app/data/lab_dataset.csv

# /app/models is mounted read-only on the api container, so we train into /tmp
# inside the container, then copy the new artifacts out to the host's ./models/
# (which is what the mount points at). The api re-reads them on /admin/reload.
docker exec ad-api bash -c "rm -rf /tmp/models && mkdir -p /tmp/models"
docker exec ad-api python -m scripts.train \
    --data /app/data/lab_dataset.csv \
    --out-dir /tmp/models \
    --prefer "$ALGO"

echo
echo "[train] copying new model out to host ./models/"
docker cp ad-api:/tmp/models/best.joblib              "$(host_path "$ROOT/models/best.joblib")"
docker cp ad-api:/tmp/models/comparison_matrix.csv    "$(host_path "$ROOT/models/comparison_matrix.csv")" || true
docker cp ad-api:/tmp/models/comparison_matrix.md     "$(host_path "$ROOT/models/comparison_matrix.md")"  || true

# --- Reload -------------------------------------------------------------------
echo
echo "[reload] POST /admin/reload"
curl -s -X POST http://localhost:8000/admin/reload | head -c 400; echo

# --- Quick health check after reload ------------------------------------------
echo
echo "[done] /health says:"
curl -s http://localhost:8000/health
echo
echo "Now click the same lab preset again and check the verdicts —"
echo "they should match the category much more often."
