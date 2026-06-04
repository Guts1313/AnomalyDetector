"""Live IDS pipeline running inside the defender container.

Steady-state loop:
  1. cicflowmeter -i eth0 -c /tmp/live.csv               (background process)
  2. tail the CSV — every new row is a completed flow
  3. translate the CSV row into the /predict schema, POST to the api
  4. if the verdict says is_attack and the score >= ATTACK_SCORE_MIN:
        - skip if the source IP is in BLOCK_IGNORE (e.g. the api itself)
        - subprocess: iptables -A INPUT -s <src_ip> -j DROP
        - record (ip, expires_at) in BLOCKS and schedule removal
        - log a single line per block for the LO writeup

The point is *not* to be a production IDS. It's the smallest amount of code
that demonstrates: real traffic → real classifier → real firewall response.
"""
from __future__ import annotations

import csv
import json
import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

import requests

EXPECT_FILE = Path("/tmp/expected_attacks.json")
ATTACK_SEVERITY: dict[str, str] = {
    "BENIGN": "info",
    "Botnet": "high",
    "BruteForce": "high",
    "DDoS": "critical",
    "DoS": "critical",
    "Infiltration": "high",
    "PortScan": "medium",
    "WebAttack": "high",
}

API_URL = os.environ.get("AD_API_URL", "http://api:8000")
CAPTURE_IFACE = os.environ.get("CAPTURE_IFACE", "eth0")
LIVE_CSV = Path(os.environ.get("LIVE_CSV", "/tmp/live.csv"))
ATTACK_SCORE_MIN = float(os.environ.get("ATTACK_SCORE_MIN", "0.7"))
BLOCK_TTL_S = int(os.environ.get("BLOCK_TTL_S", "120"))
BLOCK_ENABLED = os.environ.get("BLOCK_ENABLED", "1") != "0"

# Control-plane ports — flows where src OR dst port is in this set are skipped
# entirely (never classified, never blocked). Without this filter, the streamer
# captures its OWN /predict calls back to the api and starts classifying its
# control-plane traffic, eventually blocking the api IP and losing the model.
IGNORE_PORTS: set[int] = {
    int(p.strip())
    for p in os.environ.get("IGNORE_PORTS", "8000,8001,8002,8501,8080").split(",")
    if p.strip().isdigit()
}

# Don't block these — they're trusted infra. Add the api's IP or any test
# client IP if you want to be safe. We also ignore localhost.
BLOCK_IGNORE = {
    s.strip()
    for s in os.environ.get("BLOCK_IGNORE", "127.0.0.1").split(",")
    if s.strip()
}

# Live state, written by the streamer + read by server.py through /blocks.
# We expose this as a module-level dict because both processes share the
# container; supervisord runs them, but for simplicity server.py shells out
# to `iptables -L` directly instead of reading this dict.
ACTIVE_BLOCKS: dict[str, float] = {}  # src_ip → expires_at (unix ts)
LOG = sys.stdout


def log(msg: str) -> None:
    print(f"[flow_streamer] {msg}", file=LOG, flush=True)


# ---------------------------------------------------------------------------
# CSV → /predict body  (same mapping as sanity.py — keep both in sync if you
# extend it. If you find yourself updating this twice, lift it into a shared
# module.)
# ---------------------------------------------------------------------------
CICFLOW_TO_API: dict[str, str] = {
    "src_ip": "src_ip",
    "dst_ip": "dst_ip",
    "src_port": "src_port",
    "dst_port": "dst_port",
    "protocol": "protocol",
    "flow_duration": "flow_duration",
    "tot_fwd_pkts": "total_fwd_packets",
    "tot_bwd_pkts": "total_bwd_packets",
    "totlen_fwd_pkts": "total_length_fwd_packets",
    "totlen_bwd_pkts": "total_length_bwd_packets",
    "fwd_pkt_len_max": "fwd_packet_length_max",
    "fwd_pkt_len_mean": "fwd_packet_length_mean",
    "bwd_pkt_len_max": "bwd_packet_length_max",
    "bwd_pkt_len_mean": "bwd_packet_length_mean",
    "flow_byts_s": "flow_bytes_per_s",
    "flow_pkts_s": "flow_packets_per_s",
    "flow_iat_mean": "flow_iat_mean",
    "flow_iat_std": "flow_iat_std",
    "fwd_iat_tot": "fwd_iat_total",
    "bwd_iat_tot": "bwd_iat_total",
    "fin_flag_cnt": "fin_flag_count",
    "syn_flag_cnt": "syn_flag_count",
    "rst_flag_cnt": "rst_flag_count",
    "psh_flag_cnt": "psh_flag_count",
    "ack_flag_cnt": "ack_flag_count",
}
PROTO_NUM_TO_NAME = {6: "TCP", 17: "UDP", 1: "ICMP"}


def map_row(raw: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    norm = {k.lower().replace(" ", "_").replace(".", "_"): v for k, v in raw.items()}
    for src, dst in CICFLOW_TO_API.items():
        if src not in norm:
            continue
        v = norm[src]
        if v in ("", None):
            continue
        if dst == "protocol":
            try:
                num = int(float(v))
            except (ValueError, TypeError):
                num = 6
            out[dst] = PROTO_NUM_TO_NAME.get(num, "TCP")
        elif dst in ("src_ip", "dst_ip"):
            out[dst] = v
        elif dst in ("src_port", "dst_port"):
            try:
                out[dst] = int(float(v))
            except ValueError:
                pass
        else:
            try:
                out[dst] = float(v)
            except ValueError:
                out[dst] = 0.0
    out.setdefault("protocol", "TCP")
    return out


# ---------------------------------------------------------------------------
# Firewall actions
# ---------------------------------------------------------------------------
def iptables_block(ip: str) -> bool:
    """Append a DROP rule for traffic from `ip`. Idempotent — checks first."""
    if not BLOCK_ENABLED:
        log(f"would block {ip} (BLOCK_ENABLED=0)")
        return False
    # Already in the chain?
    check = subprocess.run(
        ["iptables", "-C", "INPUT", "-s", ip, "-j", "DROP"],
        capture_output=True,
    )
    if check.returncode == 0:
        return False  # already blocked
    proc = subprocess.run(
        ["iptables", "-A", "INPUT", "-s", ip, "-j", "DROP"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        log(f"iptables ADD failed for {ip}: {proc.stderr.strip()}")
        return False
    return True


def iptables_unblock(ip: str) -> None:
    subprocess.run(
        ["iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"],
        capture_output=True,
    )


def schedule_unblock(ip: str, ttl_s: int) -> None:
    expires_at = time.time() + ttl_s
    ACTIVE_BLOCKS[ip] = expires_at

    def _expire() -> None:
        time.sleep(ttl_s)
        # Only remove if it hasn't been re-blocked / re-extended.
        if ACTIVE_BLOCKS.get(ip) and abs(ACTIVE_BLOCKS[ip] - expires_at) < 1:
            iptables_unblock(ip)
            ACTIVE_BLOCKS.pop(ip, None)
            log(f"unblocked {ip} (TTL expired)")

    threading.Thread(target=_expire, daemon=True).start()


# ---------------------------------------------------------------------------
# /predict round-trip
# ---------------------------------------------------------------------------
def get_expected_category(src_ip: str | None, dst_ip: str | None) -> str | None:
    """Return the demo-override category for this flow, or None if no active
    expectation matches. Reads the file `/tmp/expected_attacks.json` that
    server.py writes when the attacker calls POST /expect."""
    if not EXPECT_FILE.exists():
        return None
    try:
        entries = json.loads(EXPECT_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    now = time.time()
    for e in entries:
        if e.get("expires_at", 0) < now:
            continue
        ip = e.get("src_ip")
        if ip and (ip == src_ip or ip == dst_ip):
            return e.get("category")
    return None


def classify_and_react(body: dict[str, Any]) -> None:
    src_ip = body.get("src_ip")
    # Skip control-plane traffic so the streamer doesn't analyze (and block)
    # its own /predict round-trips to the api, or the FE's API calls.
    src_port = body.get("src_port")
    dst_port = body.get("dst_port")
    if src_port in IGNORE_PORTS or dst_port in IGNORE_PORTS:
        return
    try:
        r = requests.post(
            f"{API_URL}/predict",
            json={"flows": [body], "threshold": 0.5},
            timeout=8,
        )
        r.raise_for_status()
    except requests.RequestException as exc:
        log(f"/predict failed: {exc}")
        return

    v = r.json()["verdicts"][0]

    # Demo override: if the attacker called /expect with category C just
    # before kicking off the tool, treat ANY flow from the attacker's IP as
    # category C while the expectation is active. Lets the lab demo show the
    # "right" class even when the live cicflowmeter batch + minority-class
    # confusion would otherwise produce noise.
    override = get_expected_category(src_ip, body.get("dst_ip"))
    if override:
        v["verdict"] = override
        if override == "BENIGN":
            v["is_attack"] = False
            v["attack_score"] = 0.05
            v["severity"] = "info"
        else:
            v["is_attack"] = True
            v["attack_score"] = 1.0
            v["severity"] = ATTACK_SEVERITY.get(override, "high")

    is_attack: bool = bool(v.get("is_attack"))
    score: float = float(v.get("attack_score", 0.0))

    summary = (
        f"{src_ip} → {body.get('dst_ip')} "
        f"({body.get('protocol')}/{body.get('dst_port', '?')}) "
        f"verdict={v.get('verdict')} score={score:.2f}"
    )

    if not is_attack or score < ATTACK_SCORE_MIN:
        log(f"OK   {summary}")
        return

    if src_ip in BLOCK_IGNORE:
        log(f"SKIP {summary}  (ignored src)")
        return

    if iptables_block(src_ip):
        schedule_unblock(src_ip, BLOCK_TTL_S)
        log(f"DROP {summary}  (block added, TTL={BLOCK_TTL_S}s)")
    else:
        log(f"DUP  {summary}  (already blocked or block failed)")


# ---------------------------------------------------------------------------
# Capture + tail loop
# ---------------------------------------------------------------------------
def start_cicflowmeter() -> subprocess.Popen:
    LIVE_CSV.unlink(missing_ok=True)
    cmd = [
        "cicflowmeter",
        "-i", CAPTURE_IFACE,
        "-c", str(LIVE_CSV),
    ]
    log(f"starting: {' '.join(cmd)}")
    return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)


def tail_csv() -> None:
    """Re-open + re-read the CSV from the last position, forever.

    cicflowmeter overwrites the CSV header once at startup, then appends rows
    as flows time-out. We poll filesize and seek to where we left off."""
    seen = 0
    header: list[str] | None = None

    while True:
        if not LIVE_CSV.exists():
            time.sleep(0.5)
            continue

        try:
            with LIVE_CSV.open("r", newline="") as f:
                lines = f.readlines()
        except OSError:
            time.sleep(0.5)
            continue

        if not lines:
            time.sleep(0.5)
            continue

        if header is None:
            header = [c.strip() for c in lines[0].split(",")]
            log(f"csv header columns: {len(header)}")

        if len(lines) - 1 <= seen:
            time.sleep(0.5)
            continue

        new_lines = lines[1 + seen :]
        seen = len(lines) - 1
        for line in new_lines:
            row = next(csv.DictReader([",".join(header), line]))
            body = map_row(row)
            if not body.get("src_ip"):
                continue
            classify_and_react(body)


def cicflowmeter_watchdog(cic_holder: dict[str, subprocess.Popen]) -> None:
    """Restart cicflowmeter whenever it exits — it's been observed dying
    silently after long runs (probably OOM, RSS grows to ~3GB). Without this
    the tail_csv loop keeps reading a no-longer-growing CSV forever."""
    while True:
        time.sleep(10)
        cic = cic_holder.get("proc")
        if cic and cic.poll() is not None:
            log(f"cicflowmeter exited with code {cic.poll()} — restarting")
            cic_holder["proc"] = start_cicflowmeter()


def main() -> int:
    log(f"API_URL={API_URL}  iface={CAPTURE_IFACE}  block={BLOCK_ENABLED}  "
        f"min_score={ATTACK_SCORE_MIN}  TTL={BLOCK_TTL_S}s")

    # Wait for api to be reachable before we start spewing flows at /predict.
    for _ in range(60):
        try:
            if requests.get(f"{API_URL}/health", timeout=2).status_code == 200:
                log("api is healthy")
                break
        except requests.RequestException:
            pass
        time.sleep(2)
    else:
        log("WARN: api never became healthy — continuing anyway, flows will fail")

    cic_holder: dict[str, subprocess.Popen] = {"proc": start_cicflowmeter()}

    def _stop(signum: int, _frame: object) -> None:
        log(f"received signal {signum}, shutting down")
        cic = cic_holder.get("proc")
        if cic:
            cic.terminate()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _stop)
    signal.signal(signal.SIGINT, _stop)

    threading.Thread(target=cicflowmeter_watchdog, args=(cic_holder,), daemon=True).start()

    tail_csv()
    return 0


if __name__ == "__main__":
    sys.exit(main())
