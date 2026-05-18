"""Render research charts (confusion matrix, per-class F1, algo comparison) as PNGs.

These artefacts are referenced by the DOT research document and the LO evidence
dossiers. They are regenerated automatically by the train script in CI but
can also be produced manually:

    python -m scripts.make_research_charts
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

MODELS_DIR = Path("models")
OUT_DIR = Path("docs/screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SEV_COLORS = {
    "BENIGN": "#10b981",
    "DDoS": "#1d4ed8",
    "DoS": "#3b82f6",
    "PortScan": "#ef4444",
    "BruteForce": "#f97316",
    "WebAttack": "#a855f7",
    "Botnet": "#eab308",
    "Infiltration": "#0ea5e9",
}


def _algo_comparison():
    matrix = pd.read_csv(MODELS_DIR / "comparison_matrix.csv")
    matrix = matrix.sort_values("f1_macro", ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(matrix))
    width = 0.27
    ax.barh(x - width, matrix["precision_macro"], width, label="Precision (macro)", color="#3b82f6")
    ax.barh(x, matrix["recall_macro"], width, label="Recall (macro)", color="#10b981")
    ax.barh(x + width, matrix["f1_macro"], width, label="F1 (macro)", color="#ef4444")
    ax.set_yticks(x)
    ax.set_yticklabels(matrix["algorithm"])
    ax.set_xlim(0, 1.0)
    ax.set_xlabel("Score")
    ax.set_title("Algorithm comparison — SRQ2 (CICIDS-synthetic, 20k flows)")
    ax.legend(loc="lower right")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    for i, row in enumerate(matrix.itertuples()):
        ax.text(row.f1_macro + 0.01, i + width, f"{row.f1_macro:.3f}", va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "04_algo_comparison.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def _confusion_and_per_class():
    with (MODELS_DIR / "per_class_report.json").open("r", encoding="utf-8") as fh:
        bundle = json.load(fh)
    report = bundle["report"]
    classes = [c for c in report if isinstance(report[c], dict) and c not in {"accuracy", "macro avg", "weighted avg"}]
    f1s = [report[c]["f1-score"] for c in classes]
    supports = [report[c]["support"] for c in classes]
    colors = [SEV_COLORS.get(c, "#64748b") for c in classes]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    order = np.argsort(f1s)[::-1]
    classes_o = [classes[i] for i in order]
    f1_o = [f1s[i] for i in order]
    sup_o = [supports[i] for i in order]
    cols_o = [colors[i] for i in order]
    bars = ax.bar(classes_o, f1_o, color=cols_o, edgecolor="white")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("F1-score")
    ax.set_title(
        f"Per-class F1 — {bundle['production_model']} (SRQ6) · macro F1 = {bundle['metrics']['f1_macro']:.3f}"
    )
    for bar, f1, sup in zip(bars, f1_o, sup_o):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            f1 + 0.02,
            f"{f1:.2f}\n(n={int(sup)})",
            ha="center",
            va="bottom",
            fontsize=9,
        )
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    plt.setp(ax.get_xticklabels(), rotation=20, ha="right")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "05_per_class_f1.png", dpi=140, bbox_inches="tight")
    plt.close(fig)

    # Confusion matrix
    cm = np.array(bundle["confusion"])
    if cm.shape[0] != len(classes):
        # When the production model is one-class the cm is 2x2 — handle gracefully
        classes_cm = ["BENIGN", "ATTACK"]
    else:
        classes_cm = classes
    fig, ax = plt.subplots(figsize=(7, 6))
    cm_norm = cm / cm.sum(axis=1, keepdims=True).clip(min=1)
    im = ax.imshow(cm_norm, cmap="Blues")
    ax.set_xticks(np.arange(len(classes_cm)))
    ax.set_yticks(np.arange(len(classes_cm)))
    ax.set_xticklabels(classes_cm, rotation=30, ha="right")
    ax.set_yticklabels(classes_cm)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion matrix — {bundle['production_model']} (row-normalised)")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j, i, f"{cm[i, j]}\n{cm_norm[i, j] * 100:.1f}%",
                ha="center", va="center",
                color="white" if cm_norm[i, j] > 0.5 else "black", fontsize=8,
            )
    fig.colorbar(im, ax=ax, fraction=0.04)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "06_confusion_matrix.png", dpi=140, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    _algo_comparison()
    _confusion_and_per_class()
    print(f"[+] Wrote charts to {OUT_DIR}/")


if __name__ == "__main__":
    main()
