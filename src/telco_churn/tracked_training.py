"""Explicit TP03 tracking; run against the documented local MLflow server."""

import hashlib
import json
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path
from time import perf_counter

import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier

from telco_churn.dataset import read_dataset
from telco_churn.first_model import SEED, split_customers
from telco_churn.pipeline import FEATURES, build_pipeline, prepare_features
from telco_churn.training import evaluate_model

URI = "http://127.0.0.1:5000"
EVIDENCE = Path("evidence/tp03")


def git(*args):
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={Path.cwd().as_posix()}", *args], text=True
    ).strip()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    mlflow.set_tracking_uri(URI)
    experiment = mlflow.set_experiment("telco-churn-tp03")
    config = json.loads(Path("configs/train.json").read_text())
    if config["selection_metric"] != "average_precision":
        raise ValueError("Primary metric must remain average_precision")
    source = Path("data/raw/datasets.csv")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    previous = json.loads(Path("evidence/tp02/first_model.json").read_text())
    if digest != previous["source_sha256"]:
        raise ValueError("Original CSV hash changed")
    parts = split_customers(read_dataset(source))
    for name, part in zip(["train", "validation", "test"], parts):
        if part["customerID"].tolist() != previous["splits"][name]["customer_ids"]:
            raise ValueError("Customer allocations changed")
    train, valid, _ = parts
    X_train, X_valid = prepare_features(train), prepare_features(valid)
    y_train, y_valid = [
        part["Churn"].map({"No": 0, "Yes": 1}) for part in (train, valid)
    ]
    datasets = [
        mlflow.data.from_pandas(part[FEATURES + ["Churn"]], name=name, targets="Churn")
        for part, name in [(train, "telco_train"), (valid, "telco_validation")]
    ]
    commit = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--porcelain", "--untracked-files=no"))
    provenance = {
        "git_commit": commit,
        "git_dirty": dirty,
        "data_sha256": digest,
        "features": FEATURES,
        "class_mapping": {"No": 0, "Yes": 1},
        "seed": SEED,
        "threshold": config["threshold"],
        "selection_metric": "validation average precision from positive probabilities",
        "confusion_matrix_order": "rows actual, columns predicted, labels [0,1]",
        "customer_allocations": previous["splits"],
        "test_evaluated": False,
        "input_policy": "Call prepare_features; see references/tp02_pipeline.md",
    }
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    rows, fitted = [], {}
    for name, cls in [
        ("logistic", LogisticRegression),
        ("decision_tree", DecisionTreeClassifier),
        ("random_forest", RandomForestClassifier),
    ]:
        estimator = cls(**config["models"][name])
        with mlflow.start_run(run_name=name) as run:
            mlflow.log_params(
                {
                    "model_type": cls.__name__,
                    "split_seed": SEED,
                    "threshold": config["threshold"],
                    **estimator.get_params(),
                }
            )
            mlflow.set_tags(
                {
                    "git_commit": commit,
                    "git_dirty": str(dirty).lower(),
                    "data_sha256": digest,
                }
            )
            for dataset, context in zip(datasets, ["training", "validation"]):
                mlflow.log_input(dataset, context=context)
            pipeline = build_pipeline(estimator)
            start = perf_counter()
            pipeline.fit(X_train, y_train)
            elapsed = perf_counter() - start
            metrics = evaluate_model(pipeline, X_valid, y_valid, config["threshold"])
            logged_metrics = {
                f"val_{key}": value
                for key, value in metrics.items()
                if key != "confusion_matrix"
            }
            mlflow.log_metrics({**logged_metrics, "fit_seconds": elapsed})
            mlflow.log_dict(
                {
                    "matrix": metrics["confusion_matrix"],
                    "labels": [0, 1],
                    "rows": "actual",
                    "columns": "predicted",
                },
                "confusion_matrix.json",
            )
            mlflow.log_dict(provenance, "provenance.json")
            requirements = [
                f"{package}=={version(package)}"
                for package in [
                    "mlflow",
                    "scikit-learn",
                    "numpy",
                    "scipy",
                    "pandas",
                    "joblib",
                    "cloudpickle",
                ]
            ]
            info = mlflow.sklearn.log_model(
                pipeline,
                name="churn_pipeline",
                input_example=X_train.head(3),
                serialization_format="cloudpickle",
                pip_requirements=requirements,
            )
            row = {
                "candidate": name,
                "run_id": run.info.run_id,
                "model_uri": info.model_uri,
                "fit_seconds": elapsed,
                **logged_metrics,
            }
            rows.append(row)
            fitted[name] = pipeline
    selected = max(rows, key=lambda item: item["val_average_precision"])
    registered = mlflow.register_model(selected["model_uri"], "telco-churn")
    mlflow.MlflowClient().set_registered_model_alias(
        "telco-churn", "candidate", registered.version
    )
    batch = X_valid.head(5)
    batch.to_json(EVIDENCE / "inference_batch.json", orient="records", indent=2)
    pipeline = fitted[selected["candidate"]]
    scores = pipeline.predict_proba(batch)[:, list(pipeline.classes_).index(1)]
    expected = {
        "probabilities": scores.tolist(),
        "predictions": (scores >= config["threshold"]).astype(int).tolist(),
    }
    (EVIDENCE / "expected_predictions.json").write_text(json.dumps(expected, indent=2))
    result = {
        "tracking_uri": URI,
        "experiment_id": experiment.experiment_id,
        "runs": rows,
        "selected": selected,
        "registered_name": "telco-churn",
        "registered_version": registered.version,
        "alias": "candidate",
        "alias_uri": "models:/telco-churn@candidate",
        "threshold": config["threshold"],
        "git_commit": commit,
        "git_dirty": dirty,
        "source_sha256": digest,
        "test_evaluated": False,
    }
    (EVIDENCE / "tracking_results.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
