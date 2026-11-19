import numpy as np
import pytest

from telco_churn.pipeline import FEATURES, prepare_features


@pytest.mark.parametrize("column", FEATURES)
def test_missing_required_feature_is_rejected(sample_features, column):
    with pytest.raises(ValueError, match=f"Missing required features:.*{column}"):
        prepare_features(sample_features.drop(columns=column))


def test_supported_missing_numeric_and_unseen_category(
    fitted_pipeline, sample_features
):
    unseen = "Never-seen contract"
    encoder = (
        fitted_pipeline.named_steps["preprocessor"]
        .named_transformers_["cat"]
        .named_steps["encoder"]
    )
    assert unseen not in sample_features["Contract"].values
    assert unseen not in encoder.categories_[0]
    batch = sample_features.head(3).copy()
    batch.loc[batch.index[0], "TotalCharges"] = np.nan
    batch.loc[batch.index[0], "Contract"] = unseen
    X = prepare_features(batch)
    predictions = fitted_pipeline.predict(X)
    probabilities = fitted_pipeline.predict_proba(X)
    assert predictions.shape == (len(batch),)
    assert set(predictions).issubset({0, 1})
    assert probabilities.shape == (len(batch), 2)
    assert np.isfinite(probabilities).all()
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    np.testing.assert_allclose(probabilities.sum(axis=1), 1.0, atol=1e-12)


def test_whitespace_is_missing_but_malformed_numeric_is_rejected(sample_features):
    batch = sample_features.copy()
    batch.loc[0, "TotalCharges"] = "   "
    assert np.isnan(prepare_features(batch).loc[0, "TotalCharges"])
    batch.loc[0, "TotalCharges"] = "invalid-charge"
    with pytest.raises(ValueError, match="Unable to parse string"):
        prepare_features(batch)


def test_target_and_id_are_not_features(sample_features):
    batch = sample_features.assign(Churn="Yes", customerID="invented")
    assert list(prepare_features(batch).columns) == FEATURES
