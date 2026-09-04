from pathlib import Path

import joblib
import pandas as pd


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "transactions.csv"

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "recovery_model.joblib"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_opportunities.csv"
)


# ---------------------------------------------------------
# Load model and data
# ---------------------------------------------------------

print("Loading recovery model...")

model = joblib.load(MODEL_PATH)

print("Loading transaction data...")

df = pd.read_csv(DATA_PATH)


# ---------------------------------------------------------
# Keep only at-risk transactions
# ---------------------------------------------------------

opportunities = df[
    df["payment_status"].isin(
        ["failed", "abandoned"]
    )
].copy()


# ---------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------

import math

opportunities["amount_log"] = (
    opportunities["amount"] + 1
).apply(math.log)


feature_columns = [
    "amount_log",
    "payment_method",
    "payment_status",
    "failure_reason",
    "previous_transactions",
    "previous_successes",
    "previous_failures",
    "previous_success_rate",
    "retry_count",
    "days_since_failure",
    "checkout_abandoned",
    "customer_lifetime_value",
]


X = opportunities[feature_columns]


# ---------------------------------------------------------
# Predict recovery probability
# ---------------------------------------------------------

print("Calculating recovery probabilities...")

probabilities = model.predict_proba(X)[:, 1]

opportunities["recovery_probability"] = probabilities


# ---------------------------------------------------------
# Expected recovery
# ---------------------------------------------------------

opportunities["expected_recovery"] = (
    opportunities["amount"]
    * opportunities["recovery_probability"]
)


# ---------------------------------------------------------
# Revenue-at-risk
# ---------------------------------------------------------

opportunities["revenue_at_risk"] = (
    opportunities["amount"]
)


# ---------------------------------------------------------
# Priority score
# ---------------------------------------------------------

opportunities["priority_score"] = (
    opportunities["expected_recovery"]
)


# ---------------------------------------------------------
# Sort
# ---------------------------------------------------------

opportunities = opportunities.sort_values(
    by="priority_score",
    ascending=False,
)


# ---------------------------------------------------------
# Add ranking
# ---------------------------------------------------------

opportunities.insert(
    0,
    "priority_rank",
    range(1, len(opportunities) + 1),
)


# ---------------------------------------------------------
# Save
# ---------------------------------------------------------

opportunities.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ---------------------------------------------------------
# Display summary
# ---------------------------------------------------------

print()
print("=" * 60)
print("RECOVERY PRIORITIZATION")
print("=" * 60)

print(
    f"Recovery opportunities: "
    f"{len(opportunities):,}"
)

print(
    "Revenue at risk: "
    f"₹{opportunities['revenue_at_risk'].sum():,.2f}"
)

print(
    "Expected recoverable revenue: "
    f"₹{opportunities['expected_recovery'].sum():,.2f}"
)

print()
print("Top 10 recovery opportunities:")

columns_to_show = [
    "priority_rank",
    "transaction_id",
    "amount",
    "payment_status",
    "failure_reason",
    "recovery_probability",
    "expected_recovery",
    "retry_count",
]

print(
    opportunities[
        columns_to_show
    ]
    .head(10)
    .to_string(index=False)
)

print()
print(
    f"Saved to: {OUTPUT_PATH}"
)