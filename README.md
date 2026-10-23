# Telco Churn — TP01

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
