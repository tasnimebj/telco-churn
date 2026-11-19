# TP04 input/output contract

The validation boundary is `prepare_features`, followed by the pipeline's predict/predict_proba. All six TP02 columns are required; missing required columns raise ValueError naming the missing feature. Churn and customerID are excluded.

Numeric strings are parsed strictly. Actual missing numeric values are allowed; whitespace-only TotalCharges is treated as missing, but nonblank malformed numeric text must fail. Training medians impute numeric values, then training scaling is reused. Missing categorical values use the training mode. Previously unseen categories are accepted by OneHotEncoder(handle_unknown="ignore"); this does not establish prediction accuracy for those categories.

For a nonempty valid batch, there is one class prediction and one probability row per record. Classes are [0=No, 1=Yes]; positive-class scores must be selected through classes_. All probabilities are finite, bounded by [0,1], and each row sums to one within tolerance 1e-12. The complete pipeline's serialization preserves probabilities within absolute tolerance 1e-12 and class predictions exactly.

Realistic defects protected against: silently missing an input column; rejecting a permitted unknown category or missing charge; producing invalid/misaligned probability outputs; and losing fitted preprocessing during serialization. Additional checks cover label/ID leakage, malformed numeric inputs, and unintended refitting during prediction. Synthetic fixtures contain 16 invented customers and both classes; tests need no full dataset, saved production model or MLflow service.
