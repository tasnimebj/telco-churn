"""Inference only: load a trusted artifact and predict without training data."""

import argparse
import hashlib
import json
from pathlib import Path

import joblib
import pandas as pd

from telco_churn.pipeline import prepare_features


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="JSON list of feature records")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", type=Path, default=Path("models/selected_pipeline.joblib"))
    parser.add_argument("--metadata", type=Path, default=Path("models/metadata.json"))
    args = parser.parse_args()
    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    if hashlib.sha256(args.model.read_bytes()).hexdigest() != metadata["artifact_sha256"]:
        raise ValueError("Model hash does not match metadata; use the matching artifact pair.")
    # Only load artifacts whose source you trust; joblib is pickle based.
    pipeline = joblib.load(args.model)
    records = pd.DataFrame(json.loads(args.input.read_text(encoding="utf-8")))
    X = prepare_features(records)
    positive_index = list(pipeline.classes_).index(1)
    scores = pipeline.predict_proba(X)[:, positive_index]
    result = {
        "positive_class": "Yes = 1",
        "threshold": metadata["configuration"]["threshold"],
        "positive_probabilities": scores.tolist(),
        "predictions": (scores >= metadata["configuration"]["threshold"]).astype(int).tolist(),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Predictions saved to {args.output}")


if __name__ == "__main__":
    main()
