# TP04 — Testing and Code Quality

## Input/output contract and test-to-risk mapping

The boundary is `prepare_features`, then the fitted pipeline. Six TP02 inputs are mandatory; target and ID are excluded. Numeric parsing is strict, blank TotalCharges becomes missing, numeric nulls are imputed from training medians, and unknown categorical values are accepted without refitting. Positive class is 1=Yes, negative class is 0=No; output columns are interpreted using `classes_`. See `references/tp04_contract.md`.

| Test | Realistic defect detected |
|---|---|
| Missing required feature (six parameterized cases) | A removed column silently reaching prediction or an uninformative boundary error |
| Supported missing numeric input and unseen category | A change from documented imputation/ignore policy to an accidental inference crash |
| Probability contract | Wrong batch/class shape, NaN/inf, invalid probabilities, row normalization errors or wrong positive-class mapping |
| Joblib persistence using tmp_path | Saving an incomplete or altered prediction object that cannot reproduce fitted-pipeline behavior |
| Whitespace versus malformed charge | Silently converting invalid nonblank charges into allowed missing values |
| Target/ID exclusion | Accidentally including identification or the answer as model inputs |
| Prediction preserves learned statistics | Fitting preprocessing again on inference data |

There are **12 passing cases** using 16 invented customers and both target classes, with the actual pipeline builder and a fixed-seed logistic classifier. No raw CSV, training service, network request or production artifact is used. No exact accuracy/AUC is asserted on the tiny fixture. Serialization loads only the test's own trusted temporary file.

## Genuine regression and repair

Temporarily changing `OneHotEncoder(handle_unknown="ignore")` to `handle_unknown="error"` made `test_supported_missing_numeric_and_unseen_category` fail with a ValueError reporting an unknown category. The category is verified absent from both fixture inputs and fitted encoder categories. The original implementation was restored in a finally block; all 12 tests then passed. No test expectations were weakened and no `assert False` was introduced.

- Failure traceback: [regression_failure.txt](../evidence/tp04/regression_failure.txt).
- Passing repair: [regression_repaired.txt](../evidence/tp04/regression_repaired.txt).

## Ruff and formatting

Scope: all `src/telco_churn` and `tests`, including TP02 and TP03 modules. Ruff 0.17.5 uses E4, E7, E9, F and I; formatting is separate. The initial run found four fixable findings: three import-order issues and one unused NumPy import. These fixes and formatter changes were reviewed; no package exclusion or blanket ignore was introduced. Final lint and formatter checks passed on all 14 Python files, and tests passed again.

Initial findings: [ruff_initial.txt](../evidence/tp04/ruff_initial.txt). Final results: [quality_final.txt](../evidence/tp04/quality_final.txt).

## Coverage observation

Actual package-wide statement coverage: **8% (34 of 421 statements executed)**. The focused preprocessing module `pipeline.py` has **92% (33 of 36 statements)**. Full training, artifact orchestration, data loading and MLflow entry points are included in the denominator, but deliberately not executed by these unit tests. Earlier integration evidence is separate and does not increase this run's coverage.

One relevant uncovered behavior is rejection of infinite numeric inputs in `prepare_features` (line 30 in the formatted module). A useful follow-up is a parameterized test passing positive/negative infinity in each numeric feature and asserting ValueError with the feature name. Other uncovered branches reject blank tenure/MonthlyCharges and non-string categories. There is no arbitrary coverage threshold and no claim of complete verification.

Coverage log: [coverage.txt](../evidence/tp04/coverage.txt). The generated `coverage.xml` remains local and ignored. Executing a line proves it was reached, not that an assertion checked the right behavior. Third-party sklearn/pandas internals are outside this package coverage scope.

## Pre-commit demonstration

`.pre-commit-config.yaml` uses the real `astral-sh/ruff-pre-commit` release tag `v0.17.5`, matching the locked CLI version. Lint with fixes runs first, formatter second. Paths are limited to package, scripts and tests, without virtual environments or tracking storage. Config validation, hook installation and all-files execution succeeded.

In the tracked production pipeline, `result = records[FEATURES].copy()` was temporarily written as `result=records[FEATURES].copy()`. This was formatting-only, with unchanged intended behavior. The staged commit was rejected because ruff-format modified the file. HEAD was verified unchanged. Formatter output was verified against the intended source, staged again, and the retry succeeded as commit `81917eb`. Hooks were not bypassed.

- Actual rejected attempt: [blocked_commit.txt](../evidence/tp04/blocked_commit.txt).
- Actual successful retry: [successful_commit.txt](../evidence/tp04/successful_commit.txt).
- Final all-files check: [precommit_final.txt](../evidence/tp04/precommit_final.txt).

Each clone must install its own hook; committing configuration does not install hooks for other users. Tests are run separately, not by hooks. Local hooks do not replace CI or required-check repository policies.

## Quality Gate reflection and limits

Behavioral tests check chosen input/output expectations; static analysis finds selected code patterns without proving model behavior; formatting normalizes presentation. Coverage measures executed application statements and identifies gaps, without proving assertion quality. A Quality Gate is a policy over analysis results, with thresholds and a definition of new code; analysis finishing successfully is distinct from the gate passing. Configuring a gate to fail CI is also distinct from configuring a required check to block a merge.

SonarQube imports pytest-generated coverage (for example via `sonar.python.coverage.reportPaths=coverage.xml`); it does not produce it by running pytest itself. SonarQube Community Build installation and screenshots are optional and were not performed. No Sonar score, issue count or gate result is claimed. A GitHub-hosted runner cannot reach this laptop's localhost server; no server was exposed. TP05 can run Ruff and pytest in CI, with security checks added separately.

Passing tests/gates does not establish generalization, calibration, fairness, security or business usefulness. Unknown-category acceptance does not establish accuracy on shifted inputs. These checks and evidence were implemented and executed with AI assistance, not independently reviewed by a human peer. The model comparison, dataset allocation and reserved test policy were not changed by TP04.
