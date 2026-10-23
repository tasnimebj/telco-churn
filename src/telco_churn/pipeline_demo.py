"""TP02 milestone 2: fit and validate the six-feature pipeline."""

import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix

from telco_churn.dataset import read_dataset
from telco_churn.first_model import SEED, split_customers
from telco_churn.pipeline import FEATURES, NUMERIC_FEATURES, build_pipeline, prepare_features


def main():
    df = read_dataset(Path("data/raw/datasets.csv"))
    train, valid, _ = split_customers(df)
    # Verify exact customer allocations against milestone 1 before training.
    previous = json.loads(Path("evidence/tp02/first_model.json").read_text(encoding="utf-8"))
    for name, part in zip(["train", "validation", "test"], split_customers(df)):
        if part["customerID"].tolist() != previous["splits"][name]["customer_ids"]:
            raise ValueError("Split allocation differs from milestone 1.")
    X_train = prepare_features(train)
    X_valid = prepare_features(valid)
    y_train = train["Churn"].map({"No": 0, "Yes": 1})
    y_valid = valid["Churn"].map({"No": 0, "Yes": 1})
    pipe = build_pipeline(LogisticRegression(max_iter=1000, random_state=SEED))
    pipe.fit(X_train, y_train)
    numeric = pipe.named_steps["preprocessor"].named_transformers_["num"]
    medians_before = numeric.named_steps["imputer"].statistics_.copy()
    np.testing.assert_allclose(medians_before, X_train[NUMERIC_FEATURES].median().to_numpy())
    predictions = pipe.predict(X_valid)
    np.testing.assert_array_equal(medians_before, numeric.named_steps["imputer"].statistics_)
    report = {
        "features": FEATURES,
        "seed": SEED,
        "test_evaluated": False,
        "same_customer_allocations_as_milestone_1": True,
        "validation_accuracy": float(accuracy_score(y_valid, predictions)),
        "confusion_matrix": confusion_matrix(y_valid, predictions, labels=[0, 1]).tolist(),
        "matrix_definition": "Rows actual, columns predicted; labels [0=No, 1=Yes]",
        "training_medians": dict(zip(NUMERIC_FEATURES, medians_before.tolist())),
        "imputer_matches_training_medians": True,
        "prediction_preserves_imputer_statistics": True,
    }
    output = Path("evidence/tp02/pipeline_demo.json")
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
