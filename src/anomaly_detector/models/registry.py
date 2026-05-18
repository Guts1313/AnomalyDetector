"""Lightweight on-disk model registry."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from ..features.pipeline import FeaturePipeline, ensure_flow_columns
from ..features.schema import FLOW_FEATURE_COLUMNS


@dataclass
class ModelArtifact:
    name: str
    family: str
    feature_pipeline: FeaturePipeline
    model: Any
    metrics: dict
    supervised: bool

    def predict(self, df: pd.DataFrame, threshold: float | None = None) -> dict:
        df = ensure_flow_columns(df)
        X = self.feature_pipeline.transform(df)
        if self.supervised:
            preds = self.model.predict(X)
            proba_map: list[dict] = []
            attack_scores: list[float] = []
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba(X)
                classes = list(self.model.classes_)
                for row in proba:
                    proba_map.append({c: float(row[i]) for i, c in enumerate(classes)})
                    if "BENIGN" in classes:
                        attack_scores.append(float(1 - row[classes.index("BENIGN")]))
                    else:
                        attack_scores.append(float(row.max()))
            else:
                proba_map = [{} for _ in preds]
                attack_scores = [0.0 if p == "BENIGN" else 1.0 for p in preds]
            verdicts = [str(p) for p in preds]
            if threshold is not None:
                verdicts = [
                    v if s >= threshold else ("BENIGN" if s < threshold else v)
                    for v, s in zip(verdicts, attack_scores)
                ]
            return {
                "verdicts": verdicts,
                "attack_scores": attack_scores,
                "class_probabilities": proba_map,
            }
        # one-class
        raw = self.model.predict(X)
        verdicts = ["BENIGN" if r == 1 else "ATTACK" for r in raw]
        if hasattr(self.model, "score_samples"):
            anomaly = -self.model.score_samples(X)
        else:
            anomaly = np.where(raw == 1, 0.0, 1.0)
        # Normalise to 0-1
        if len(anomaly):
            a_min, a_max = float(np.min(anomaly)), float(np.max(anomaly))
            if a_max - a_min > 1e-9:
                anomaly = (anomaly - a_min) / (a_max - a_min)
            else:
                anomaly = np.zeros_like(anomaly)
        attack_scores = [float(x) for x in anomaly]
        if threshold is not None:
            verdicts = ["ATTACK" if s >= threshold else "BENIGN" for s in attack_scores]
        return {
            "verdicts": verdicts,
            "attack_scores": attack_scores,
            "class_probabilities": [{} for _ in verdicts],
        }


class ModelRegistry:
    """File-system-backed registry. Loads `best.joblib` from a directory."""

    def __init__(self, models_dir: str | Path = "models") -> None:
        self.models_dir = Path(models_dir)
        self._artifact: ModelArtifact | None = None

    @property
    def is_loaded(self) -> bool:
        return self._artifact is not None

    def load(self) -> ModelArtifact:
        if self._artifact is not None:
            return self._artifact
        path = self.models_dir / "best.joblib"
        if not path.exists():
            raise FileNotFoundError(
                f"No trained model at {path}. Run `python -m scripts.train` first."
            )
        bundle = joblib.load(path)
        self._artifact = ModelArtifact(
            name=bundle["name"],
            family=bundle["family"],
            feature_pipeline=bundle["feature_pipeline"],
            model=bundle["model"],
            metrics=bundle.get("metrics", {}),
            supervised=bundle.get("supervised", True),
        )
        return self._artifact

    def reload(self) -> ModelArtifact:
        self._artifact = None
        return self.load()
