"""Stateless input parsing and fresh, unfitted pipeline construction."""

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

NUMERIC_FEATURES = ["tenure", "MonthlyCharges", "TotalCharges"]
CATEGORICAL_FEATURES = ["Contract", "InternetService", "PaymentMethod"]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def prepare_features(records):
    """Apply these same stateless boundary rules at training and inference."""
    missing = sorted(set(FEATURES) - set(records.columns))
    if missing:
        raise ValueError(f"Missing required features: {missing}")
    result = records[FEATURES].copy()
    for column in NUMERIC_FEATURES:
        values = result[column]
        blank = values.astype("string").str.strip().eq("").fillna(False)
        # Only TotalCharges permits blank text; actual nulls are allowed in all numeric fields.
        if column != "TotalCharges" and blank.any():
            raise ValueError(f"Blank text is not allowed in {column}")
        values = values.mask(blank, np.nan)
        numeric = pd.to_numeric(values, errors="raise").astype(float)
        if np.isinf(numeric.to_numpy()).any():
            raise ValueError(f"Infinite value in {column}")
        result[column] = numeric
    for column in CATEGORICAL_FEATURES:
        values = result[column]
        if not values.dropna().map(lambda value: isinstance(value, str)).all():
            raise ValueError(f"Expected strings or missing values in {column}")
        # Normalize categorical blanks/nulls for the sklearn imputer.
        stripped = values.astype("string").str.strip()
        result[column] = stripped.replace("", pd.NA).astype(object).where(
            stripped.notna() & stripped.ne("").fillna(False), np.nan
        )
    return result


def build_pipeline(classifier):
    """Construct a fresh preprocessor; do not load data or fit here."""
    numeric = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("num", numeric, NUMERIC_FEATURES),
        ("cat", categorical, CATEGORICAL_FEATURES),
    ])
    return Pipeline([("preprocessor", preprocessor), ("classifier", classifier)])
