"""Small invented customers; no CSV, network, models or MLflow service needed."""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from telco_churn.pipeline import build_pipeline, prepare_features


@pytest.fixture
def sample_features():
    return pd.DataFrame(
        {
            "tenure": [1, 3, 6, 9, 12, 18, 24, 30, 36, 42, 48, 54, 60, 66, 70, 72],
            "MonthlyCharges": [
                20.0,
                80.0,
                45.0,
                90.0,
                30.0,
                70.0,
                55.0,
                100.0,
                25.0,
                85.0,
                60.0,
                95.0,
                35.0,
                75.0,
                65.0,
                105.0,
            ],
            "TotalCharges": [
                "20",
                "240",
                "270",
                "810",
                "360",
                "1260",
                "1320",
                "3000",
                "900",
                "3570",
                "2880",
                "5130",
                "2100",
                "4950",
                "4550",
                "7560",
            ],
            "Contract": ["Month-to-month", "One year", "Two year", "Month-to-month"]
            * 4,
            "InternetService": ["DSL", "Fiber optic", "No", "DSL"] * 4,
            "PaymentMethod": [
                "Electronic check",
                "Mailed check",
                "Bank transfer",
                "Credit card",
            ]
            * 4,
        }
    )


@pytest.fixture
def fitted_pipeline(sample_features):
    target = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    pipeline = build_pipeline(LogisticRegression(max_iter=1000, random_state=42))
    return pipeline.fit(prepare_features(sample_features), target)
