"""Canonical feature schema for flow-level network records.

The names are aligned with the CICIDS2017 / CICFlowMeter feature set so that
real captures can be plugged in without changes to downstream code.  Only a
representative 20-feature subset is wired through the pipeline by default —
empirical SRQ1 analysis showed these carry most of the discriminative power
(see docs/research/DOT_Research.md §SRQ1).
"""
from __future__ import annotations

LABEL_COLUMN: str = "label"

NUMERIC_FEATURES: list[str] = [
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

CATEGORICAL_FEATURES: list[str] = [
    "protocol",
]

FLOW_FEATURE_COLUMNS: list[str] = NUMERIC_FEATURES + CATEGORICAL_FEATURES
