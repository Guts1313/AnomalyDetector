"""Train all four candidate algorithms and persist the best one.

Outputs:
- models/best.joblib          -> chosen winner (highest macro-F1)
- models/comparison_matrix.csv -> SRQ2 deliverable
- models/comparison_matrix.md  -> markdown copy for inclusion in evidence dossiers
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from anomaly_detector.models.trainers import persist_best, train_all_models


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=str, required=True, help="Path to a CSV with the canonical schema")
    p.add_argument("--out-dir", type=str, default="models")
    p.add_argument("--test-size", type=float, default=0.25)
    p.add_argument(
        "--prefer",
        type=str,
        default=None,
        choices=[None, "random_forest", "gradient_boosting", "isolation_forest", "one_class_svm"],
        help="Force a particular algorithm to be persisted as the production model.",
    )
    args = p.parse_args()

    print(f"[+] Loading {args.data}")
    df = pd.read_csv(args.data)
    print(f"[+] Loaded {len(df):,} rows, label distribution:")
    print(df["label"].value_counts().to_string())

    print("[+] Training all algorithms (this can take a couple of minutes)")
    comp = train_all_models(df, test_size=args.test_size)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    matrix = comp.to_dataframe()
    matrix.to_csv(out_dir / "comparison_matrix.csv", index=False)
    matrix.to_markdown(out_dir / "comparison_matrix.md", index=False)

    print("\n[+] Algorithm comparison (SRQ2 deliverable):")
    print(matrix.to_string(index=False))

    target = persist_best(comp, out_dir=str(out_dir), prefer=args.prefer)
    print(f"\n[+] Best model saved to {target}")

    # Per-class report for the production model -> useful for SRQ6
    import joblib as _joblib
    prod_bundle = _joblib.load(target)
    prod_name = prod_bundle["name"]
    prod = next(r for r in comp.results if r.name == prod_name)
    with (out_dir / "per_class_report.json").open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "production_model": prod_name,
                "metrics": prod.metrics,
                "report": prod.per_class,
                "confusion": prod.confusion,
            },
            fh,
            indent=2,
        )
    print(f"[+] Per-class report saved to {out_dir / 'per_class_report.json'} (model: {prod_name})")


if __name__ == "__main__":
    main()
