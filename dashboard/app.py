"""Streamlit dashboard for the Network Traffic Anomaly Detector.

This is the D5 deliverable from the PRP (SRQ5 — analyst-friendly presentation).
The dashboard talks to the FastAPI backend, so it can be deployed independently
and run against any model rebuilt and reloaded via `POST /admin/reload`.
"""
from __future__ import annotations

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


def render_predict_form() -> None:
    st.subheader("Manual flow scoring")
    with st.form("score_one_flow"):
        c1, c2, c3 = st.columns(3)
        with c1:
            protocol = st.selectbox("Protocol", ["TCP", "UDP", "ICMP", "OTHER"], index=0)
            flow_duration = st.number_input("Flow duration (μs)", value=120_000.0, step=10_000.0)
            total_fwd_packets = st.number_input("Total fwd packets", value=10.0, step=1.0)
            total_bwd_packets = st.number_input("Total bwd packets", value=8.0, step=1.0)
            flow_packets_per_s = st.number_input("Packets / s", value=50.0, step=10.0)
            flow_bytes_per_s = st.number_input("Bytes / s", value=20_000.0, step=1000.0)
        with c2:
            fwd_packet_length_max = st.number_input("Fwd pkt length max", value=800.0)
            fwd_packet_length_mean = st.number_input("Fwd pkt length mean", value=450.0)
            bwd_packet_length_max = st.number_input("Bwd pkt length max", value=900.0)
            bwd_packet_length_mean = st.number_input("Bwd pkt length mean", value=500.0)
            flow_iat_mean = st.number_input("Flow IAT mean", value=500.0)
            flow_iat_std = st.number_input("Flow IAT std", value=200.0)
        with c3:
            syn = st.number_input("SYN flag count", value=1.0)
            ack = st.number_input("ACK flag count", value=5.0)
            psh = st.number_input("PSH flag count", value=1.0)
            rst = st.number_input("RST flag count", value=0.0)
            fin = st.number_input("FIN flag count", value=1.0)
            src_ip = st.text_input("Src IP", value="10.0.0.5")
            dst_ip = st.text_input("Dst IP", value="10.0.0.100")
            threshold = st.slider("Decision threshold", 0.0, 1.0, 0.5, 0.05)

        submitted = st.form_submit_button("Score flow")

    if submitted:
        flow = {
            "protocol": protocol,
            "flow_duration": flow_duration,
            "total_fwd_packets": total_fwd_packets,
            "total_bwd_packets": total_bwd_packets,
            "total_length_fwd_packets": total_fwd_packets * fwd_packet_length_mean,
            "total_length_bwd_packets": total_bwd_packets * bwd_packet_length_mean,
            "fwd_packet_length_max": fwd_packet_length_max,
            "fwd_packet_length_mean": fwd_packet_length_mean,
            "bwd_packet_length_max": bwd_packet_length_max,
            "bwd_packet_length_mean": bwd_packet_length_mean,
            "flow_bytes_per_s": flow_bytes_per_s,
            "flow_packets_per_s": flow_packets_per_s,
            "flow_iat_mean": flow_iat_mean,
            "flow_iat_std": flow_iat_std,
            "fwd_iat_total": flow_duration * 0.5,
            "bwd_iat_total": flow_duration * 0.5,
            "fin_flag_count": fin,
            "syn_flag_count": syn,
            "rst_flag_count": rst,
            "psh_flag_count": psh,
            "ack_flag_count": ack,
            "src_ip": src_ip,
            "dst_ip": dst_ip,
        }
        try:
            r = requests.post(f"{API_URL}/predict", json={"flows": [flow], "threshold": threshold}, timeout=15)
            r.raise_for_status()
            out = r.json()
            v = out["verdicts"][0]
            color = SEVERITY_COLOR.get(v["severity"], "#3b82f6")
            st.markdown(
                f"### Verdict: {_badge(v['verdict'], color)} · "
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
            st.caption(f"Model: `{out['model_name']}` ({out['model_family']}) · threshold used: {out['threshold_used']}")
        except Exception as exc:
            st.error(f"Prediction failed: {exc}")


def main() -> None:
    render_header()
    health = _api_get("/health")
    metrics = _api_get("/metrics")
    alerts = _api_get("/alerts", limit=200)

    render_health(health)
    st.divider()

    tabs = st.tabs(["📊 Overview", "🚨 Alerts", "🧪 Manual scoring", "ℹ️ About"])
    with tabs[0]:
        render_metrics(metrics)
    with tabs[1]:
        st.subheader(f"Recent alerts ({len(alerts or [])})")
        render_alerts(alerts)
    with tabs[2]:
        render_predict_form()
    with tabs[3]:
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
