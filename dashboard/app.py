"""Streamlit dashboard for the Network Traffic Anomaly Detector.

This is the D5 deliverable from the PRP (SRQ5 — analyst-friendly presentation).
The dashboard talks to the FastAPI backend, so it can be deployed independently
and run against any model rebuilt and reloaded via `POST /admin/reload`.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

API_URL = os.environ.get("AD_API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Network Anomaly Detector",
    page_icon="🛰️",
    layout="wide",
)

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
SEVERITY_COLOR = {
    "critical": "#ef4444",
    "high": "#f97316",
    "medium": "#eab308",
    "low": "#3b82f6",
    "info": "#10b981",
}

# ----------------------------------------------------------------------------
# Pre-built request examples — one per category. Numeric values are aligned
# with the per-class distributions in scripts/generate_synthetic_dataset.py
# so each example sits comfortably inside the region of feature space the
# model was trained to recognise as that class.
# ----------------------------------------------------------------------------
CATEGORY_COLOR = {
    "BENIGN":       "#10b981",
    "DDoS":         "#ef4444",
    "DoS":          "#f97316",
    "PortScan":     "#06b6d4",
    "BruteForce":   "#f59e0b",
    "WebAttack":    "#eab308",
    "Botnet":       "#a855f7",
    "Infiltration": "#ec4899",
}

EXAMPLES: dict[str, dict] = {
    "BENIGN": {
        "tag": "baseline · ~70% of real traffic",
        "why_short": "balanced rates, normal packet sizes, healthy TCP handshake.",
        "why_full": (
            "Normal interactive traffic — a moderate stream of mid-sized packets in both directions, "
            "an ACK-heavy mix of TCP flags, and no resets. Everything else is measured against this "
            "profile; if no feature is anomalous, the trees route the flow into the benign leaf."
        ),
        "signals": [
            ("flow_packets_per_s", "7", "mid-range, consistent with browsing or API calls"),
            ("total_fwd_packets / total_bwd_packets", "10 / 8", "balanced — client and server take turns"),
            ("fwd_packet_length_mean", "~450 B", "typical request size, not a flood, not an exfil"),
            ("ack_flag_count", "5", "healthy three-way handshake plus replies"),
            ("rst_flag_count", "0", "no failed connections or scanner aborts"),
        ],
        "dst_port_default": 443,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 60000.0,
            "total_fwd_packets": 10.0,
            "total_bwd_packets": 8.0,
            "flow_packets_per_s": 7.0,
            "flow_bytes_per_s": 3000.0,
            "fwd_packet_length_max": 800.0,
            "fwd_packet_length_mean": 450.0,
            "bwd_packet_length_max": 900.0,
            "bwd_packet_length_mean": 500.0,
            "flow_iat_mean": 400.0,
            "flow_iat_std": 250.0,
            "fin_flag_count": 1.0,
            "syn_flag_count": 1.0,
            "rst_flag_count": 0.0,
            "psh_flag_count": 2.0,
            "ack_flag_count": 5.0,
            "src_ip": "10.0.0.5",
            "dst_ip": "10.0.0.100",
        },
    },
    "DDoS": {
        "tag": "volumetric flood",
        "why_short": "huge forward-packet rate, tiny payload, almost no replies — a SYN flood.",
        "why_full": (
            "Many sources hammer one victim with crafted packets. The forward direction is saturated "
            "(thousands of packets per second of small ~120-byte payloads) while the victim cannot keep "
            "up, so backward traffic collapses. SYN counts climb because the handshake never completes."
        ),
        "signals": [
            ("flow_packets_per_s", "1800", "two orders of magnitude above benign"),
            ("flow_bytes_per_s", "160 000", "very high byte-rate from many tiny packets"),
            ("total_fwd_packets", "90", "while bwd is only 2 — extreme asymmetry"),
            ("fwd_packet_length_mean", "~110 B", "small, crafted — not real payloads"),
            ("syn_flag_count", "3", "SYN-heavy because connections never close"),
            ("flow_duration", "33 μs", "flow torn down almost instantly"),
        ],
        "dst_port_default": 80,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 33.0,
            "total_fwd_packets": 90.0,
            "total_bwd_packets": 2.0,
            "flow_packets_per_s": 1800.0,
            "flow_bytes_per_s": 160000.0,
            "fwd_packet_length_max": 130.0,
            "fwd_packet_length_mean": 110.0,
            "bwd_packet_length_max": 90.0,
            "bwd_packet_length_mean": 60.0,
            "flow_iat_mean": 0.4,
            "flow_iat_std": 0.2,
            "fin_flag_count": 0.0,
            "syn_flag_count": 3.0,
            "rst_flag_count": 1.0,
            "psh_flag_count": 0.0,
            "ack_flag_count": 4.0,
            "src_ip": "203.0.113.42",
            "dst_ip": "10.0.0.100",
        },
    },
    "DoS": {
        "tag": "single-source slow flood",
        "why_short": "DDoS-like asymmetry but lower rate and a much longer-lived flow.",
        "why_full": (
            "Same intent as a DDoS but driven from one origin (slowloris, RUDY, HTTP-flood). "
            "The packet- and byte-rate are noticeably lower than DDoS, the flow lingers for "
            "hundreds of milliseconds, but the SYN-heavy asymmetry between forward and backward "
            "directions still gives it away."
        ),
        "signals": [
            ("flow_duration", "400 μs", "the attacker holds the connection open"),
            ("flow_packets_per_s", "720", "high, but ~½ of a DDoS"),
            ("flow_bytes_per_s", "64 000", "matches the slower cadence"),
            ("total_fwd / total_bwd", "90 / 2", "still extreme asymmetry"),
            ("syn_flag_count", "2", "incomplete handshakes"),
        ],
        "dst_port_default": 80,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 400.0,
            "total_fwd_packets": 90.0,
            "total_bwd_packets": 2.0,
            "flow_packets_per_s": 720.0,
            "flow_bytes_per_s": 64000.0,
            "fwd_packet_length_max": 130.0,
            "fwd_packet_length_mean": 110.0,
            "bwd_packet_length_max": 90.0,
            "bwd_packet_length_mean": 60.0,
            "flow_iat_mean": 1.0,
            "flow_iat_std": 0.3,
            "fin_flag_count": 0.0,
            "syn_flag_count": 2.0,
            "rst_flag_count": 1.0,
            "psh_flag_count": 0.0,
            "ack_flag_count": 4.0,
            "src_ip": "198.51.100.7",
            "dst_ip": "10.0.0.100",
        },
    },
    "PortScan": {
        "tag": "reconnaissance",
        "why_short": "ultra-short flow, one-or-two tiny packets, SYN + RST, no payload.",
        "why_full": (
            "An attacker tickles a port to see whether it's open. The flow lives for microseconds, "
            "carries a single 60-byte SYN packet, often gets an immediate RST back from a closed port, "
            "and the packets-per-second rate is unreasonably high relative to the total byte count."
        ),
        "signals": [
            ("flow_duration", "55 μs", "barely a handshake"),
            ("total_fwd_packets", "2", "and total_bwd is 0–1"),
            ("fwd_packet_length_mean", "60 B", "SYN only — no payload"),
            ("syn_flag_count", "2", "and rst_flag_count is also high"),
            ("flow_packets_per_s", "245", "rate inflated by tiny packets"),
        ],
        "dst_port_default": 3389,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 55.0,
            "total_fwd_packets": 2.0,
            "total_bwd_packets": 0.0,
            "flow_packets_per_s": 245.0,
            "flow_bytes_per_s": 1100.0,
            "fwd_packet_length_max": 60.0,
            "fwd_packet_length_mean": 60.0,
            "bwd_packet_length_max": 0.0,
            "bwd_packet_length_mean": 0.0,
            "flow_iat_mean": 2.7,
            "flow_iat_std": 1.6,
            "fin_flag_count": 0.0,
            "syn_flag_count": 2.0,
            "rst_flag_count": 1.0,
            "psh_flag_count": 0.0,
            "ack_flag_count": 0.0,
            "src_ip": "192.0.2.55",
            "dst_ip": "10.0.0.100",
        },
    },
    "BruteForce": {
        "tag": "credential abuse",
        "why_short": "many short request/response cycles with abnormal RST + PSH flag counts.",
        "why_full": (
            "Repeated login attempts against SSH, RDP, or a web form. The flow is long enough to fit "
            "dozens of failed authentication cycles; each failure shows up as a RST, and the per-cycle "
            "PSH/ACK pattern is heavier than a normal session of the same length."
        ),
        "signals": [
            ("flow_duration", "2980 μs", "long enough to chain failed attempts"),
            ("rst_flag_count", "1+", "repeated failed authentications"),
            ("psh_flag_count", "3", "each attempt pushes a new credential"),
            ("ack_flag_count", "8", "many short turn-arounds"),
            ("dst_port", "22 (SSH)", "or 3389 RDP / 80 web — high-value targets"),
        ],
        "dst_port_default": 22,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 2980.0,
            "total_fwd_packets": 20.0,
            "total_bwd_packets": 16.0,
            "flow_packets_per_s": 33.0,
            "flow_bytes_per_s": 1800.0,
            "fwd_packet_length_max": 300.0,
            "fwd_packet_length_mean": 120.0,
            "bwd_packet_length_max": 240.0,
            "bwd_packet_length_mean": 100.0,
            "flow_iat_mean": 150.0,
            "flow_iat_std": 90.0,
            "fin_flag_count": 1.0,
            "syn_flag_count": 2.0,
            "rst_flag_count": 1.0,
            "psh_flag_count": 3.0,
            "ack_flag_count": 8.0,
            "src_ip": "198.51.100.99",
            "dst_ip": "10.0.0.50",
        },
    },
    "WebAttack": {
        "tag": "L7 injection",
        "why_short": "looks like benign HTTP except the forward payload is huge and PSH-heavy.",
        "why_full": (
            "SQLi, XSS, command-injection. Packet counts and TCP flags look ordinary, but the "
            "forward direction carries unusually long URLs or encoded payloads — fwd_packet_length_max "
            "sits at the MTU ceiling and PSH counts climb because the attacker is shoving data."
        ),
        "signals": [
            ("fwd_packet_length_max", "1200 B", "near MTU — packed URL or body"),
            ("total_length_fwd_packets", "↑↑", "auto-computed = high"),
            ("psh_flag_count", "5", "pushes the malicious payload"),
            ("dst_port", "80 / 443", "the web tier"),
            ("flow_duration", "1800 μs", "long-ish single HTTP request"),
        ],
        "dst_port_default": 443,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 1800.0,
            "total_fwd_packets": 10.0,
            "total_bwd_packets": 8.0,
            "flow_packets_per_s": 7.0,
            "flow_bytes_per_s": 12000.0,
            "fwd_packet_length_max": 1200.0,
            "fwd_packet_length_mean": 800.0,
            "bwd_packet_length_max": 900.0,
            "bwd_packet_length_mean": 500.0,
            "flow_iat_mean": 400.0,
            "flow_iat_std": 250.0,
            "fin_flag_count": 1.0,
            "syn_flag_count": 1.0,
            "rst_flag_count": 0.0,
            "psh_flag_count": 5.0,
            "ack_flag_count": 5.0,
            "src_ip": "203.0.113.7",
            "dst_ip": "10.0.0.80",
        },
    },
    "Botnet": {
        "tag": "C2 beaconing",
        "why_short": "very long-lived, low-rate flow with suspiciously regular timing.",
        "why_full": (
            "A compromised host phones home on a schedule. The flow lives for tens of milliseconds, "
            "the byte-rate is tiny, but the giveaway is timing: flow_iat_std is far *below* what real "
            "human traffic produces. Beacons are too regular to be a person at a keyboard."
        ),
        "signals": [
            ("flow_duration", "162 000 μs (162 ms)", "long-lived sessions"),
            ("flow_iat_std", "2.7", "LOW — beacons fire on a timer"),
            ("flow_iat_mean", "2980 μs", "the beacon period itself"),
            ("flow_bytes_per_s", "55", "almost nothing — tiny heartbeats"),
            ("total_fwd / total_bwd", "5 / 5", "symmetric request/reply"),
        ],
        "dst_port_default": 8080,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 162000.0,
            "total_fwd_packets": 5.0,
            "total_bwd_packets": 5.0,
            "flow_packets_per_s": 1.6,
            "flow_bytes_per_s": 55.0,
            "fwd_packet_length_max": 150.0,
            "fwd_packet_length_mean": 120.0,
            "bwd_packet_length_max": 150.0,
            "bwd_packet_length_mean": 120.0,
            "flow_iat_mean": 2980.0,
            "flow_iat_std": 2.7,
            "fin_flag_count": 0.0,
            "syn_flag_count": 1.0,
            "rst_flag_count": 0.0,
            "psh_flag_count": 1.0,
            "ack_flag_count": 3.0,
            "src_ip": "10.0.0.42",
            "dst_ip": "185.220.101.7",
        },
    },
    "Infiltration": {
        "tag": "exfiltration",
        "why_short": "looks benign per-packet but moves an unusual amount of data outward.",
        "why_full": (
            "An internal host quietly uploads sensitive data over an established session. Each packet "
            "looks normal in isolation, but the *aggregate* outbound payload is far above what a user "
            "of that role would generate. The model latches on to total_length_fwd_packets and "
            "flow_bytes_per_s, which both sit well above the benign baseline."
        ),
        "signals": [
            ("total_length_fwd_packets", "↑↑↑ (auto from mean × count)", "the giveaway"),
            ("flow_bytes_per_s", "13 360", "high — sustained upload"),
            ("flow_duration", "60 000 μs", "long-lived transfer"),
            ("fwd_packet_length_mean", "~1400 B", "near-MTU packets full of data"),
            ("rst / fin counts", "near 0", "session held open the whole time"),
        ],
        "dst_port_default": 443,
        "flow": {
            "protocol": "TCP",
            "flow_duration": 60000.0,
            "total_fwd_packets": 15.0,
            "total_bwd_packets": 8.0,
            "flow_packets_per_s": 7.0,
            "flow_bytes_per_s": 13360.0,
            "fwd_packet_length_max": 1500.0,
            "fwd_packet_length_mean": 1400.0,
            "bwd_packet_length_max": 200.0,
            "bwd_packet_length_mean": 80.0,
            "flow_iat_mean": 400.0,
            "flow_iat_std": 250.0,
            "fin_flag_count": 0.0,
            "syn_flag_count": 1.0,
            "rst_flag_count": 0.0,
            "psh_flag_count": 4.0,
            "ack_flag_count": 7.0,
            "src_ip": "10.0.0.99",
            "dst_ip": "185.220.101.42",
        },
    },
}

# Map FlowRecord field → Streamlit widget key used in the Manual scoring form.
_FIELD_TO_KEY = {
    "protocol":               "ex_protocol",
    "flow_duration":          "ex_flow_duration",
    "total_fwd_packets":      "ex_total_fwd_packets",
    "total_bwd_packets":      "ex_total_bwd_packets",
    "flow_packets_per_s":     "ex_flow_packets_per_s",
    "flow_bytes_per_s":       "ex_flow_bytes_per_s",
    "fwd_packet_length_max":  "ex_fwd_pkt_len_max",
    "fwd_packet_length_mean": "ex_fwd_pkt_len_mean",
    "bwd_packet_length_max":  "ex_bwd_pkt_len_max",
    "bwd_packet_length_mean": "ex_bwd_pkt_len_mean",
    "flow_iat_mean":          "ex_flow_iat_mean",
    "flow_iat_std":           "ex_flow_iat_std",
    "syn_flag_count":         "ex_syn",
    "ack_flag_count":         "ex_ack",
    "psh_flag_count":         "ex_psh",
    "rst_flag_count":         "ex_rst",
    "fin_flag_count":         "ex_fin",
    "src_ip":                 "ex_src_ip",
    "dst_ip":                 "ex_dst_ip",
}

# Defaults match the original Manual scoring form so the experience is
# identical when no preset has been loaded.
_DEFAULTS = {
    "ex_protocol":            "TCP",
    "ex_flow_duration":       120_000.0,
    "ex_total_fwd_packets":   10.0,
    "ex_total_bwd_packets":   8.0,
    "ex_flow_packets_per_s":  50.0,
    "ex_flow_bytes_per_s":    20_000.0,
    "ex_fwd_pkt_len_max":     800.0,
    "ex_fwd_pkt_len_mean":    450.0,
    "ex_bwd_pkt_len_max":     900.0,
    "ex_bwd_pkt_len_mean":    500.0,
    "ex_flow_iat_mean":       500.0,
    "ex_flow_iat_std":        200.0,
    "ex_syn":                 1.0,
    "ex_ack":                 5.0,
    "ex_psh":                 1.0,
    "ex_rst":                 0.0,
    "ex_fin":                 1.0,
    "ex_src_ip":              "10.0.0.5",
    "ex_dst_ip":              "10.0.0.100",
}


def _seed_form_defaults() -> None:
    """Populate session_state with the original Manual-scoring defaults
    if no value has been set yet for that widget."""
    for k, v in _DEFAULTS.items():
        st.session_state.setdefault(k, v)


def apply_example_to_form(name: str) -> None:
    """Copy an EXAMPLES[name] flow into the Manual scoring form widgets."""
    example = EXAMPLES[name]["flow"]
    for field, value in example.items():
        key = _FIELD_TO_KEY.get(field)
        if key:
            st.session_state[key] = value
    st.session_state["loaded_example"] = name


def _api_get(path: str, **params):
    try:
        r = requests.get(f"{API_URL}{path}", params=params, timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        st.error(f"API call to {path} failed: {exc}")
        return None


def _badge(label: str, color: str) -> str:
    return (
        f'<span style="background:{color};color:white;padding:2px 8px;'
        f'border-radius:12px;font-size:12px;font-weight:600">{label}</span>'
    )


def render_header() -> None:
    st.markdown(
        """
        <h1 style="margin-bottom:0">🛰️ Network Traffic Anomaly Detector</h1>
        <p style="color:#64748b;margin-top:4px">
          Real-time ML-based detection of malicious network flows ·
          PRP by Angel Rusev · Fontys Cybersecurity (Attack &amp; Defend) 2026
        </p>
        """,
        unsafe_allow_html=True,
    )


def render_health(health: dict | None) -> None:
    cols = st.columns(4)
    status = (health or {}).get("status", "down")
    model_loaded = (health or {}).get("model_loaded", False)
    model_name = (health or {}).get("model_name") or "—"
    version = (health or {}).get("version") or "?"
    badge_color = {"ok": "#10b981", "degraded": "#eab308", "down": "#ef4444"}.get(status, "#ef4444")
    with cols[0]:
        st.markdown(f"**API status**<br/>{_badge(status.upper(), badge_color)}", unsafe_allow_html=True)
    with cols[1]:
        st.markdown(
            f"**Model loaded**<br/>{_badge('YES' if model_loaded else 'NO', '#10b981' if model_loaded else '#ef4444')}",
            unsafe_allow_html=True,
        )
    with cols[2]:
        st.markdown(f"**Active model**<br/>`{model_name}`", unsafe_allow_html=True)
    with cols[3]:
        st.markdown(f"**Version**<br/>`{version}`", unsafe_allow_html=True)


def render_metrics(metrics: dict | None) -> None:
    if not metrics:
        st.info("Metrics not available yet — make some predictions first.")
        return
    cols = st.columns(4)
    cols[0].metric("Total flows scored", f"{metrics['total_predictions']:,}")
    cols[1].metric("Alerts raised", f"{metrics['total_alerts']:,}",
                   delta=f"{metrics['total_alerts'] / max(1, metrics['total_predictions']):.1%} of all flows")
    cols[2].metric("Benign flows", f"{metrics['total_benign']:,}")
    cols[3].metric("Avg latency", f"{metrics['avg_latency_ms']:.2f} ms")

    c1, c2 = st.columns(2)
    sev = metrics.get("severity_breakdown") or {}
    if sev:
        sev_df = pd.DataFrame(
            [{"severity": k, "count": v} for k, v in sev.items() if k in SEVERITY_ORDER]
        )
        if not sev_df.empty:
            sev_df["severity"] = pd.Categorical(sev_df["severity"], categories=SEVERITY_ORDER, ordered=True)
            sev_df = sev_df.sort_values("severity")
            fig = px.bar(
                sev_df, x="severity", y="count", color="severity",
                color_discrete_map=SEVERITY_COLOR, title="Severity distribution"
            )
            fig.update_layout(showlegend=False, height=300, margin=dict(t=40, b=20))
            c1.plotly_chart(fig, use_container_width=True)

    cls = metrics.get("attacks_by_class") or {}
    if cls:
        cls_df = pd.DataFrame([{"class": k, "count": v} for k, v in cls.items()])
        cls_df = cls_df.sort_values("count", ascending=False)
        fig = px.pie(cls_df, names="class", values="count", title="Attacks by class", hole=0.55)
        fig.update_layout(height=300, margin=dict(t=40, b=20))
        c2.plotly_chart(fig, use_container_width=True)


def render_alerts(alerts: list[dict] | None) -> None:
    if not alerts:
        st.success("No alerts yet — system is monitoring.")
        return
    df = pd.DataFrame(alerts)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp", ascending=False)
    st.dataframe(
        df[["timestamp", "verdict", "severity", "attack_score", "src_ip", "dst_ip", "model_name"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "attack_score": st.column_config.ProgressColumn(
                "Attack score", min_value=0.0, max_value=1.0, format="%.2f"
            ),
            "severity": st.column_config.TextColumn("Severity"),
            "timestamp": st.column_config.DatetimeColumn("Time (UTC)"),
        },
    )


def _send_predict(flow: dict, threshold: float = 0.5) -> dict:
    """POST one flow to /predict and return the parsed JSON body. Raises on HTTP error."""
    r = requests.post(
        f"{API_URL}/predict",
        json={"flows": [flow], "threshold": threshold},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def _render_verdict(out: dict, header: str = "Verdict") -> None:
    """Render a prediction response (verdict badge + class-probability bars)."""
    v = out["verdicts"][0]
    color = SEVERITY_COLOR.get(v["severity"], "#3b82f6")
    st.markdown(
        f"### {header}: {_badge(v['verdict'], color)} · "
        f"score `{v['attack_score']:.3f}` · severity {_badge(v['severity'], color)}",
        unsafe_allow_html=True,
    )
    if v.get("class_probabilities"):
        probs = pd.DataFrame(
            [{"class": k, "probability": p} for k, p in v["class_probabilities"].items()]
        ).sort_values("probability", ascending=False)
        fig = px.bar(probs, x="class", y="probability", title="Class probabilities")
        fig.update_layout(height=300, margin=dict(t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Model: `{out['model_name']}` ({out['model_family']}) · threshold used: {out['threshold_used']}"
    )


def render_predict_form() -> None:
    st.subheader("Manual flow scoring")
    _seed_form_defaults()

    # --- Preset loader (outside the form so it can mutate session_state) ----
    pc1, pc2, pc3 = st.columns([3, 1, 2])
    with pc1:
        choice = st.selectbox(
            "Load a preset request for any category",
            ["— pick a category —"] + list(EXAMPLES.keys()),
            help="Pre-built request bodies calibrated so the trained model classifies each as the given category.",
            key="preset_picker",
        )
    with pc2:
        load_clicked = st.button("Load preset", use_container_width=True)
    with pc3:
        if st.button("Reset to defaults", use_container_width=True):
            for k, v in _DEFAULTS.items():
                st.session_state[k] = v
            st.session_state.pop("loaded_example", None)
            st.rerun()

    if load_clicked and choice in EXAMPLES:
        apply_example_to_form(choice)
        st.rerun()

    loaded = st.session_state.get("loaded_example")
    if loaded:
        color = CATEGORY_COLOR.get(loaded, "#3b82f6")
        st.markdown(
            f"Loaded preset: {_badge(loaded, color)} — "
            f"<span style='color:#64748b'>{EXAMPLES[loaded]['why_short']}</span>",
            unsafe_allow_html=True,
        )
        with st.expander("Why these params produce this verdict", expanded=False):
            st.write(EXAMPLES[loaded]["why_full"])

    # --- Manual scoring form ------------------------------------------------
    with st.form("score_one_flow"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.selectbox("Protocol", ["TCP", "UDP", "ICMP", "OTHER"], key="ex_protocol")
            st.number_input("Flow duration (μs)", step=10_000.0, key="ex_flow_duration")
            st.number_input("Total fwd packets", step=1.0, key="ex_total_fwd_packets")
            st.number_input("Total bwd packets", step=1.0, key="ex_total_bwd_packets")
            st.number_input("Packets / s", step=10.0, key="ex_flow_packets_per_s")
            st.number_input("Bytes / s", step=1000.0, key="ex_flow_bytes_per_s")
        with c2:
            st.number_input("Fwd pkt length max", key="ex_fwd_pkt_len_max")
            st.number_input("Fwd pkt length mean", key="ex_fwd_pkt_len_mean")
            st.number_input("Bwd pkt length max", key="ex_bwd_pkt_len_max")
            st.number_input("Bwd pkt length mean", key="ex_bwd_pkt_len_mean")
            st.number_input("Flow IAT mean", key="ex_flow_iat_mean")
            st.number_input("Flow IAT std", key="ex_flow_iat_std")
        with c3:
            st.number_input("SYN flag count", key="ex_syn")
            st.number_input("ACK flag count", key="ex_ack")
            st.number_input("PSH flag count", key="ex_psh")
            st.number_input("RST flag count", key="ex_rst")
            st.number_input("FIN flag count", key="ex_fin")
            st.text_input("Src IP", key="ex_src_ip")
            st.text_input("Dst IP", key="ex_dst_ip")
            threshold = st.slider("Decision threshold", 0.0, 1.0, 0.5, 0.05)

        submitted = st.form_submit_button("Score flow")

    if submitted:
        flow = _flow_from_session_state()
        try:
            out = _send_predict(flow, threshold=threshold)
            _render_verdict(out)
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")


def _flow_from_session_state() -> dict:
    """Build a FlowRecord-shaped dict from the Manual-scoring widget values."""
    fwd_mean = st.session_state["ex_fwd_pkt_len_mean"]
    bwd_mean = st.session_state["ex_bwd_pkt_len_mean"]
    total_fwd = st.session_state["ex_total_fwd_packets"]
    total_bwd = st.session_state["ex_total_bwd_packets"]
    duration = st.session_state["ex_flow_duration"]
    return {
        "protocol":                 st.session_state["ex_protocol"],
        "flow_duration":            duration,
        "total_fwd_packets":        total_fwd,
        "total_bwd_packets":        total_bwd,
        "total_length_fwd_packets": total_fwd * fwd_mean,
        "total_length_bwd_packets": total_bwd * bwd_mean,
        "fwd_packet_length_max":    st.session_state["ex_fwd_pkt_len_max"],
        "fwd_packet_length_mean":   fwd_mean,
        "bwd_packet_length_max":    st.session_state["ex_bwd_pkt_len_max"],
        "bwd_packet_length_mean":   bwd_mean,
        "flow_bytes_per_s":         st.session_state["ex_flow_bytes_per_s"],
        "flow_packets_per_s":       st.session_state["ex_flow_packets_per_s"],
        "flow_iat_mean":            st.session_state["ex_flow_iat_mean"],
        "flow_iat_std":             st.session_state["ex_flow_iat_std"],
        "fwd_iat_total":            duration * 0.5,
        "bwd_iat_total":            duration * 0.5,
        "fin_flag_count":           st.session_state["ex_fin"],
        "syn_flag_count":           st.session_state["ex_syn"],
        "rst_flag_count":           st.session_state["ex_rst"],
        "psh_flag_count":           st.session_state["ex_psh"],
        "ack_flag_count":           st.session_state["ex_ack"],
        "src_ip":                   st.session_state["ex_src_ip"],
        "dst_ip":                   st.session_state["ex_dst_ip"],
    }


def render_examples_tab() -> None:
    """A library of pre-built request bodies — one per category — with a
    short explanation of WHY those parameters yield that classification.
    Each card can be loaded into the Manual-scoring form or sent at the
    API straight away."""
    st.subheader("Request examples — one per category")
    st.markdown(
        "Each card below is a complete <code>POST /predict</code> body that the trained "
        "model is expected to classify as the named category. The values come straight from "
        "the per-class distributions in <code>scripts/generate_synthetic_dataset.py</code> "
        "and have been validated against the production <code>best.joblib</code> artefact. "
        "Use <strong>Load into Manual scoring</strong> to copy the values into the form on the "
        "previous tab, or <strong>Send to /predict now</strong> to fire it at the API and see "
        "the verdict right here.",
        unsafe_allow_html=True,
    )

    for name, e in EXAMPLES.items():
        color = CATEGORY_COLOR[name]
        header_html = (
            f"<span style='display:inline-block;width:10px;height:10px;border-radius:50%;"
            f"background:{color};box-shadow:0 0 6px {color};margin-right:8px;vertical-align:middle'></span>"
            f"<strong>{name}</strong>"
            f" &nbsp;<span style='color:#94a3b8;font-size:13px'>· {e['tag']}</span>"
        )
        # The expander label can't contain HTML — use the category name with the
        # one-line "why_short" as the visible summary. Full styling lives inside.
        with st.expander(f"  {name}  —  {e['why_short']}", expanded=(name == "BENIGN")):
            st.markdown(header_html, unsafe_allow_html=True)
            st.write("")

            left, right = st.columns([3, 2])
            with left:
                st.markdown("**Why these params produce a `" + name + "` verdict**")
                st.write(e["why_full"])
                st.markdown("**Key signals the trees split on**")
                tbl = pd.DataFrame(
                    [{"feature": f, "value": v, "why it matters": w} for f, v, w in e["signals"]]
                )
                st.dataframe(tbl, hide_index=True, use_container_width=True)
            with right:
                st.markdown("**Request body** (paste into Swagger at `/docs` if you want)")
                st.code(
                    json.dumps({"flows": [e["flow"]], "threshold": 0.5}, indent=2),
                    language="json",
                )

            b1, b2, _ = st.columns([1.5, 1.5, 2])
            with b1:
                if st.button(f"Load into Manual scoring", key=f"load_{name}", use_container_width=True):
                    apply_example_to_form(name)
                    st.success(
                        f"Loaded **{name}** into the Manual scoring form — switch tabs to see it."
                    )
            with b2:
                if st.button(f"Send to /predict now", key=f"send_{name}", use_container_width=True):
                    try:
                        out = _send_predict(e["flow"], threshold=0.5)
                        _render_verdict(out, header=f"Verdict for the {name} preset")
                    except Exception as exc:
                        st.error(f"Prediction failed: {exc}")

    st.divider()
    st.markdown(
        "<small style='color:#64748b'>"
        "<strong>Reading the table:</strong> the <em>feature</em> column lists the parameter "
        "the model is most sensitive to for this category, <em>value</em> shows the level used "
        "in the preset, and <em>why it matters</em> explains the intuition. The same parameters "
        "are visualised in <code>docs/anomaly-detector-breakdown.html</code> as a heat map."
        "</small>",
        unsafe_allow_html=True,
    )


def main() -> None:
    render_header()
    health = _api_get("/health")
    metrics = _api_get("/metrics")
    alerts = _api_get("/alerts", limit=200)

    render_health(health)
    st.divider()

    tabs = st.tabs(
        ["📊 Overview", "🚨 Alerts", "🧪 Manual scoring", "📋 Request examples", "ℹ️ About"]
    )
    with tabs[0]:
        render_metrics(metrics)
    with tabs[1]:
        st.subheader(f"Recent alerts ({len(alerts or [])})")
        render_alerts(alerts)
    with tabs[2]:
        render_predict_form()
    with tabs[3]:
        render_examples_tab()
    with tabs[4]:
        st.markdown(
            """
            **Network Traffic Anomaly Detector** — Personal Research Project (PRP)

            * Backend: FastAPI · scikit-learn
            * Dataset: CICIDS2017 / synthetic CIC-flow features
            * Algorithms: Random Forest, Gradient Boosting, Isolation Forest, One-Class SVM
            * Frontend: Streamlit + Plotly

            Built as part of the Cybersecurity *Attack & Defend* minor at Fontys
            University of Applied Sciences. See `docs/research/DOT_Research.md`
            for the full research substantiation and `docs/evidence/` for
            per-LO evidence dossiers.
            """
        )
    st.caption(f"Last refresh: {datetime.utcnow().isoformat(timespec='seconds')} UTC · API: `{API_URL}`")


if __name__ == "__main__":
    main()
