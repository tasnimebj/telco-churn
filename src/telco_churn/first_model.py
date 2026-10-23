"""TP02 milestone 1: fixed splits and two-feature validation evaluation."""

import hashlib
import json
from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

from telco_churn.dataset import read_dataset

SEED = 42
FEATURES = ["tenure", "MonthlyCharges"]


def split_customers(df):
    """Return the same stratified allocations for an unchanged input order."""
    if df["customerID"].isna().any() or df["customerID"].duplicated().any():
        raise ValueError("Customer IDs must be present and unique.")
    if df["Churn"].isna().any() or not df["Churn"].isin(["No", "Yes"]).all():
        raise ValueError("Churn must contain only No and Yes.")
    train, remaining = train_test_split(
        df, test_size=0.4, stratify=df["Churn"], random_state=SEED
    )
    valid, test = train_test_split(
        remaining, test_size=0.5, stratify=remaining["Churn"], random_state=SEED
    )
    groups = [set(part["customerID"]) for part in (train, valid, test)]
    if groups[0] & groups[1] or groups[0] & groups[2] or groups[1] & groups[2]:
        raise ValueError("Customer overlap across splits.")
    return train, valid, test


def main():
    source = Path("data/raw/datasets.csv")
    df = read_dataset(source)
    train, valid, test = split_customers(df)
    X_train = train[FEATURES].apply(pd.to_numeric, errors="raise")
    X_valid = valid[FEATURES].apply(pd.to_numeric, errors="raise")
    y_train = train["Churn"].map({"No": 0, "Yes": 1})
    y_valid = valid["Churn"].map({"No": 0, "Yes": 1})

    results = []
    for name, model in {
        "majority_baseline": DummyClassifier(strategy="most_frequent"),
        "logistic_two_features": LogisticRegression(max_iter=1000, random_state=SEED),
    }.items():
        model.fit(X_train, y_train)
        predictions = model.predict(X_valid)
        results.append({
            "model": name,
            "validation_accuracy": float(accuracy_score(y_valid, predictions)),
            "confusion_matrix": confusion_matrix(y_valid, predictions, labels=[0, 1]).tolist(),
        })

    report = {
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "seed": SEED,
        "features": FEATURES,
        "positive_class": "Yes = 1; No = 0",
        "matrix_definition": "Rows = actual, columns = predicted; order [0, 1]; [[TN, FP], [FN, TP]]",
        "test_evaluated": False,
        "splits": {
            name: {"size": len(part), "customer_ids": part["customerID"].tolist()}
            for name, part in zip(["train", "validation", "test"], [train, valid, test])
        },
        "validation_results": results,
    }
    output = Path("evidence/tp02/first_model.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Split sizes:", {name: split["size"] for name, split in report["splits"].items()})
    print(report["matrix_definition"])
    print(json.dumps(results, indent=2))
    print(f"Evidence saved to {output}")


if __name__ == "__main__":
    main()
