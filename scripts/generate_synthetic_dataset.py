"""Generate a synthetic CICIDS-compatible flow dataset for offline development.

The real CICIDS2017 dataset (~6 GB) is referenced in the PRP. To make the project
fully self-contained while waiting for the dataset to be downloaded, this script
emits a synthetic dataset whose feature distributions are calibrated against the
public CICIDS2017 statistics reported in Sharafaldin et al. (2018). It is
*deliberately* easier than the real dataset — the goal is to exercise the
end-to-end pipeline, not to validate research claims.

Usage:
    python -m scripts.generate_synthetic_dataset --rows 20000 --out data/raw/synthetic_flows.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ATTACK_CATEGORIES = [
    "BENIGN",
    "DDoS",
    "DoS",
    "PortScan",
    "BruteForce",
    "WebAttack",
    "Botnet",
    "Infiltration",
]

# Distribution shares loosely calibrated to CICIDS2017 prevalences
PRIOR = {
    "BENIGN": 0.70,
    "DDoS": 0.07,
    "DoS": 0.07,
    "PortScan": 0.06,
    "BruteForce": 0.04,
    "WebAttack": 0.03,
    "Botnet": 0.02,
    "Infiltration": 0.01,
}


def _benign(rng: np.random.Generator, n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "flow_duration": rng.lognormal(mean=11.0, sigma=1.4, size=n),
        "total_fwd_packets": rng.poisson(lam=8, size=n) + 1,
        "total_bwd_packets": rng.poisson(lam=7, size=n) + 1,
        "total_length_fwd_packets": rng.lognormal(7, 1.0, n),
        "total_length_bwd_packets": rng.lognormal(7, 1.0, n),
        "fwd_packet_length_max": rng.normal(800, 250, n).clip(40, 1500),
        "fwd_packet_length_mean": rng.normal(450, 150, n).clip(40, 1500),
        "bwd_packet_length_max": rng.normal(900, 250, n).clip(40, 1500),
        "bwd_packet_length_mean": rng.normal(500, 150, n).clip(40, 1500),
        "flow_bytes_per_s": rng.lognormal(8, 1.0, n),
        "flow_packets_per_s": rng.lognormal(2.0, 0.7, n),
        "flow_iat_mean": rng.lognormal(6.0, 1.0, n),
        "flow_iat_std": rng.lognormal(5.5, 1.0, n),
        "fwd_iat_total": rng.lognormal(10, 1.2, n),
        "bwd_iat_total": rng.lognormal(10, 1.2, n),
        "fin_flag_count": rng.binomial(2, 0.6, n),
        "syn_flag_count": rng.binomial(2, 0.6, n),
        "rst_flag_count": rng.binomial(1, 0.05, n),
        "psh_flag_count": rng.binomial(4, 0.4, n),
        "ack_flag_count": rng.binomial(8, 0.7, n),
        "protocol": rng.choice(["TCP", "UDP"], size=n, p=[0.78, 0.22]),
    })


def _portscan(rng: np.random.Generator, n: int) -> pd.DataFrame:
    df = pd.DataFrame({
        "flow_duration": rng.lognormal(4.0, 0.6, n),  # very short
        "total_fwd_packets": rng.poisson(1.5, n) + 1,
        "total_bwd_packets": rng.poisson(0.3, n),
        "total_length_fwd_packets": rng.normal(60, 10, n).clip(40, 100),
        "total_length_bwd_packets": rng.normal(40, 15, n).clip(0, 80),
        "fwd_packet_length_max": rng.normal(60, 8, n).clip(40, 80),
        "fwd_packet_length_mean": rng.normal(60, 8, n).clip(40, 80),
        "bwd_packet_length_max": rng.normal(40, 8, n).clip(0, 60),
        "bwd_packet_length_mean": rng.normal(40, 8, n).clip(0, 60),
        "flow_bytes_per_s": rng.lognormal(4.0, 1.0, n),
        "flow_packets_per_s": rng.lognormal(5.5, 0.7, n),  # high packet rate
        "flow_iat_mean": rng.lognormal(1.0, 0.5, n),
        "flow_iat_std": rng.lognormal(0.5, 0.5, n),
        "fwd_iat_total": rng.lognormal(2.0, 0.5, n),
        "bwd_iat_total": rng.lognormal(1.0, 0.5, n),
        "fin_flag_count": rng.binomial(1, 0.05, n),
        "syn_flag_count": rng.binomial(2, 0.95, n),  # SYN-heavy
        "rst_flag_count": rng.binomial(2, 0.7, n),
        "psh_flag_count": rng.binomial(1, 0.05, n),
        "ack_flag_count": rng.binomial(1, 0.05, n),
        "protocol": rng.choice(["TCP", "UDP"], size=n, p=[0.95, 0.05]),
    })
    return df


def _ddos(rng: np.random.Generator, n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "flow_duration": rng.lognormal(3.5, 0.6, n),
        "total_fwd_packets": rng.poisson(60, n) + 30,
        "total_bwd_packets": rng.poisson(2, n),
        "total_length_fwd_packets": rng.lognormal(10, 0.5, n),
        "total_length_bwd_packets": rng.lognormal(4, 1.0, n),
        "fwd_packet_length_max": rng.normal(120, 20, n).clip(40, 1500),
        "fwd_packet_length_mean": rng.normal(110, 20, n).clip(40, 1500),
        "bwd_packet_length_max": rng.normal(80, 30, n).clip(0, 200),
        "bwd_packet_length_mean": rng.normal(60, 20, n).clip(0, 200),
        "flow_bytes_per_s": rng.lognormal(12.0, 0.7, n),  # very high
        "flow_packets_per_s": rng.lognormal(7.5, 0.8, n),
        "flow_iat_mean": rng.lognormal(-1.0, 0.5, n),
        "flow_iat_std": rng.lognormal(-1.5, 0.5, n),
        "fwd_iat_total": rng.lognormal(2.0, 0.5, n),
        "bwd_iat_total": rng.lognormal(1.0, 0.5, n),
        "fin_flag_count": rng.binomial(1, 0.05, n),
        "syn_flag_count": rng.binomial(3, 0.9, n),
        "rst_flag_count": rng.binomial(2, 0.3, n),
        "psh_flag_count": rng.binomial(1, 0.05, n),
        "ack_flag_count": rng.binomial(4, 0.5, n),
        "protocol": np.array(["TCP"] * n),
    })


def _dos(rng: np.random.Generator, n: int) -> pd.DataFrame:
    df = _ddos(rng, n)
    df["flow_packets_per_s"] *= 0.4
    df["flow_bytes_per_s"] *= 0.4
    df["flow_duration"] = rng.lognormal(6.0, 0.6, n)
    return df


def _brute_force(rng: np.random.Generator, n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "flow_duration": rng.lognormal(8.0, 0.7, n),
        "total_fwd_packets": rng.poisson(15, n) + 5,
        "total_bwd_packets": rng.poisson(12, n) + 4,
        "total_length_fwd_packets": rng.normal(800, 150, n).clip(100, 2000),
        "total_length_bwd_packets": rng.normal(600, 150, n).clip(100, 2000),
        "fwd_packet_length_max": rng.normal(300, 60, n).clip(40, 600),
        "fwd_packet_length_mean": rng.normal(120, 40, n).clip(40, 400),
        "bwd_packet_length_max": rng.normal(240, 60, n).clip(40, 400),
        "bwd_packet_length_mean": rng.normal(100, 30, n).clip(40, 300),
        "flow_bytes_per_s": rng.lognormal(7.5, 0.6, n),
        "flow_packets_per_s": rng.lognormal(3.5, 0.5, n),
        "flow_iat_mean": rng.lognormal(5.0, 0.5, n),
        "flow_iat_std": rng.lognormal(4.5, 0.5, n),
        "fwd_iat_total": rng.lognormal(7.0, 0.6, n),
        "bwd_iat_total": rng.lognormal(7.0, 0.6, n),
        "fin_flag_count": rng.binomial(2, 0.6, n),
        "syn_flag_count": rng.binomial(2, 0.8, n),
        "rst_flag_count": rng.binomial(2, 0.4, n),  # failed auth -> RST
        "psh_flag_count": rng.binomial(5, 0.7, n),
        "ack_flag_count": rng.binomial(10, 0.8, n),
        "protocol": np.array(["TCP"] * n),
    })


def _web_attack(rng: np.random.Generator, n: int) -> pd.DataFrame:
    df = _benign(rng, n)
    df["total_length_fwd_packets"] *= 1.8  # long URLs / payloads
    df["fwd_packet_length_max"] = rng.normal(1200, 250, n).clip(40, 1500)
    df["psh_flag_count"] = rng.binomial(6, 0.8, n)
    df["flow_duration"] = rng.lognormal(7.5, 0.7, n)
    df["protocol"] = np.array(["TCP"] * n)
    return df


def _botnet(rng: np.random.Generator, n: int) -> pd.DataFrame:
    return pd.DataFrame({
        "flow_duration": rng.lognormal(12.0, 0.6, n),  # long-lived C2
        "total_fwd_packets": rng.poisson(4, n) + 1,
        "total_bwd_packets": rng.poisson(4, n) + 1,
        "total_length_fwd_packets": rng.normal(200, 80, n).clip(40, 600),
        "total_length_bwd_packets": rng.normal(200, 80, n).clip(40, 600),
        "fwd_packet_length_max": rng.normal(150, 40, n).clip(40, 300),
        "fwd_packet_length_mean": rng.normal(120, 30, n).clip(40, 250),
        "bwd_packet_length_max": rng.normal(150, 40, n).clip(40, 300),
        "bwd_packet_length_mean": rng.normal(120, 30, n).clip(40, 250),
        "flow_bytes_per_s": rng.lognormal(4.0, 0.6, n),  # low
        "flow_packets_per_s": rng.lognormal(0.5, 0.4, n),
        "flow_iat_mean": rng.lognormal(8.0, 0.5, n),  # periodic beacons
        "flow_iat_std": rng.lognormal(1.0, 0.3, n),  # *low* IAT variance = beaconing
        "fwd_iat_total": rng.lognormal(11.0, 0.6, n),
        "bwd_iat_total": rng.lognormal(11.0, 0.6, n),
        "fin_flag_count": rng.binomial(1, 0.3, n),
        "syn_flag_count": rng.binomial(1, 0.5, n),
        "rst_flag_count": rng.binomial(1, 0.05, n),
        "psh_flag_count": rng.binomial(2, 0.5, n),
        "ack_flag_count": rng.binomial(5, 0.7, n),
        "protocol": rng.choice(["TCP", "UDP"], size=n, p=[0.6, 0.4]),
    })


def _infiltration(rng: np.random.Generator, n: int) -> pd.DataFrame:
    df = _benign(rng, n)
    df["total_length_fwd_packets"] *= 6  # data exfil
    df["flow_duration"] = rng.lognormal(11.0, 0.7, n)
    df["flow_bytes_per_s"] = rng.lognormal(9.5, 0.6, n)
    df["protocol"] = np.array(["TCP"] * n)
    return df


GENERATORS = {
    "BENIGN": _benign,
    "DDoS": _ddos,
    "DoS": _dos,
    "PortScan": _portscan,
    "BruteForce": _brute_force,
    "WebAttack": _web_attack,
    "Botnet": _botnet,
    "Infiltration": _infiltration,
}


def _random_ip(rng: np.random.Generator) -> str:
    return ".".join(str(int(x)) for x in rng.integers(1, 254, size=4))


def generate(rows: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    parts: list[pd.DataFrame] = []
    for label, share in PRIOR.items():
        n = max(50, int(rows * share))
        df = GENERATORS[label](rng, n)
        df["label"] = label
        df["src_ip"] = [_random_ip(rng) for _ in range(n)]
        df["dst_ip"] = [_random_ip(rng) for _ in range(n)]
        df["src_port"] = rng.integers(1024, 65535, size=n)
        df["dst_port"] = rng.choice([22, 23, 53, 80, 443, 3389, 8080], size=n)
        parts.append(df)
    out = pd.concat(parts, ignore_index=True).sample(frac=1.0, random_state=seed).reset_index(drop=True)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=20000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="data/raw/synthetic_flows.csv")
    args = parser.parse_args()

    df = generate(args.rows, seed=args.seed)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")
    print(df["label"].value_counts())


if __name__ == "__main__":
    main()
