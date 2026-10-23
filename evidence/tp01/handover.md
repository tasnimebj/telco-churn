# Individual validation and handover status

- Author: tasnimebj
- Environment recreation date: 2026-10-23
- Repository: https://github.com/tasnimebj/telco-churn
- Working arrangement: individual work.
- Independent reviewer: none; independent review and peer execution remain pending.
- Pull request URL: https://github.com/tasnimebj/telco-churn/pull/2 (provided by the author).
- Repository pull request listing: https://github.com/tasnimebj/telco-churn/pulls (listing link, not an individual PR).

## Completed local environment recreation

The original inspection report was preserved as `inspection_before.json`. The existing `.venv` was renamed to `.venv-before`, then the environment was recreated from the existing lock file:

```powershell
python -m uv sync --locked
python -m uv run --locked python -m telco_churn.dataset
```

The second report was preserved as `inspection_after.json`. Comparison confirmed matching source identity/hash, environment information, dimensions, field types, target counts and proportions, duplicate customer-ID count, null counts, and empty/whitespace counts. The execution timestamp was deliberately excluded from comparison.

Both reports contain 7,043 rows and 21 columns. They record 11 whitespace-only values in `TotalCharges`. The original CSV was not modified.

## Implementation issue resolved

The inspection module was initially saved at the project root, causing `No module named telco_churn.dataset`. Saving the code at `src/telco_churn/dataset.py` resolved the import problem, and inspection subsequently ran successfully. This was an author-observed issue, not peer feedback.

## Fresh-clone self-validation

- Status: successful self-validation in the separate `telco-churn-selfcheck` checkout, as confirmed by terminal output.
- Branch: `docs/project-onboarding`.
- Data acquisition: copied the supplied CSV separately from `../dataset/datasets.csv` to `data/raw/datasets.csv`.
- Hash verification: SHA-256 matched `62ca518b1ebbcd4c832c18c1a21629b03abe9033fef66fe2e38d8d030658a20c`.
- Environment check: `python -m uv sync --locked` succeeded. At this invocation uv checked six existing packages; this output does not demonstrate another new environment recreation.
- Import check: importing pandas and `telco_churn` succeeded; the package path pointed to `telco-churn-selfcheck/src/telco_churn/__init__.py`.
- Inspection: `python -m uv run --locked python -m telco_churn.dataset` saved `reports/data_overview.json` and reported 7,043 rows and 21 columns.
- Issue observed: repeating `git clone` failed because `telco-churn-selfcheck` already existed and was not empty.
- Resolution and retry: used the existing separate checkout, confirmed the branch, and completed the commands successfully. No files were deleted. This was a repeated setup attempt, not an independently observed README defect.

## Review and remaining limits

- Suggested review question: Can a new user obtain and verify the exact supplied CSV and generate the report by following only the README?
- Independent review feedback and author response: pending.
- The original provider/download of the supplied CSV still needs confirmation in `references/data_source.md`.

Completed evidence demonstrates local environment recreation, consistent before/after inspection results, and successful execution in a separate checkout. The latter was self-validation using an already existing clone, not independent peer execution. Independent handover remains pending; self-validation does not replace the assignment's independent review requirement unless the instructor accepts an alternative.
