# TP02 validation and handover

## Completed local verification

- Fixed stratified customer allocations are recorded in `first_model.json` and checked in subsequent training.
- Three learned classifiers and the majority baseline were compared with identical six-feature inputs and validation metrics.
- Random forest was selected by validation average precision, using the predeclared configuration in `configs/train.json`.
- The selected fitted pipeline was saved and reloaded in a separate Python process without fit or labels.
- Reloaded probabilities matched with absolute tolerance 1e-12; thresholded classes matched exactly.
- Training-only preprocessing statistics, unchanged state during prediction, supported missingness/unknown categories and invalid-input failures passed automated checks; see `reliability_checks.json`.
- The test set remains reserved and has not been evaluated.

## Issue observed and resolution

The TP01 CSV has an outer CSV quoting layer, so direct pandas loading would expose one column rather than the expected fields. TP02 reuses the existing `read_dataset` function to decode the layer in memory. Subsequent training and inference checks succeeded. This is an implementation observation, not independent peer feedback.

## Remaining handover evidence

- Independent reviewer: pending; the author is working alone.
- Peer training or trusted-artifact inference attempt: pending.
- Peer issue, author response and successful retry: pending.
- TP02 pull request URL: https://github.com/tasnimebj/telco-churn/pull/3 (provided by the author).
- Artifact delivery: `models/selected_pipeline.joblib` and `models/metadata.json` must be included in a separate submission archive or regenerated using the documented training workflow; they are excluded from Git.

Self-validation and automated checks are not represented as independent review. Confirm an acceptable alternative with the instructor if peer execution cannot be arranged.
