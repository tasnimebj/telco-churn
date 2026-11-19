"""Inference-only fresh-process recovery through the MLflow candidate alias."""

import argparse
import json
import sys
from pathlib import Path

import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd

from telco_churn.pipeline import prepare_features


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="evidence/tp03/reload_check.json")
    args = parser.parse_args()
    folder = Path("evidence/tp03")
    info = json.loads((folder / "tracking_results.json").read_text())
    mlflow.set_tracking_uri(info["tracking_uri"])
    version = mlflow.MlflowClient().get_model_version_by_alias(
        "telco-churn", "candidate"
    )
    if str(version.version) != str(info["registered_version"]):
        raise ValueError(
            "Alias moved; expected selected version is no longer candidate"
        )
    pipeline = mlflow.sklearn.load_model(info["alias_uri"])
    records = pd.DataFrame(json.loads((folder / "inference_batch.json").read_text()))
    scores = pipeline.predict_proba(prepare_features(records))[
        :, list(pipeline.classes_).index(1)
    ]
    predictions = (scores >= info["threshold"]).astype(int)
    expected = json.loads((folder / "expected_predictions.json").read_text())
    np.testing.assert_allclose(scores, expected["probabilities"], atol=1e-12, rtol=0)
    np.testing.assert_array_equal(predictions, expected["predictions"])
    result = {
        "alias_uri": info["alias_uri"],
        "version": version.version,
        "run_id": version.run_id,
        "probabilities": scores.tolist(),
        "predictions": predictions.tolist(),
        "agreement": True,
        "atol": 1e-12,
        "fit_called": False,
    }
    Path(args.output).write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
