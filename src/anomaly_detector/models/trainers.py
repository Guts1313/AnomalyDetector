"""Train and evaluate the four candidate algorithms (SRQ2).

The four algorithms cover the three classical strategies for anomaly detection
identified in the literature study:

* **Supervised / discriminative**: Random Forest, Gradient Boosting
* **Unsupervised / density-based**: Isolation Forest
* **One-class boundary**: One-Class SVM

This breadth lets us substantiate the SRQ2 trade-off matrix (accuracy / speed /
false-positive rate) with concrete numbers per family. Deep-learning approaches
(autoencoder, LSTM) are documented as out-of-scope in the PRP and reserved for
future work.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, IsolationForest, RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.svm import OneClassSVM

from ..features import build_default_pipeline
from ..features.pipeline import FeaturePipeline
from ..features.schema import LABEL_COLUMN


@dataclass
class TrainResult:
    name: str
    family: str
    pipeline: FeaturePipeline
    model: object
    metrics: Dict[str, float]
    confusion: list
    per_class: dict
    train_seconds: float
    predict_micro_seconds_per_sample: float
    notes: str = ""


@dataclass
class TrainComparison:
    results: list[TrainResult] = field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        rows = []
        for r in self.results:
            row = {"algorithm": r.name, "family": r.family}
            row.update(r.metrics)
            row["train_s"] = round(r.train_seconds, 3)
            row["predict_us_per_sample"] = round(r.predict_micro_seconds_per_sample, 1)
            rows.append(row)
        return pd.DataFrame(rows).sort_values("f1_macro", ascending=False)


def _benchmark_predict(model_predict_fn: Callable[[np.ndarray], np.ndarray], X: np.ndarray) -> float:
    if len(X) == 0:
        return 0.0
    start = time.perf_counter()
    _ = model_predict_fn(X)
    elapsed = time.perf_counter() - start
    return (elapsed / len(X)) * 1_000_000  # microseconds per sample


def _eval_supervised(model, X_test: np.ndarray, y_test: np.ndarray) -> tuple[dict, list, dict]:
    y_pred = model.predict(X_test)
    metrics = {
        "precision_macro": precision_score(y_test, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_test, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_test, y_pred, average="macro", zero_division=0),
    }
    # binary attack-vs-benign roc auc when probabilities available
    if hasattr(model, "predict_proba"):
        try:
            proba = model.predict_proba(X_test)
            y_bin = (y_test != "BENIGN").astype(int)
            # P(attack) = 1 - P(benign)
            classes = list(model.classes_)
            if "BENIGN" in classes:
                benign_idx = classes.index("BENIGN")
                attack_proba = 1 - proba[:, benign_idx]
            else:
                attack_proba = proba.max(axis=1)
            metrics["roc_auc_attack"] = roc_auc_score(y_bin, attack_proba)
        except Exception:
            pass
    cm = confusion_matrix(y_test, y_pred).tolist()
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    return metrics, cm, report


def _eval_one_class(model, X_test: np.ndarray, y_test: np.ndarray) -> tuple[dict, list, dict]:
    raw = model.predict(X_test)  # +1 inlier, -1 outlier
    y_pred = np.where(raw == 1, "BENIGN", "ATTACK")
    y_true_bin = np.where(y_test == "BENIGN", "BENIGN", "ATTACK")
    metrics = {
        "precision_macro": precision_score(y_true_bin, y_pred, average="macro", zero_division=0),
        "recall_macro": recall_score(y_true_bin, y_pred, average="macro", zero_division=0),
        "f1_macro": f1_score(y_true_bin, y_pred, average="macro", zero_division=0),
    }
    if hasattr(model, "score_samples"):
        try:
            scores = -model.score_samples(X_test)  # higher = more anomalous
            y_bin = (y_true_bin != "BENIGN").astype(int)
            metrics["roc_auc_attack"] = roc_auc_score(y_bin, scores)
        except Exception:
            pass
    cm = confusion_matrix(y_true_bin, y_pred, labels=["BENIGN", "ATTACK"]).tolist()
    report = classification_report(y_true_bin, y_pred, output_dict=True, zero_division=0)
    return metrics, cm, report


def _train_random_forest(X_train, y_train) -> object:
    model = RandomForestClassifier(
        n_estimators=200, max_depth=None, n_jobs=-1, class_weight="balanced", random_state=42
    )
    model.fit(X_train, y_train)
    return model


def _train_gradient_boosting(X_train, y_train) -> object:
    model = GradientBoostingClassifier(n_estimators=120, max_depth=3, random_state=42)
    model.fit(X_train, y_train)
    return model


def _train_isolation_forest(X_train, y_train) -> object:
    # Train only on benign traffic — true semi-supervised setup
    benign_mask = (y_train == "BENIGN")
    contamination = max(0.005, min(0.2, 1 - benign_mask.mean()))
    model = IsolationForest(
        n_estimators=200, contamination=contamination, n_jobs=-1, random_state=42
    )
    model.fit(X_train[benign_mask])
    return model


def _train_one_class_svm(X_train, y_train) -> object:
    benign_mask = (y_train == "BENIGN")
    # Cap sample size — OC-SVM is O(n^2)
    X_benign = X_train[benign_mask]
    if len(X_benign) > 5000:
        rng = np.random.default_rng(42)
        idx = rng.choice(len(X_benign), size=5000, replace=False)
        X_benign = X_benign[idx]
    model = OneClassSVM(kernel="rbf", gamma="scale", nu=0.05)
    model.fit(X_benign)
    return model


ALGO_REGISTRY: dict[str, dict] = {
    "random_forest": {
        "family": "supervised-ensemble",
        "train": _train_random_forest,
        "eval": _eval_supervised,
    },
    "gradient_boosting": {
        "family": "supervised-boosting",
        "train": _train_gradient_boosting,
        "eval": _eval_supervised,
    },
    "isolation_forest": {
        "family": "unsupervised-density",
        "train": _train_isolation_forest,
        "eval": _eval_one_class,
    },
    "one_class_svm": {
        "family": "one-class-boundary",
        "train": _train_one_class_svm,
        "eval": _eval_one_class,
    },
}


def train_all_models(df: pd.DataFrame, test_size: float = 0.25, seed: int = 42) -> TrainComparison:
    """Train every algorithm in :data:`ALGO_REGISTRY` and return a comparison."""
    y = df[LABEL_COLUMN].astype(str).values
    pipeline = build_default_pipeline()
    X = pipeline.fit_transform(df)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed
    )

    comp = TrainComparison()
    for name, spec in ALGO_REGISTRY.items():
        t0 = time.perf_counter()
        model = spec["train"](X_train, y_train)
        train_s = time.perf_counter() - t0
        metrics, cm, report = spec["eval"](model, X_test, y_test)
        predict_us = _benchmark_predict(model.predict, X_test[: min(1000, len(X_test))])
        comp.results.append(
            TrainResult(
                name=name,
                family=spec["family"],
                pipeline=pipeline,
                model=model,
                metrics=metrics,
                confusion=cm,
                per_class=report,
                train_seconds=train_s,
                predict_micro_seconds_per_sample=predict_us,
            )
        )
    return comp


def persist_best(comp: TrainComparison, out_dir: str, prefer: str | None = None) -> str:
    """Save the recommended production model as `models/best.joblib`.

    Selection rule:
    * If `prefer` is supplied (e.g. "gradient_boosting"), persist that model.
    * Otherwise prefer the highest-F1 *supervised* algorithm when its F1 is
      within 0.02 of the overall top F1, because supervised models also
      provide per-attack-class output that's required for SRQ5/SRQ6 — analyst
      usability and per-category evaluation.
    * Fallback to the overall F1 winner.
    """
    from pathlib import Path
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    df = comp.to_dataframe()
    if prefer is not None:
        best_name = prefer
    else:
        top = df.iloc[0]
        supervised = df[df["family"].str.startswith("supervised")]
        if not supervised.empty and (top["f1_macro"] - supervised.iloc[0]["f1_macro"]) < 0.02:
            best_name = supervised.iloc[0]["algorithm"]
        else:
            best_name = top["algorithm"]
    best = next(r for r in comp.results if r.name == best_name)
    bundle = {
        "name": best.name,
        "family": best.family,
        "feature_pipeline": best.pipeline,
        "model": best.model,
        "metrics": best.metrics,
        "supervised": "supervised" in best.family,
    }
    target = out / "best.joblib"
    joblib.dump(bundle, target)
    return str(target)
