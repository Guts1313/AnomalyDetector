"""Feature pipeline tests — guarantees train/inference parity."""
import numpy as np
import pandas as pd

from anomaly_detector.features import build_default_pipeline
from anomaly_detector.features.schema import FLOW_FEATURE_COLUMNS, NUMERIC_FEATURES


def _frame(n=5):
    return pd.DataFrame({
        "protocol": ["TCP"] * n,
        **{c: np.linspace(1, 10, n) for c in NUMERIC_FEATURES},
        "label": ["BENIGN"] * n,
    })


def test_pipeline_fits_and_transforms():
    pipe = build_default_pipeline()
    X = pipe.fit_transform(_frame())
    assert X.shape[0] == 5
    assert X.shape[1] > len(NUMERIC_FEATURES)  # categorical OHE adds columns


def test_pipeline_handles_missing_columns():
    pipe = build_default_pipeline()
    pipe.fit_transform(_frame())
    # Drop a feature on inference -> pipeline should still produce a result
    df = _frame()
    df = df.drop(columns=["flow_duration"])
    X = pipe.transform(df)
    assert X.shape[0] == 5
    assert not np.isnan(X).any()


def test_pipeline_robust_to_inf():
    df = _frame()
    df.loc[0, "flow_bytes_per_s"] = float("inf")
    df.loc[1, "flow_packets_per_s"] = float("-inf")
    pipe = build_default_pipeline()
    X = pipe.fit_transform(df)
    assert np.isfinite(X).all()
