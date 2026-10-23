# Data source and identity

- Local input: `data/raw/datasets.csv`.
- Original workspace copy: `../dataset/datasets.csv`, relative to the project root.
- SHA-256: `62ca518b1ebbcd4c832c18c1a21629b03abe9033fef66fe2e38d8d030658a20c`.
- Acquisition provenance: confirmation of the original provider/download remains pending.
- To reproduce this run, obtain the exact supplied `datasets.csv` from the project author through the agreed course sharing channel, place it at the local input path and verify the hash. The CSV is intentionally excluded from Git.

The assignment identifies the dataset family as IBM Telco Customer Churn and lists https://github.com/IBM/telco-customer-churn-on-icp4d as background. This local file wraps each comma-separated record in an outer quoted CSV field. We have not established byte identity with the upstream CSV. Do not substitute a download and assume it has this hash or encoding structure.

The reader decodes that outer layer in memory. The original input remains unchanged. Matching hashes prove matching bytes, not business accuracy.

## Field roles

- `customerID`: customer identifier; exclude from ordinary model inputs later.
- `Churn`: target (`Yes`/`No`); including it as an input would leak the answer.
- `tenure`, `MonthlyCharges`, `TotalCharges`: potential numeric inputs; `TotalCharges` currently contains 11 whitespace-only entries and is inferred as text.
- `Contract`, `InternetService`, `PaymentMethod`: examples of categorical inputs.

This is a customer snapshot, not a dated event history or randomized retention experiment. TP01 does not clean or transform records for training.
