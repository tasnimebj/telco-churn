# TP05 — GitHub Actions and DevSecOps

## Reproducible CI and actual PR execution

- Pull request: https://github.com/tasnimebj/telco-churn/pull/5
- Workflow: `.github/workflows/ci.yml`, named **Telco CI**.
- Events: `pull_request` targeting the actual default branch `master`, and `push` to `master`.
- Runner: GitHub-hosted `ubuntu-latest` (actual run used Ubuntu 26.04); Python 3.12; uv 0.13.5.
- Installation: `uv sync --locked`, including development tools and the importable src-layout package.
- Quality job: `ruff check src/telco_churn tests`, `ruff format --check src/telco_churn tests`, `pytest -q`.
- Successful repaired run: https://github.com/tasnimebj/telco-churn/actions/runs/44508766257

The repaired run collected and passed **12 tests** using synthetic fixtures, without CSV, model-training execution or a running MLflow instance. Ruff lint and formatting both passed. `format --check` reports nonconforming formatting without rewriting files on the runner. Local pre-commit is useful early feedback but cannot establish what was actually pushed, and can be bypassed. These remote checks run independently on the PR commit. Requiring them to block merges is a separate repository policy; no branch-protection setting was changed.

The workflow has only `contents: read`, explicit timeouts, no repository secrets, no write token and no `pull_request_target`. Checkout disables persisted credentials. Official actions are pinned to immutable commit references resolved from real releases:

| Action | Reviewed release | Pinned commit |
|---|---|---|
| actions/checkout | v7.0.1 | `3d3c42e5aac5ba805825da76410c181273ba90b1` |
| astral-sh/setup-uv | v10.3.3 | `68559e99cc807c1eb7e9238fd43a15bba460eec2` |

## Real regression: red to green

Failed run: https://github.com/tasnimebj/telco-churn/actions/runs/44508625038 (commit `78cc10c`). Changing the encoder from `handle_unknown="ignore"` to `handle_unknown="error"` was syntactically valid and format-compliant: both Ruff steps passed, but the actual `test_supported_missing_numeric_and_unseen_category` failed with a ValueError for an unseen contract (11 passed, 1 failed). Restoring the documented permissive policy in commit `4aaa49c` produced the successful run above, with 12 passing tests and both security jobs passing. Final code remains repaired; no artificial assertion or YAML failure was used.

Actual retained step logs: [failed run](../evidence/tp05/actions_44508625038.txt), [repaired run](../evidence/tp05/actions_44508766257.txt). API-exported job/step conclusions are in [actions_results.json](../evidence/tp05/actions_results.json).

## Python dependency audit

Tool: pip-audit 2.10.1, added to the project development dependencies and lockfile. Both local and GitHub scans ran inside the installed locked project environment, including development tools. Local scan reported **no known vulnerabilities** for auditable entries; the report contains 127 installed entries and explicitly skips `telco-churn` 0.1.0 because this local package is not on PyPI. The Actions audit also finished successfully with **No known vulnerabilities found**, rather than a connection/setup error.

Machine-readable local result: [pip_audit.json](../evidence/tp05/pip_audit.json). There is no advisory finding to remediate in these recorded runs. This does not prove the code is secure or cover OS packages and all platform-specific branches of the lockfile. Re-audit on updates as advisory data evolves. For a future finding, record package/version/advisory/fixed version, make a compatible intentional update, review the lock diff and rerun tests and audit. If no compatible fix exists, document the finding and next action without suppressing the failing exit status.

## Gitleaks and safe synthetic detection

The separate secret job scans a clean checkout before creating environments or artifacts: `gitleaks dir --redact --exit-code 1 .`. Default rules are retained, and all matches are redacted. Official Gitleaks **8.30.1** is pinned. The matching Linux x64 archive SHA-256 was verified against the official pinned release checksum list and embedded in the workflow; CI uses `sha256sum --check --strict`. The locally used Windows x64 archive was likewise checked before executing. See [gitleaks_release.json](../evidence/tp05/gitleaks_release.json).

Actual Actions result: **no leaks found**, job succeeded. Local checkout-equivalent tracked-file snapshot result: **no leaks found**. This scans the current directory snapshot, not Git history or arbitrary files elsewhere on the laptop.

For the demonstration, a system temporary directory outside the project held an invented marker and a rule extending default rules (`useDefault = true`). The first scan exited 1 and reported rule `tp05-demo-marker`, with the match redacted. After removing the invented file, the second scan exited 0 and reported no leaks. The fixture and rule were never staged or committed; only [redacted detection/cleanup evidence](../evidence/tp05/synthetic_scan.txt) is retained.

Deleting a genuinely exposed credential from the current snapshot is insufficient: revoke or rotate it, investigate its scope/use and prior commits, and coordinate any history remediation. No real credential was introduced for the exercise.

## Dependabot review procedure

`.github/dependabot.yml` requests weekly version updates for **uv** at `/` and **github-actions** at `/`, with a modest open-PR limit. Version updates become effective after the configuration reaches the default branch; the submitted exercise PR contains it. A bot PR is not required and none is claimed. Version-update scheduling is separate from security alerts and security updates, which depend on repository settings and ecosystem support.

A concrete review example is Ruff 0.17.5 in this lockfile: read the proposed version's release notes, inspect manifest/lock changes, check rule/formatter compatibility, and keep `.pre-commit-config.yaml` aligned with the CLI version. For an action update, verify the official release and its exact new SHA. Require review of all three CI jobs before deciding to merge; do not blindly auto-merge or add privileged tokens.

## Handover and limits

README lists the local reproduction commands. Tests and scans address different risks and passing them does not prove model utility, fairness, calibration or freedom from unknown vulnerabilities. The demonstration and implementation were AI-assisted; no independent human review is claimed. No paid security product, cloud VM, SonarQube integration, container scan or deployment was added. Branch rules, Actions policy and repository visibility were not changed. The final exercise branch is fixed; merge the PR to activate default-branch version updates.
