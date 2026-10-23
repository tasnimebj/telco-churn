"""TP02 milestone 3: fair validation comparison; the test set stays reserved."""

import hashlib
import json
from pathlib import Path
from time import perf_counter

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, average_precision_score, confusion_matrix,
    precision_score, recall_score, f1_score,
)
from sklearn.tree import DecisionTreeClassifier

from telco_churn.dataset import read_dataset
from telco_churn.first_model import SEED, split_customers
from telco_churn.pipeline import FEATURES, build_pipeline, prepare_features


def evaluate_model(model, X, y, threshold):
    positive_index = list(model.classes_).index(1)
    scores = model.predict_proba(X)[:, positive_index]
    predictions = (scores >= threshold).astype(int)
    return {
        "average_precision": float(average_precision_score(y, scores)),
        "precision": float(precision_score(y, predictions, zero_division=0)),
        "recall": float(recall_score(y, predictions, zero_division=0)),
        "f1": float(f1_score(y, predictions, zero_division=0)),
        "accuracy": float(accuracy_score(y, predictions)),
        "confusion_matrix": confusion_matrix(y, predictions, labels=[0, 1]).tolist(),
    }


def run_comparison(config):
    source = Path("data/raw/datasets.csv")
    df = read_dataset(source)
    parts = split_customers(df)
    prior = json.loads(Path("evidence/tp02/first_model.json").read_text(encoding="utf-8"))
    if hashlib.sha256(source.read_bytes()).hexdigest() != prior["source_sha256"]:
        raise ValueError("Input hash changed since milestone 1.")
    for name, part in zip(["train", "validation", "test"], parts):
        if part["customerID"].tolist() != prior["splits"][name]["customer_ids"]:
            raise ValueError("Customer allocations changed since milestone 1.")
    train, valid, _ = parts
    X_train, X_valid = prepare_features(train), prepare_features(valid)
    y_train = train["Churn"].map({"No": 0, "Yes": 1})
    y_valid = valid["Churn"].map({"No": 0, "Yes": 1})
    classifiers = {
        "baseline": DummyClassifier(strategy="most_frequent"),
        "logistic": LogisticRegression(**config["models"]["logistic"]),
        "decision_tree": DecisionTreeClassifier(**config["models"]["decision_tree"]),
        "random_forest": RandomForestClassifier(**config["models"]["random_forest"]),
    }
    results, fitted = [], {}
    for name, classifier in classifiers.items():
        candidate = build_pipeline(classifier)
        start = perf_counter()
        candidate.fit(X_train, y_train)
        fit_seconds = perf_counter() - start
        results.append({
            "model": name,
            "parameters": classifier.get_params(),
            "fit_seconds": fit_seconds,
            **evaluate_model(candidate, X_valid, y_valid, config["threshold"]),
        })
        fitted[name] = candidate
    learned = [row for row in results if row["model"] != "baseline"]
    winner = max(learned, key=lambda row: row["average_precision"])
    return {
        "configuration": config,
        "seed": SEED,
        "features": FEATURES,
        "positive_class": "Yes = 1",
        "matrix_definition": "Rows actual; columns predicted; labels [0=No, 1=Yes]",
        "zero_division_policy": "Undefined precision, recall or F1 reported as zero.",
        "test_evaluated": False,
        "source_sha256": prior["source_sha256"],
        "customer_allocations": prior["splits"],
        "validation_results": results,
        "selected_model": winner["model"],
        "selection_note": "Highest validation average precision among learned candidates; no test evaluation or threshold tuning.",
    }, fitted[winner["model"]]


def main():
    config = json.loads(Path("configs/train.json").read_text(encoding="utf-8"))
    if config["selection_metric"] != "average_precision":
        raise ValueError("This implementation selects by average_precision.")
    if not 0 <= config["threshold"] <= 1:
        raise ValueError("Probability threshold must be in [0, 1].")
    report, selected_pipeline = run_comparison(config)
    folder = Path("evidence/tp02")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "comparison.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    table = pd.DataFrame(report["validation_results"]).drop(columns=["parameters", "confusion_matrix"])
    table.to_csv(folder / "comparison.csv", index=False)
    print(table.to_string(index=False))
    print("Selected:", report["selected_model"])
    (folder / "selection.md").write_text(
        f"# Validation selection\n\nSelected: {report['selected_model']}.\n\n"
        + config["selection_reason"] + "\n\n" + report["selection_note"]
        + "\n\nConfigurations and threshold were declared before this comparison. Timings describe this machine only. "
        + "These candidates all use the same six features and split; the earlier two-feature model is not part of this fair comparison.\n",
        encoding="utf-8",
    )
    from telco_churn.artifacts import save_and_check
    save_and_check(selected_pipeline, report)


if __name__ == "__main__":
    main()
