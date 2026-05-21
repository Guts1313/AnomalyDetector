"""Phase 0 sanity test for the AnomalyDetector model.

End-to-end:
  1. Wait until the existing FastAPI /health says "ok".
  2. Start tcpdump in the background, writing to a pcap.
  3. Run an nmap SYN scan against the `target` nginx container.
  4. Stop tcpdump.
  5. Run cicflowmeter to convert the pcap into a CIC-flow CSV.
  6. Pick the most data-rich flows from the CSV and POST them to /predict.
  7. Print each verdict + class probabilities so we can eyeball whether the
     model can recognise a real port scan as PortScan (or at least non-BENIGN).

The point is *not* to be production code. It's the minimum amount of glue
needed to answer one question: does the model survive real CICFlowMeter
output, or do we need to retrain on real CICIDS2017 captures?
"""
from __future__ import annotations

import csv
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

API_URL = os.environ.get("AD_API_URL", "http://api:8000")
TARGET = os.environ.get("SCAN_TARGET", "target")
PCAP_PATH = Path("/tmp/sanity.pcap")
CSV_DIR = Path("/tmp/flows")


# ---------------------------------------------------------------------------
# Step 1 — wait for API
# ---------------------------------------------------------------------------
def wait_api_ready(timeout_s: int = 60) -> None:
    """Block until /health returns ok, or bail out."""
    deadline = time.time() + timeout_s
    last_err: str = "<no attempt>"
    while time.time() < deadline:
        try:
            r = requests.get(f"{API_URL}/health", timeout=2)
            if r.status_code == 200 and r.json().get("status") == "ok":
                print(f"  ✓ API up at {API_URL} — {r.json()}")
                return
            last_err = f"status={r.status_code} body={r.text[:120]}"
        except requests.RequestException as exc:
            last_err = str(exc)
        time.sleep(2)
    raise SystemExit(f"API not reachable at {API_URL}. Last error: {last_err}")


# ---------------------------------------------------------------------------
# Step 2-4 — capture + attack + stop
# ---------------------------------------------------------------------------
def capture_and_scan() -> None:
    """Start tcpdump, run nmap, then cleanly stop tcpdump."""
    PCAP_PATH.unlink(missing_ok=True)

    # -i any: capture on all interfaces (the scan goes out of eth0 to the lab network)
    # -U:     don't buffer — flush each packet immediately so a SIGINT loses nothing
    # host TARGET: only packets to/from the target — keeps the pcap focused
    print(f"  ▸ tcpdump -> {PCAP_PATH}")
    tcpdump = subprocess.Popen(
        ["tcpdump", "-i", "any", "-U", "-w", str(PCAP_PATH), "host", TARGET],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    # Give libpcap a moment to bind before we start firing packets.
    time.sleep(1.5)

    print(f"  ▸ nmap -sS -p 1-1000 -T4 {TARGET}")
    nmap = subprocess.run(
        ["nmap", "-sS", "-p", "1-1000", "-T4", "-Pn", TARGET],
        capture_output=True,
        text=True,
        check=False,
    )
    print(_indent(nmap.stdout, 6))
    if nmap.returncode != 0:
        print(f"    nmap exited {nmap.returncode}: {nmap.stderr[:300]}")

    # SIGINT is the polite way to stop tcpdump — it flushes the pcap properly.
    time.sleep(1.0)
    tcpdump.send_signal(signal.SIGINT)
    try:
        tcpdump.wait(timeout=8)
    except subprocess.TimeoutExpired:
        tcpdump.kill()
    print(f"  ✓ pcap = {PCAP_PATH.stat().st_size:,} bytes")


# ---------------------------------------------------------------------------
# Step 5 — pcap → CIC flow CSV
# ---------------------------------------------------------------------------
def extract_flows() -> Path:
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    # cicflowmeter writes one CSV per pcap into the directory we point it at.
    cmd = ["cicflowmeter", "-f", str(PCAP_PATH), "-c", str(CSV_DIR / "flows.csv")]
    print(f"  ▸ {' '.join(cmd)}")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        print(_indent(proc.stdout, 6))
        print(_indent(proc.stderr, 6))
        raise SystemExit(f"cicflowmeter failed ({proc.returncode})")

    candidates = sorted(CSV_DIR.glob("*.csv"))
    if not candidates:
        raise SystemExit(f"No CSV produced under {CSV_DIR}")
    print(f"  ✓ wrote {candidates[0]} ({candidates[0].stat().st_size:,} bytes)")
    return candidates[0]


# ---------------------------------------------------------------------------
# Step 6 — translate one row of CSV into the /predict body
# ---------------------------------------------------------------------------
# cicflowmeter (Python) uses these column names; our /predict schema uses
# different names. This dict maps the FROM (CSV column) to TO (API field).
# If a key here doesn't exist in the CSV (different cicflowmeter version),
# it's silently skipped and the field falls back to its server-side default.
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

# IP protocol numbers → string the schema expects.
PROTO_NUM_TO_NAME = {6: "TCP", 17: "UDP", 1: "ICMP"}


def map_row(raw: dict[str, str]) -> dict[str, Any]:
    """One row of cicflowmeter CSV → /predict FlowRecord."""
    out: dict[str, Any] = {}
    # Normalise column names: lower-case, replace spaces and dots with underscores.
    norm = {k.lower().replace(" ", "_").replace(".", "_"): v for k, v in raw.items()}

    for src, dst in CICFLOW_TO_API.items():
        if src not in norm:
            continue
        v = norm[src]
        if v == "" or v is None:
            continue

        if dst == "protocol":
            # cicflowmeter occasionally writes 0 for short/incomplete flows.
            # We know the scan was TCP, so any non-UDP/ICMP value falls back to TCP
            # rather than the model-unfriendly "OTHER".
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


def post_top_flows(csv_path: Path, n: int = 5) -> None:
    rows = list(csv.DictReader(csv_path.open()))
    if not rows:
        raise SystemExit("CSV had no rows — did the scan generate any traffic?")
    print(f"  ▸ {len(rows)} flows extracted; sampling top {n} by packet count")

    def packets(r: dict[str, str]) -> float:
        try:
            return float(r.get("tot fwd pkts", r.get("tot_fwd_pkts", 0)) or 0) + float(
                r.get("tot bwd pkts", r.get("tot_bwd_pkts", 0)) or 0
            )
        except ValueError:
            return 0.0

    rows.sort(key=packets, reverse=True)

    for i, raw in enumerate(rows[:n]):
        body = map_row(raw)
        print(
            f"\n  Flow #{i+1}: {body.get('src_ip')}:{body.get('src_port', '?')} "
            f"-> {body.get('dst_ip')}:{body.get('dst_port', '?')} "
            f"({body.get('protocol')}, {packets(raw):.0f} pkts)"
        )
        resp = requests.post(
            f"{API_URL}/predict",
            json={"flows": [body], "threshold": 0.5},
            timeout=10,
        )
        resp.raise_for_status()
        v = resp.json()["verdicts"][0]
        cls = v.get("class_probabilities") or {}
        top = max(cls.items(), key=lambda kv: kv[1]) if cls else ("?", 0.0)
        print(f"    verdict   = {v['verdict']}")
        print(f"    severity  = {v['severity']}")
        print(f"    score     = {v['attack_score']:.3f}")
        print(f"    top class = {top[0]} ({top[1]:.3f})")


# ---------------------------------------------------------------------------
# Glue
# ---------------------------------------------------------------------------
def _indent(text: str, n: int) -> str:
    pad = " " * n
    return "\n".join(pad + line for line in (text or "").splitlines() if line.strip())


def main() -> int:
    print("=== Phase 0 sanity test ===")
    print("[1/4] API health")
    wait_api_ready()
    print("[2/4] tcpdump + nmap")
    capture_and_scan()
    print("[3/4] cicflowmeter")
    csv_path = extract_flows()
    print("[4/4] POST /predict")
    post_top_flows(csv_path)
    print("\n=== Done ===")
    print("If at least one flow above shows verdict=PortScan (or any non-BENIGN")
    print("class with a meaningful probability), the model handles real")
    print("CICFlowMeter output. We're clear to build Phase 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
