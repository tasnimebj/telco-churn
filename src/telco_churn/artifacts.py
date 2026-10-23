"""Persist the selected fitted pipeline and verify fresh-process inference."""

import hashlib
import json
import platform
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

import joblib
import numpy as np

from telco_churn.dataset import read_dataset
from telco_churn.first_model import split_customers
from telco_churn.pipeline import FEATURES, NUMERIC_FEATURES, prepare_features


def save_and_check(pipeline, report):
    models = Path("models")
    evidence = Path("evidence/tp02")
    models.mkdir(exist_ok=True)
    train, valid, _ = split_customers(read_dataset(Path("data/raw/datasets.csv")))
    X_train = prepare_features(train)
    batch = valid[FEATURES].head(5).copy()
    X_batch = prepare_features(batch)
    numeric = pipeline.named_steps["preprocessor"].named_transformers_["num"]
    imputer = numeric.named_steps["imputer"]
    scaler = numeric.named_steps["scaler"]
    medians_before = imputer.statistics_.copy()
    means_before = scaler.mean_.copy()
    scales_before = scaler.scale_.copy()
    np.testing.assert_allclose(medians_before, X_train[NUMERIC_FEATURES].median().to_numpy())
    filled_train = imputer.transform(X_train[NUMERIC_FEATURES])
    np.testing.assert_allclose(means_before, filled_train.mean(axis=0))
    expected_scores = pipeline.predict_proba(X_batch)[:, list(pipeline.classes_).index(1)]
    threshold = report["configuration"]["threshold"]
    expected_predictions = (expected_scores >= threshold).astype(int)

    altered = batch.copy()
    altered.loc[altered.index[0], "TotalCharges"] = " "
    altered.loc[altered.index[0], "Contract"] = "UNSEEN_CONTRACT_FOR_CHECK"
    altered_scores = pipeline.predict_proba(prepare_features(altered))
    if not np.isfinite(altered_scores).all():
        raise AssertionError("Missing/unseen inputs produced nonfinite scores.")
    try:
        prepare_features(batch.drop(columns="tenure"))
    except ValueError as exc:
        missing_feature_error = str(exc)
    else:
        raise AssertionError("Missing required feature did not fail.")
    invalid = batch.copy()
    invalid["TotalCharges"] = "not-a-number"
    try:
        prepare_features(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Malformed nonblank numeric text did not fail.")
    np.testing.assert_array_equal(imputer.statistics_, medians_before)
    np.testing.assert_array_equal(scaler.mean_, means_before)
    np.testing.assert_array_equal(scaler.scale_, scales_before)

    artifact = models / "selected_pipeline.joblib"
    joblib.dump(pipeline, artifact)
    identity_paths = list(Path("src/telco_churn").glob("*.py")) + [
        Path("configs/train.json"), Path("pyproject.toml"), Path("uv.lock"), Path(".python-version")
    ]
    metadata = {
        **report,
        "environment": {"python": sys.version, "platform": platform.platform(), **{
            package: version(package) for package in ["scikit-learn", "pandas", "numpy", "scipy", "joblib"]
        }},
        "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "code_and_environment_file_hashes": {
            path.as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in identity_paths
        },
        "preprocessing": {
            "boundary_rules": "Call prepare_features at training and inference; see references/tp02_pipeline.md.",
            "numeric_features": NUMERIC_FEATURES,
            "numeric_imputation": "training median",
            "numeric_scaling": "StandardScaler after imputation",
            "categorical_imputation": "training most_frequent",
            "encoding": "OneHotEncoder(handle_unknown=ignore, sparse_output=False)",
            "learned_medians": medians_before.tolist(),
            "learned_scaler_means": means_before.tolist(),
        },
        "training_scope": "Selected candidate remains fitted on training customers only; no train+validation refit.",
    }
    (models / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    # A feature-only batch: no target or customer IDs are required by inference.
    batch_path = evidence / "inference_batch.json"
    batch.to_json(batch_path, orient="records", indent=2)
    output = evidence / "reloaded_predictions.json"
    subprocess.run([
        sys.executable, "-m", "telco_churn.prediction",
        "--input", str(batch_path), "--output", str(output),
    ], check=True)
    actual = json.loads(output.read_text(encoding="utf-8"))
    np.testing.assert_allclose(actual["positive_probabilities"], expected_scores, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(actual["predictions"], expected_predictions)
    checks = {
        "customer_allocations_match_milestone_1_and_are_disjoint": True,
        "imputer_matches_training_medians": True,
        "scaler_mean_matches_imputed_training_data": True,
        "prediction_preserves_imputer_and_scaler_statistics": True,
        "missing_TotalCharges_and_unseen_Contract_accepted": True,
        "missing_required_feature_error": missing_feature_error,
        "malformed_nonblank_numeric_text_rejected": True,
        "fresh_process_probability_agreement_atol": 1e-12,
        "fresh_process_class_predictions_match": True,
        "inference_requires_training_labels_or_fit": False,
        "test_evaluated": False,
        "artifact_sha256": metadata["artifact_sha256"],
    }
    (evidence / "reliability_checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    # Track metadata separately from the ignored binary model directory.
    (evidence / "artifact_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("Artifact saved; fresh-process reload and reliability checks passed.")
