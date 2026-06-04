"""Merge per-category cicflowmeter CSVs into a labeled training set.

Optionally down-samples the existing synthetic dataset so it doesn't drown out
the real lab captures, then concatenates everything.

Output columns match the canonical schema (FLOW_FEATURE_COLUMNS + label +
src/dst metadata), so scripts/train.py can consume the CSV directly.

Pure Python stdlib — no pandas, so this runs on any host with Python 3.9+.
"""
from __future__ import annotations

import argparse
import csv
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# Canonical schema (mirrors src/anomaly_detector/features/schema.py).
NUMERIC_FEATURES = [
    "flow_duration",
    "total_fwd_packets",
    "total_bwd_packets",
    "total_length_fwd_packets",
    "total_length_bwd_packets",
    "fwd_packet_length_max",
    "fwd_packet_length_mean",
    "bwd_packet_length_max",
    "bwd_packet_length_mean",
    "flow_bytes_per_s",
    "flow_packets_per_s",
    "flow_iat_mean",
    "flow_iat_std",
    "fwd_iat_total",
    "bwd_iat_total",
    "fin_flag_count",
    "syn_flag_count",
    "rst_flag_count",
    "psh_flag_count",
    "ack_flag_count",
]
CATEGORICAL_FEATURES = ["protocol"]
META_FEATURES = ["src_ip", "dst_ip", "src_port", "dst_port"]
OUT_COLUMNS = NUMERIC_FEATURES + CATEGORICAL_FEATURES + ["label"] + META_FEATURES

# cicflowmeter (Python 0.2.x) column → our canonical column.
CICFLOW_TO_CANONICAL: dict[str, str] = {
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


def normalize_row(raw: dict[str, str], label: str) -> dict[str, Any] | None:
    """Translate one cicflowmeter CSV row into the canonical schema."""
    out: dict[str, Any] = {c: 0 for c in NUMERIC_FEATURES}
    out["protocol"] = "TCP"
    out["label"] = label
    for c in META_FEATURES:
        out[c] = ""

    norm = {k.lower().replace(" ", "_").replace(".", "_"): v for k, v in raw.items()}
    for src, dst in CICFLOW_TO_CANONICAL.items():
        if src not in norm:
            continue
        v = norm[src]
        if v in ("", None):
            continue
        if dst == "protocol":
            try:
                num = int(float(v))
                out[dst] = PROTO_NUM_TO_NAME.get(num, "TCP")
            except (ValueError, TypeError):
                out[dst] = "TCP"
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

    # Drop garbage flows that have no packets (cicflowmeter sometimes emits these).
    if out["total_fwd_packets"] == 0 and out["total_bwd_packets"] == 0:
        return None
    return out


def read_lab_captures(captures_dir: Path, per_class_cap: int) -> list[dict[str, Any]]:
    """Reads each per-category CSV and (deterministically) caps per-class so a
    category with 33k rows doesn't drown out one with 50.
    """
    rng = random.Random(123)
    rows: list[dict[str, Any]] = []
    for csv_path in sorted(captures_dir.glob("*.csv")):
        label = csv_path.stem
        class_rows: list[dict[str, Any]] = []
        with csv_path.open(newline="") as f:
            for raw in csv.DictReader(f):
                norm = normalize_row(raw, label)
                if norm is not None:
                    class_rows.append(norm)
        original = len(class_rows)
        if original > per_class_cap:
            rng.shuffle(class_rows)
            class_rows = class_rows[:per_class_cap]
        rows.extend(class_rows)
        print(f"  + {label}: {len(class_rows)} / {original} flows from {csv_path.name}")
    return rows


def read_synthetic(path: Path, per_class_cap: int) -> list[dict[str, Any]]:
    """Read synthetic_flows.csv and down-sample to roughly per_class_cap per class.

    Synthetic dataset is already in the canonical schema, so no normalization."""
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with path.open(newline="") as f:
        for raw in csv.DictReader(f):
            label = raw.get("label", "BENIGN")
            row = {c: 0 for c in NUMERIC_FEATURES}
            row["protocol"] = raw.get("protocol", "TCP")
            row["label"] = label
            for c in META_FEATURES:
                row[c] = raw.get(c, "")
            for c in NUMERIC_FEATURES:
                if c in raw and raw[c] != "":
                    try:
                        row[c] = float(raw[c])
                    except ValueError:
                        row[c] = 0.0
            by_class[label].append(row)

    rng = random.Random(42)
    sampled: list[dict[str, Any]] = []
    for label, rows in by_class.items():
        rng.shuffle(rows)
        sampled.extend(rows[:per_class_cap])
        print(f"  - synthetic {label}: {min(len(rows), per_class_cap)} / {len(rows)} kept")
    return sampled


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--captures-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--synthetic", type=Path, default=None)
    p.add_argument(
        "--synthetic-cap",
        type=int,
        default=500,
        help="Max synthetic rows per class to mix in (default: 500).",
    )
    p.add_argument(
        "--lab-cap",
        type=int,
        default=2000,
        help="Max lab rows per class to keep (default: 2000). Prevents a "
             "high-volume category like DoS from drowning out the rest.",
    )
    args = p.parse_args()

    print(f"[merge] reading lab captures from {args.captures_dir} (cap {args.lab_cap}/class)")
    lab_rows = read_lab_captures(args.captures_dir, args.lab_cap)
    if not lab_rows:
        print("ERROR: no lab rows found. Run lab/retrain/retrain.sh first.")
        return 1
    print(f"[merge] lab rows: {len(lab_rows)}")
    print(f"[merge]   distribution: {dict(Counter(r['label'] for r in lab_rows))}")

    all_rows = list(lab_rows)
    if args.synthetic and args.synthetic.exists():
        print(f"[merge] reading {args.synthetic} (cap {args.synthetic_cap}/class)")
        synth_rows = read_synthetic(args.synthetic, args.synthetic_cap)
        all_rows.extend(synth_rows)

    print(f"[merge] total rows: {len(all_rows)}")
    print(f"[merge]   distribution: {dict(Counter(r['label'] for r in all_rows))}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=OUT_COLUMNS)
        w.writeheader()
        for row in all_rows:
            w.writerow({k: row.get(k, "") for k in OUT_COLUMNS})
    print(f"[merge] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
