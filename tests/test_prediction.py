import numpy as np

from telco_churn.pipeline import NUMERIC_FEATURES, prepare_features


def test_probability_contract(fitted_pipeline, sample_features):
    probabilities = fitted_pipeline.predict_proba(prepare_features(sample_features))
    classes = fitted_pipeline.classes_
    np.testing.assert_array_equal(classes, [0, 1])
    assert probabilities.shape == (len(sample_features), len(classes))
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, rtol=0, atol=1e-12)
    positive_index = list(classes).index(1)
    positive_scores = probabilities[:, positive_index]
    assert positive_scores.shape == (len(sample_features),)
    # This binary logistic model uses the same >0.5 rule except for exact ties.
    assert not np.any(positive_scores == 0.5)
    np.testing.assert_array_equal(
        fitted_pipeline.predict(prepare_features(sample_features)),
        (positive_scores > 0.5).astype(int),
    )


def test_prediction_does_not_refit_training_statistics(
    fitted_pipeline, sample_features
):
    numeric = fitted_pipeline.named_steps["preprocessor"].named_transformers_["num"]
    imputer = numeric.named_steps["imputer"]
    scaler = numeric.named_steps["scaler"]
    medians, means, scales = (
        imputer.statistics_.copy(),
        scaler.mean_.copy(),
        scaler.scale_.copy(),
    )
    train = prepare_features(sample_features)[NUMERIC_FEATURES]
    np.testing.assert_allclose(medians, train.median().to_numpy())
    batch = sample_features.copy()
    batch["tenure"] = 10000.0
    fitted_pipeline.predict_proba(prepare_features(batch))
    np.testing.assert_array_equal(imputer.statistics_, medians)
    np.testing.assert_array_equal(scaler.mean_, means)
    np.testing.assert_array_equal(scaler.scale_, scales)
