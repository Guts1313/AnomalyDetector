"""Feature engineering pipeline.

Wraps preprocessing (imputation, scaling, one-hot encoding) into a single
scikit-learn `Pipeline` that can be persisted with the model. This guarantees
that the exact same transformations are applied at train- and inference-time —
a common defect source in anomaly-detection systems (SRQ4: false-positive
stability).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

from .schema import CATEGORICAL_FEATURES, FLOW_FEATURE_COLUMNS, NUMERIC_FEATURES


@dataclass
class FeaturePipeline:
    """Thin wrapper around a fitted sklearn ColumnTransformer."""

    transformer: ColumnTransformer

    def fit(self, df: pd.DataFrame) -> "FeaturePipeline":
        self.transformer.fit(df[FLOW_FEATURE_COLUMNS])
        return self

    def transform(self, df: pd.DataFrame) -> np.ndarray:
        df = ensure_flow_columns(df)
        return self.transformer.transform(df[FLOW_FEATURE_COLUMNS])

    def fit_transform(self, df: pd.DataFrame) -> np.ndarray:
        df = ensure_flow_columns(df)
        return self.transformer.fit_transform(df[FLOW_FEATURE_COLUMNS])

    @property
    def output_dim(self) -> int:
        try:
            return self.transformer.transform(
                pd.DataFrame([_empty_row()], columns=FLOW_FEATURE_COLUMNS)
            ).shape[1]
        except Exception:
            return -1


def _empty_row() -> dict:
    row: dict[str, object] = {c: 0.0 for c in NUMERIC_FEATURES}
    for c in CATEGORICAL_FEATURES:
        row[c] = "TCP"
    return row


def ensure_flow_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of `df` with all expected columns present (fills missing with 0/UNK)."""
    df = df.copy()
    for col in NUMERIC_FEATURES:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        # Replace inf/-inf with 0 (CICFlowMeter occasionally produces these on degenerate flows)
        df[col] = df[col].replace([np.inf, -np.inf], 0.0)
    for col in CATEGORICAL_FEATURES:
        if col not in df.columns:
            df[col] = "UNK"
        df[col] = df[col].astype(str).fillna("UNK")
    return df


def build_default_pipeline() -> FeaturePipeline:
    """Default preprocessing: median imputation + RobustScaler for numeric,
    OneHotEncoder for categorical. Robust scaler is preferred over StandardScaler
    because flow metrics are heavily right-skewed (long tail of large flows)."""
    numeric_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="median")),
            ("scale", RobustScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    transformer = ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, NUMERIC_FEATURES),
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )
    return FeaturePipeline(transformer=transformer)
