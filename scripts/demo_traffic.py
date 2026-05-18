"""Replay a slice of the synthetic dataset against the running API.

Useful for the demo and the screenshot evidence — populates the dashboard
with a mix of benign and attack flows so the analyst view is non-empty.
"""
from __future__ import annotations

import argparse
import time

import pandas as pd
import requests

CANONICAL_FIELDS = [
    "protocol", "flow_duration", "total_fwd_packets", "total_bwd_packets",
    "total_length_fwd_packets", "total_length_bwd_packets",
    "fwd_packet_length_max", "fwd_packet_length_mean",
    "bwd_packet_length_max", "bwd_packet_length_mean",
    "flow_bytes_per_s", "flow_packets_per_s",
    "flow_iat_mean", "flow_iat_std", "fwd_iat_total", "bwd_iat_total",
    "fin_flag_count", "syn_flag_count", "rst_flag_count",
    "psh_flag_count", "ack_flag_count",
    "src_ip", "dst_ip", "src_port", "dst_port",
]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/raw/synthetic_flows.csv")
    p.add_argument("--url", default="http://localhost:8000")
    p.add_argument("--batch", type=int, default=25)
    p.add_argument("--n-batches", type=int, default=20)
    p.add_argument("--sleep", type=float, default=0.4)
    p.add_argument("--threshold", type=float, default=0.5)
    args = p.parse_args()

    df = pd.read_csv(args.data)
    rng = pd.Series(range(len(df))).sample(frac=1, random_state=7).tolist()

    total_predictions = 0
    total_alerts = 0
    for b in range(args.n_batches):
        sample_idx = rng[b * args.batch:(b + 1) * args.batch]
        sample = df.iloc[sample_idx]
        flows = []
        for _, row in sample.iterrows():
            d = {k: row.get(k) for k in CANONICAL_FIELDS if k in row}
            d["protocol"] = str(d.get("protocol") or "TCP")
            flows.append(d)
        resp = requests.post(f"{args.url}/predict", json={"flows": flows, "threshold": args.threshold}, timeout=30)
        resp.raise_for_status()
        out = resp.json()
        verdicts = out["verdicts"]
        total_predictions += len(verdicts)
        total_alerts += sum(1 for v in verdicts if v["is_attack"])
        sev = {}
        for v in verdicts:
            sev[v["severity"]] = sev.get(v["severity"], 0) + 1
        print(f"[batch {b+1:>2}/{args.n_batches}] {len(verdicts):>3} flows  alerts={sum(1 for v in verdicts if v['is_attack']):>2}  severity={sev}")
        time.sleep(args.sleep)

    print(f"\nDone — {total_predictions} flows, {total_alerts} alerts, fp rate proxy = {1 - total_alerts/total_predictions:.2%} benign-classified")


if __name__ == "__main__":
    main()
