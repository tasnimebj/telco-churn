import joblib
import numpy as np

from telco_churn.pipeline import prepare_features


def test_reload_preserves_predictions(tmp_path, fitted_pipeline, sample_features):
    X = prepare_features(sample_features)
    before_scores = fitted_pipeline.predict_proba(X)
    before_classes = fitted_pipeline.predict(X)
    artifact = tmp_path / "pipeline.joblib"
    joblib.dump(fitted_pipeline, artifact)
    loaded = joblib.load(artifact)  # Our own temporary, trusted test artifact.
    np.testing.assert_allclose(
        loaded.predict_proba(X), before_scores, rtol=0, atol=1e-12
    )
    np.testing.assert_array_equal(loaded.predict(X), before_classes)
