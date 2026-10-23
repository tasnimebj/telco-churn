# Telco Churn — TP01

## TP02: training and reusable prediction

From the project root, after supplying the unchanged CSV and running `python -m uv sync --locked`:

```powershell
python -m uv run --locked python -m telco_churn.first_model
python -m uv run --locked python -m telco_churn.pipeline_demo
python -m uv run --locked python -m telco_churn.training
```

The first command records the fixed stratified 60/20/20 customer allocation and a two-feature baseline. Later commands verify that allocation. Configuration is in `configs/train.json`; input types and preprocessing policies are in [the TP02 input policy](references/tp02_pipeline.md). Churn Yes is positive. The three learned classifiers use the same six features, fresh preprocessing, training-only fitting and validation metrics. Selection maximizes validation average precision; threshold metrics use probability >= 0.5. The test set remains reserved.

Training saves the selected fitted preprocessor and classifier together to `models/selected_pipeline.joblib`, alongside `models/metadata.json`. It also runs a separate inference process and verifies probability agreement with absolute tolerance 1e-12 and exact class agreement. Checks cover disjoint allocations, training-only imputation/scaling statistics, unchanged statistics after prediction, permitted missingness and unknown categories, and visible failures for missing features and malformed numeric text. Results, fit durations, selected-model rationale, metadata and checks are tracked under `evidence/tp02/`.

To predict without training execution or labels, after generating or obtaining the trusted artifact and metadata:

```powershell
python -m uv run --locked python -m telco_churn.prediction --input evidence/tp02/inference_batch.json --output reports/predictions.json
```

Input JSON contains a list of records with the six required unencoded features, without Churn. Only load trusted joblib artifacts, using matching dependency versions from `uv.lock`. The `models/` directory is deliberately excluded from Git: recreate it with the training command, or include both the artifact and metadata in the course's artifact submission location. The tracked metadata contains the artifact hash, source hash, exact customer allocations, configuration, metrics, library versions and code/dependency-file hashes.

Independent TP02 peer execution and feedback remain pending. Local automated checks do not constitute peer review. No claim of generalization on the reserved test set or probability calibration is made.

The business question is whether a telecom customer will churn. TP01 establishes a reproducible data inspection workflow; it does not train a model or infer the effects of retention actions from this customer snapshot.

## Setup and execution

This project was created manually with `uv init --package --python 3.12 telco-churn`. The recorded environment uses Python 3.12.15, pandas 3.1.0 and uv 0.13.5. Install uv before following these instructions. Run all commands below from the project root (the folder containing `pyproject.toml`).

1. Obtain the exact supplied `datasets.csv` described in [the data-source record](references/data_source.md). Create `data/raw/` and place the file at `data/raw/datasets.csv` without editing it.
2. Verify its SHA-256 in PowerShell:

   ```powershell
   Get-FileHash -LiteralPath data/raw/datasets.csv -Algorithm SHA256
   ```

   Expected: `62ca518b1ebbcd4c832c18c1a21629b03abe9033fef66fe2e38d8d030658a20c`.
3. Install the locked environment and verify imports:

   ```powershell
   python -m uv sync --locked
   python -m uv run --locked python -c "import pandas, telco_churn; print(telco_churn.__file__)"
   ```
4. Generate the inspection report:

   ```powershell
   python -m uv run --locked python -m telco_churn.dataset
   ```

   Result: `reports/data_overview.json`. The reader decodes the supplied file's outer CSV layer in memory before parsing its inner records. It does not modify source bytes, remove records or impute values.

## Project responsibilities

| Location | Responsibility |
|---|---|
| `data/raw/` | Immutable original inputs, excluded from Git |
| `src/telco_churn/dataset.py` | Importable inspection and data-reading code |
| `references/data_source.md` | Input identity, acquisition instructions and field notes |
| `reports/` | Generated JSON reports, excluded from Git |
| `evidence/tp01/` | Small tracked assessment records |
| `pyproject.toml` | Project metadata and dependency requirements |
| `uv.lock` | Resolved dependency versions, tracked in Git |
| `.venv/` | Local installed environment, excluded from Git |

Future TP02 work will put preprocessing and training code in the package, settings in `configs/`, and saved fitted pipelines in `models/`. Notebooks can hold exploration, while reusable terminal workflows belong in package code. These future locations do not need empty placeholder files today.

## Inspection results and recreation

The report records dimensions, inferred field types, target counts/proportions, duplicate IDs (occurrences beyond the first), pandas null counts, separate empty/whitespace counts, source hash, timestamp and environment information.

The recorded input has 7,043 rows and 21 columns. Churn labels are `No`: 5,174 (73.46%) and `Yes`: 1,869 (26.54%). There are no duplicate customer IDs and no pandas null values. `TotalCharges` has 11 whitespace-only values and is read as text. Always predicting `No` would give approximately 73.46% accuracy on this snapshot, but would identify no churners; a future model needs a proper held-out evaluation and suitable metrics.

`evidence/tp01/inspection_before.json` and `inspection_after.json` preserve runs before and after renaming `.venv` to `.venv-before` and recreating it with `python -m uv sync --locked`. All report sections matched except the deliberately excluded execution timestamp. Environment backups are ignored along with the active environment.

This demonstrates local inspection recreation. A lock file does not freeze hardware or establish reproducibility of a future trained model. That will also require versioned training/preprocessing code, configuration, split and randomness details, evaluation evidence, and model artifacts.

## Review and handover

Peer review and execution in a clean directory remain pending. Record actual observations in [the handover note](evidence/tp01/handover.md). Do not treat this local recreation as evidence of independent peer execution.
