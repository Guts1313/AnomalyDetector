"""Render the diagram + planning figures the expanded research report embeds.

Everything here is drawn with matplotlib so the report has no external-tool
dependency (no Graphviz / Mermaid). Output PNGs land in docs/screenshots/ next
to the charts and frontend captures.

    .venv/Scripts/python.exe -m scripts.make_report_diagrams
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)

# Palette — mirrors frontend/src/theme/tokens.css and the report headings.
INK = "#1f2a44"
MUTED = "#55657a"
PURPLE = "#9457ff"
INDIGO = "#6366f1"
BLUE = "#3b82f6"
GREEN = "#10b981"
ORANGE = "#f97316"
RED = "#ef4444"
YELLOW = "#eab308"
CYAN = "#06b6d4"
PINK = "#ec4899"
SURFACE = "#f4f6fb"
CARD = "#ffffff"

CAT_COLORS = {
    "BENIGN": GREEN,
    "DDoS": RED,
    "DoS": ORANGE,
    "PortScan": CYAN,
    "BruteForce": YELLOW,
    "WebAttack": PURPLE,
    "Botnet": "#a855f7",
    "Infiltration": PINK,
}

plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 11,
        "axes.edgecolor": "#cdd5e3",
        "savefig.facecolor": "white",
    }
)


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def _box(ax, x, y, w, h, text, *, fc=CARD, ec=INDIGO, tc=INK, fs=10, bold=False,
         lw=1.6, rounding=0.025):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.01,rounding_size={rounding}",
        linewidth=lw, edgecolor=ec, facecolor=fc, mutation_aspect=1,
    )
    ax.add_patch(box)
    ax.text(
        x + w / 2, y + h / 2, text, ha="center", va="center",
        fontsize=fs, color=tc, fontweight="bold" if bold else "normal",
        wrap=True, linespacing=1.3,
    )
    return (x + w / 2, y + h / 2)


def _arrow(ax, p0, p1, *, color=MUTED, lw=1.8, style="-|>", ls="-", rad=0.0):
    ax.add_patch(
        FancyArrowPatch(
            p0, p1, arrowstyle=style, mutation_scale=16,
            color=color, lw=lw, linestyle=ls,
            connectionstyle=f"arc3,rad={rad}", shrinkA=6, shrinkB=6,
        )
    )


def _label(ax, x, y, text, *, color=MUTED, fs=8.5, ha="center", style="italic"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color, fontstyle=style)


def _frame(ax, title):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    if title:
        ax.text(2, 97, title, fontsize=14, fontweight="bold", color=INK)


# ---------------------------------------------------------------------------
# 1 — Gantt chart for the 4-sprint PRP plan
# ---------------------------------------------------------------------------
def gantt():
    start = date(2026, 3, 17)

    def d(y, m, dd):
        return mdates.date2num(date(y, m, dd))

    # (label, start, end, colour, sprint-group)
    tasks = [
        ("Initial idea & project definition", d(2026, 3, 17), d(2026, 3, 20), INK, 0),
        ("Project plan & main/sub research questions", d(2026, 3, 18), d(2026, 3, 26), INDIGO, 1),
        ("User stories & Scrum board setup", d(2026, 3, 19), d(2026, 3, 24), INDIGO, 1),
        ("Trend analysis & literature study (Library)", d(2026, 3, 20), d(2026, 3, 26), INDIGO, 1),
        ("Feature schema & synthetic dataset generator", d(2026, 3, 26), d(2026, 4, 4), BLUE, 2),
        ("4-algorithm benchmark + model selection", d(2026, 3, 30), d(2026, 4, 8), BLUE, 2),
        ("FastAPI service + SQLite audit store (PoC)", d(2026, 4, 2), d(2026, 4, 13), BLUE, 2),
        ("Network drawing, flowcharts, attack scenarios", d(2026, 4, 6), d(2026, 4, 13), BLUE, 2),
        ("Threshold/severity tuning & FP control", d(2026, 4, 13), d(2026, 4, 22), GREEN, 3),
        ("Per-class evaluation + test suite (validate)", d(2026, 4, 16), d(2026, 4, 28), GREEN, 3),
        ("React dashboard + Streamlit analyst view", d(2026, 4, 20), d(2026, 5, 6), GREEN, 3),
        ("Attack/defend lab (attacker+defender Docker)", d(2026, 4, 24), d(2026, 5, 11), GREEN, 3),
        ("Coach/peer feedback & validation round", d(2026, 5, 4), d(2026, 5, 11), GREEN, 3),
        ("Present research approach & results to coach", d(2026, 5, 11), d(2026, 5, 25), PURPLE, 4),
        ("Research document & advisory report", d(2026, 5, 18), d(2026, 6, 11), PURPLE, 4),
        ("Presentation slides & final delivery", d(2026, 6, 1), d(2026, 6, 11), PURPLE, 4),
    ]

    milestones = [
        (d(2026, 3, 17), "17 Mar\nIdea & definition"),
        (d(2026, 3, 26), "26 Mar\nSprint 1 — Define & Analyse"),
        (d(2026, 4, 13), "13 Apr\nSprint 2 — Design & Implement"),
        (d(2026, 5, 11), "11 May\nSprint 3 — Optimise & Validate"),
        (d(2026, 6, 11), "11 Jun\nFinal PRP delivery"),
    ]

    fig, ax = plt.subplots(figsize=(13.5, 8.2))
    n = len(tasks)
    for i, (label, s, e, color, _grp) in enumerate(tasks):
        y = n - i - 1
        ax.barh(y, e - s, left=s, height=0.55, color=color, alpha=0.92,
                edgecolor="white", linewidth=0.8, zorder=3)
        ax.text(s - 1.5, y, label, ha="right", va="center", fontsize=9.3, color=INK)

    ax.set_yticks([])
    ax.set_ylim(-1.4, n + 0.4)

    # Milestone diamonds + vertical guides
    for mx, mlabel in milestones:
        ax.axvline(mx, color=MUTED, ls=":", lw=1.0, alpha=0.7, zorder=1)
        ax.scatter([mx], [n - 0.2], marker="D", s=70, color=RED, zorder=5,
                   edgecolor="white", linewidth=0.8)
        ax.text(mx, n + 0.05, mlabel, ha="center", va="bottom", fontsize=8.2,
                color=INK, fontweight="bold")

    # Sprint band shading
    bands = [
        (d(2026, 3, 17), d(2026, 3, 26), "Sprint 1", INDIGO),
        (d(2026, 3, 26), d(2026, 4, 13), "Sprint 2", BLUE),
        (d(2026, 4, 13), d(2026, 5, 11), "Sprint 3", GREEN),
        (d(2026, 5, 11), d(2026, 6, 11), "Sprint 4", PURPLE),
    ]
    for bs, be, name, color in bands:
        ax.axvspan(bs, be, color=color, alpha=0.05, zorder=0)
        ax.text((bs + be) / 2, -1.0, name, ha="center", va="center",
                fontsize=9.5, color=color, fontweight="bold")

    ax.xaxis_date()
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    ax.set_xlim(d(2026, 3, 13), d(2026, 6, 15))
    plt.setp(ax.get_xticklabels(), rotation=0, fontsize=8.5, color=MUTED)
    ax.grid(axis="x", linestyle=":", alpha=0.35, zorder=0)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.set_title(
        "PRP delivery plan — four Scrum sprints, March–June 2026",
        fontsize=14, fontweight="bold", color=INK, pad=28, loc="left",
    )
    plt.tight_layout()
    plt.savefig(OUT / "20_gantt.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2 — C4 context diagram
# ---------------------------------------------------------------------------
def c4_context():
    fig, ax = plt.subplots(figsize=(12, 6.8))
    _frame(ax, "C4 Level 1 — System context")

    analyst = _box(ax, 6, 62, 20, 16, "Security analyst\n(triages alerts,\ndrills into flows)",
                   fc=SURFACE, ec=INK, bold=True)
    mleng = _box(ax, 6, 22, 20, 16, "ML engineer\n(retrains model,\nreloads via /admin)",
                 fc=SURFACE, ec=INK, bold=True)
    sysm = _box(ax, 40, 38, 26, 24,
                "Network Traffic\nAnomaly Detector\n\n[FastAPI · scikit-learn ·\nReact + Streamlit]",
                fc="#eef1ff", ec=PURPLE, bold=True, fs=11)
    src = _box(ax, 76, 62, 20, 16, "PCAP / CSV\nflow sources\n(CICFlowMeter)",
               fc=SURFACE, ec=MUTED)
    siem = _box(ax, 76, 22, 20, 16, "SIEM / SOC\n(Splunk · Elastic ·\nWazuh)", fc=SURFACE, ec=MUTED)

    _arrow(ax, analyst, sysm, color=INDIGO)
    _label(ax, 33, 64, "views dashboard,\nHTTPS")
    _arrow(ax, mleng, sysm, color=INDIGO)
    _label(ax, 33, 33, "retrains &\nreloads model")
    _arrow(ax, src, sysm, color=BLUE)
    _label(ax, 71, 64, "flow features\nJSON / CSV")
    _arrow(ax, sysm, siem, color=GREEN)
    _label(ax, 71, 33, "severity alerts\n/alerts feed")
    plt.tight_layout()
    plt.savefig(OUT / "21_c4_context.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3 — C4 container diagram
# ---------------------------------------------------------------------------
def c4_container():
    fig, ax = plt.subplots(figsize=(12, 7.4))
    _frame(ax, "C4 Level 2 — Containers")

    react = _box(ax, 4, 70, 26, 16, "React + TypeScript SPA\n[Vite · Plotly]\nport 5173 / nginx :80",
                 fc="#eef1ff", ec=PURPLE, bold=True, fs=9.5)
    stream = _box(ax, 4, 46, 26, 16, "Streamlit dashboard\n[Plotly]\nport 8501",
                  fc="#eef1ff", ec=PURPLE, bold=True, fs=9.5)
    api = _box(ax, 40, 56, 28, 20,
               "FastAPI service\n[Pydantic v2 · scikit-learn]\nport 8000 · 6 endpoints",
               fc="#e9fbf3", ec=GREEN, bold=True, fs=10)
    model = _box(ax, 78, 68, 18, 14, "Model bundle\nbest.joblib\n(pipeline+model)",
                 fc=SURFACE, ec=BLUE, fs=9.5)
    db = _box(ax, 78, 46, 18, 14, "SQLite\nalerts.db\n(audit log)", fc=SURFACE, ec=BLUE, fs=9.5)

    attacker = _box(ax, 12, 14, 24, 16,
                    "Attacker container\n[nmap · hping3 · hydra ·\nsqlmap] /attack :8001",
                    fc="#fdeaea", ec=RED, bold=True, fs=9)
    defender = _box(ax, 50, 14, 30, 16,
                    "Defender container\n[nginx · sshd · tcpdump ·\ncicflowmeter · iptables] :8002",
                    fc="#eef7ff", ec=CYAN, bold=True, fs=9)

    _arrow(ax, react, api, color=PURPLE)
    _arrow(ax, stream, api, color=PURPLE)
    _label(ax, 35, 62, "HTTP/JSON")
    _arrow(ax, api, model, color=BLUE)
    _label(ax, 73, 70, "loads")
    _arrow(ax, api, db, color=BLUE)
    _label(ax, 73, 50, "audits")
    _arrow(ax, attacker, defender, color=RED)
    _label(ax, 43, 22, "real packets\n(lab bridge)")
    _arrow(ax, defender, (api[0] - 4, api[1] - 10), color=CYAN, rad=-0.2)
    _label(ax, 60, 38, "POST /predict")
    _arrow(ax, (react[0], react[1] - 8), (attacker[0], attacker[1] + 8),
           color=ORANGE, ls="--", rad=-0.25)
    _label(ax, 6, 44, '"Run on lab"', color=ORANGE)
    plt.tight_layout()
    plt.savefig(OUT / "22_c4_container.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4 — Attack/defend lab topology
# ---------------------------------------------------------------------------
def lab_topology():
    fig, ax = plt.subplots(figsize=(12.5, 7.2))
    _frame(ax, "Attack / defend lab — live ML-to-firewall loop")

    fe = _box(ax, 4, 74, 30, 14, '① Analyst clicks "Run on lab"\nReact Examples tab',
              fc="#eef1ff", ec=PURPLE, bold=True, fs=9.5)
    atk = _box(ax, 4, 44, 30, 18,
               "② ad-attacker\nnmap / hping3 / hydra / sqlmap\nfires the matching tool",
               fc="#fdeaea", ec=RED, bold=True, fs=9.5)
    dfn = _box(ax, 40, 36, 34, 30,
               "③ ad-defender\nnginx :80 · sshd :22  (victims)\n"
               "tcpdump → cicflowmeter → live.csv\n"
               "flow_streamer.py tails rows\n"
               "⑥ iptables -A INPUT -s <ip> DROP",
               fc="#eef7ff", ec=CYAN, bold=True, fs=9.3)
    api = _box(ax, 80, 56, 16, 14, "④ ad-api\n/predict\nGB model", fc="#e9fbf3", ec=GREEN, bold=True)
    db = _box(ax, 80, 30, 16, 12, "⑤ alerts.db\n→ /alerts", fc=SURFACE, ec=BLUE, fs=9.5)

    _arrow(ax, fe, atk, color=PURPLE)
    _label(ax, 21, 68, "POST :8001/attack\n{preset,target,dur}", ha="left")
    _arrow(ax, atk, dfn, color=RED)
    _label(ax, 36, 49, "real packets\nlab bridge", ha="left")
    _arrow(ax, dfn, api, color=CYAN)
    _label(ax, 77, 64, "flow JSON", ha="center")
    _arrow(ax, api, db, color=GREEN)
    _label(ax, 90, 46, "verdict", ha="center")
    _arrow(ax, (db[0], db[1] - 6), (fe[0] + 6, fe[1] - 7), color=BLUE, ls="--", rad=0.35)
    _label(ax, 40, 12, "Alerts tab refresh ← /alerts (severity-coloured rows)", color=BLUE)
    # feedback loop: block lands -> attacker times out
    _arrow(ax, (dfn[0] - 12, dfn[1] - 14), (atk[0] + 6, atk[1] - 9), color=INK, ls="--", rad=0.3)
    _label(ax, 24, 33, "⑦ subsequent probes time out\n(DROP rule landed)", color=INK)
    plt.tight_layout()
    plt.savefig(OUT / "23_lab_topology.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5 — Attack -> detect -> block sequence diagram
# ---------------------------------------------------------------------------
def sequence():
    fig, ax = plt.subplots(figsize=(12.5, 7.6))
    _frame(ax, "Sequence — one attack through the detect-and-block pipeline")

    lanes = [
        ("Analyst /\nReact FE", 10, PURPLE),
        ("Attacker\ncontainer", 32, RED),
        ("Defender\ncapture", 54, CYAN),
        ("API +\nGB model", 76, GREEN),
        ("iptables\nfirewall", 93, INK),
    ]
    top, bottom = 88, 8
    for name, x, color in lanes:
        _box(ax, x - 7, 90, 14, 7, name, fc=SURFACE, ec=color, bold=True, fs=8.8)
        ax.plot([x, x], [bottom, top], color=color, ls="--", lw=1.0, alpha=0.5)

    def msg(y, x0, x1, text, color, dashed=False):
        _arrow(ax, (x0, y), (x1, y), color=color, ls="--" if dashed else "-")
        midx = (x0 + x1) / 2
        ax.text(midx, y + 1.6, text, ha="center", va="bottom", fontsize=8.3, color=INK)

    msg(82, 10, 32, '"Run on lab" → POST /attack', PURPLE)
    msg(74, 32, 54, "nmap -sS / hping3 -S flood (real packets)", RED)
    msg(66, 54, 54, "tcpdump → cicflowmeter assembles flow", CYAN)
    ax.add_patch(FancyArrowPatch((54, 66), (54, 62), arrowstyle="-|>",
                 mutation_scale=14, color=CYAN, connectionstyle="arc3,rad=-1.2"))
    msg(57, 54, 76, "POST /predict  { flow features }", CYAN)
    msg(49, 76, 76, "GB model: verdict=DDoS, score 0.99, severity=critical", GREEN)
    ax.add_patch(FancyArrowPatch((76, 49), (76, 45), arrowstyle="-|>",
                 mutation_scale=14, color=GREEN, connectionstyle="arc3,rad=-1.2"))
    msg(41, 76, 93, "is_attack & score≥0.7 → DROP <attacker_ip>", GREEN)
    msg(33, 93, 32, "subsequent probes time out", INK, dashed=True)
    msg(25, 76, 10, "/alerts feed → severity-coloured row", BLUE, dashed=True)

    ax.text(50, 15, "End-to-end: real tool → captured flow → ML verdict → automated firewall response",
            ha="center", fontsize=9, color=MUTED, fontstyle="italic")
    plt.tight_layout()
    plt.savefig(OUT / "24_attack_defend_sequence.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 6 — Risk heat-map (Impact x Likelihood) over STRIDE + security risks
# ---------------------------------------------------------------------------
def risk_heatmap():
    # (id, likelihood 1-3, impact 1-3)
    risks = [
        ("SR1 evasion", 3, 3), ("SR7 TLS blind", 3, 2), ("T7 adversarial", 3, 3),
        ("SR3 audit DB", 2, 2), ("SR4 DoS batch", 2, 2), ("T5 DoS", 2, 2),
        ("T3 repudiation", 2, 2), ("T4 info-disc", 2, 2),
        ("SR2 model tamper", 1, 3), ("SR5 priv-esc", 1, 3), ("SR6 poisoning", 1, 3),
        ("T2 tamper", 1, 3), ("T6 EoP", 1, 3), ("T8 poisoning", 1, 3),
        ("T1 spoofing", 1, 1),
    ]
    fig, ax = plt.subplots(figsize=(9.5, 7.6))
    grid = np.array([
        [GREEN, YELLOW, ORANGE],
        [YELLOW, ORANGE, RED],
        [ORANGE, RED, "#b91c1c"],
    ])
    for i in range(3):
        for j in range(3):
            ax.add_patch(plt.Rectangle((j, i), 1, 1, color=grid[i, j], alpha=0.30,
                                       ec="white", lw=2))
    from collections import defaultdict
    cell = defaultdict(list)
    for name, lk, im in risks:
        cell[(im - 1, lk - 1)].append(name)
    for (i, j), names in cell.items():
        ax.text(j + 0.5, i + 0.5, "\n".join(names), ha="center", va="center",
                fontsize=8.2, color=INK)
    ax.set_xticks([0.5, 1.5, 2.5])
    ax.set_xticklabels(["Low", "Medium", "High"], fontsize=11)
    ax.set_yticks([0.5, 1.5, 2.5])
    ax.set_yticklabels(["Low", "Medium", "High"], fontsize=11)
    ax.set_xlabel("Likelihood", fontsize=12, color=INK)
    ax.set_ylabel("Impact", fontsize=12, color=INK)
    ax.set_xlim(0, 3)
    ax.set_ylim(0, 3)
    ax.set_title("Security risk register — Impact × Likelihood\n(STRIDE threats T1–T8 + risks SR1–SR7)",
                 fontsize=13, fontweight="bold", color=INK)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(length=0)
    plt.tight_layout()
    plt.savefig(OUT / "25_risk_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 7 — Dataset composition + per-attack feature fingerprint
# ---------------------------------------------------------------------------
def dataset_fingerprint():
    cats = ["BENIGN", "DDoS", "DoS", "PortScan", "BruteForce", "WebAttack", "Botnet", "Infiltration"]
    shares = [70, 7, 7, 5, 4, 3, 2.5, 1.5]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.2),
                                   gridspec_kw={"width_ratios": [1, 1.35]})

    # Left: class-share donut
    colors = [CAT_COLORS[c] for c in cats]
    wedges, _ = ax1.pie(shares, colors=colors, startangle=90,
                        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=1.5))
    ax1.legend(wedges, [f"{c} — {s}%" for c, s in zip(cats, shares)],
               loc="center", fontsize=8.5, frameon=False)
    ax1.set_title("Synthetic dataset class shares\n(20 000 flows, CICIDS-2017 prior)",
                  fontsize=12, fontweight="bold", color=INK)

    # Right: per-attack feature fingerprint heat map (illustrative intensities 0-1)
    feats = ["flow_dur", "pkts/s", "bytes/s", "syn_flag", "psh_flag", "iat_std", "fwd_len"]
    M = np.array([
        [0.50, 0.30, 0.35, 0.20, 0.25, 0.55, 0.45],  # BENIGN
        [0.15, 0.98, 0.85, 0.95, 0.10, 0.15, 0.20],  # DDoS
        [0.30, 0.80, 0.55, 0.85, 0.10, 0.30, 0.25],  # DoS
        [0.10, 0.70, 0.15, 0.90, 0.05, 0.20, 0.10],  # PortScan
        [0.20, 0.45, 0.20, 0.60, 0.55, 0.25, 0.20],  # BruteForce
        [0.25, 0.40, 0.60, 0.30, 0.90, 0.30, 0.85],  # WebAttack
        [0.80, 0.20, 0.20, 0.25, 0.30, 0.10, 0.30],  # Botnet
        [0.85, 0.35, 0.80, 0.20, 0.45, 0.40, 0.95],  # Infiltration
    ])
    im = ax2.imshow(M, cmap="magma", aspect="auto", vmin=0, vmax=1)
    ax2.set_xticks(range(len(feats)))
    ax2.set_xticklabels(feats, rotation=30, ha="right", fontsize=9)
    ax2.set_yticks(range(len(cats)))
    ax2.set_yticklabels(cats, fontsize=9.5)
    for i in range(len(cats)):
        for j in range(len(feats)):
            ax2.text(j, i, f"{M[i, j]:.1f}", ha="center", va="center",
                     fontsize=7.5, color="white" if M[i, j] < 0.6 else "black")
    ax2.set_title("Per-category feature fingerprint\n(relative intensity the trees split on)",
                  fontsize=12, fontweight="bold", color=INK)
    fig.colorbar(im, ax=ax2, fraction=0.045, label="relative intensity")
    plt.tight_layout()
    plt.savefig(OUT / "26_dataset_fingerprint.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def main():
    gantt()
    c4_context()
    c4_container()
    lab_topology()
    sequence()
    risk_heatmap()
    dataset_fingerprint()
    print("[+] Wrote diagrams 20–26 to", OUT)


if __name__ == "__main__":
    main()
