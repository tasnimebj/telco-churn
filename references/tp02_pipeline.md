# TP02 milestone 2: input and preprocessing policy

Run from the project root after milestone 1:

```powershell
python -m uv run --locked python -m telco_churn.pipeline_demo
```

`prepare_features` is a stateless boundary function shared by training and future inference. Supply a DataFrame with tenure, MonthlyCharges, TotalCharges, Contract, InternetService and PaymentMethod. Extra columns are excluded; missing required columns fail visibly. Do not pass customerID or Churn as model features.

Numeric fields accept numeric values or numeric strings and actual missing values. Whitespace-only TotalCharges becomes missing. Other blank numeric text, malformed nonblank numeric text and infinite values raise errors. The CSV stays unchanged. Categorical inputs must be strings or missing values; surrounding whitespace is stripped and blank strings become missing.

After boundary parsing, the pipeline takes the six original unencoded columns: numeric columns are floats with NaN permitted; categorical columns contain strings or NaN. Numeric imputation uses training medians followed by StandardScaler. Categorical imputation uses the training mode followed by dense one-hot encoding. Unknown categories produce an all-zero block for that feature; this avoids a schema error but provides no reliability guarantee for unseen categories.

Only the training partition is passed to fit. Validation uses predict, reusing fitted statistics. Customer allocations are checked against first_model.json. Test metrics are not computed. This milestone checks that learned imputation values match training medians and remain unchanged by prediction.

The two-feature and six-feature results are different feature settings, so their difference cannot be attributed solely to an algorithm improvement. Fair comparison of three learned classifiers and a baseline is the next milestone.
