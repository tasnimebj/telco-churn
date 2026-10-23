# AI-assisted review and reproduction

This review was executed by the coding assistant at the author's request. It is not an independent human peer review. Machine-readable results are in `ai_review_results.json`.

## Review questions and fixes

1. Can a reviewer given only the GitHub link run inference without obtaining the original CSV? Initially no: the fitted model directory was ignored. The author requested a Git-link-only submission. The selected pipeline (approximately 1.8 MB) and its matching metadata are now explicitly included through narrow ignore-rule exceptions. All other model outputs, raw data and virtual environments remain excluded. The README begins with the no-CSV inference commands.
2. Can mismatched model and metadata files silently be used together? Initially yes. Inference now checks the artifact SHA-256 against metadata before loading; a deliberately mismatched metadata file produced the expected visible failure. The hash establishes file identity, not trust in an external artifact.
3. Does a separate environment reproduce training and inference? Yes, under the conditions below.

## Actual execution

A separate workspace was populated from versioned source/configuration/evidence plus the selected artifact pair. No virtual environment was copied. `uv sync --locked --offline` created a new Python 3.12.15 environment from the lock file using the local uv cache.

Before supplying any raw CSV, the documented inference command succeeded. Its probabilities matched the original saved outputs within absolute tolerance 1e-12, and its classes matched exactly. The package import path was verified to point to the separate workspace.

Next the exact original CSV was copied separately into that workspace, and the documented first-model, pipeline-demo and training commands all succeeded. Customer allocations, all five validation metrics for all four candidates, and confusion matrices matched the original run. Fit durations varied, as expected. The selected model remained random forest. Reload and reliability checks passed. No test predictions or test metrics were computed.

## Limits

This was a separate workspace and fresh environment on the same Windows machine, using a local source snapshot and cached dependencies; it was not a network clone or cross-machine test. Full training still needs the original source CSV, whose original acquisition provider remains unconfirmed. Inference can be run with the Git-tracked artifact and feature-only batch. Independent human peer feedback has not been obtained, and instructor acceptance of this alternative has not been established.
