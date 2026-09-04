from pathlib import Path

import joblib
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = PROJECT_ROOT / "data" / "transactions.csv"

MODEL_DIR = PROJECT_ROOT / "ml" / "models"

MODEL_PATH = MODEL_DIR / "recovery_model.joblib"


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

RANDOM_STATE = 42


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

print("Loading transaction dataset...")

df = pd.read_csv(DATA_PATH)

print(f"Total records loaded: {len(df):,}")


# ---------------------------------------------------------
# Select only revenue-recovery opportunities
# ---------------------------------------------------------
#
# Successful transactions are excluded because they are
# already successful. The recovery agent is concerned with
# failed payments and abandoned checkouts.
# ---------------------------------------------------------

recovery_df = df[
    df["payment_status"].isin(
        ["failed", "abandoned"]
    )
].copy()

print(
    f"Revenue-recovery opportunities: "
    f"{len(recovery_df):,}"
)


# ---------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------

recovery_df["amount_log"] = (
    recovery_df["amount"] + 1
).apply(lambda x: __import__("math").log(x))


# ---------------------------------------------------------
# Features
# ---------------------------------------------------------

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


X = recovery_df[feature_columns]

y = recovery_df["recovered"]


# ---------------------------------------------------------
# Train / test split
# ---------------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=RANDOM_STATE,
    stratify=y,
)

print(f"Training records: {len(X_train):,}")
print(f"Test records:     {len(X_test):,}")


# ---------------------------------------------------------
# Feature types
# ---------------------------------------------------------

categorical_features = [
    "payment_method",
    "payment_status",
    "failure_reason",
]

numeric_features = [
    "amount_log",
    "previous_transactions",
    "previous_successes",
    "previous_failures",
    "previous_success_rate",
    "retry_count",
    "days_since_failure",
    "checkout_abandoned",
    "customer_lifetime_value",
]


# ---------------------------------------------------------
# Preprocessing
# ---------------------------------------------------------

numeric_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median"),
        ),
        (
            "scaler",
            StandardScaler(),
        ),
    ]
)


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent"),
        ),
        (
            "encoder",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
        ),
    ]
)


preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_pipeline,
            numeric_features,
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features,
        ),
    ]
)


# ---------------------------------------------------------
# Model
# ---------------------------------------------------------

model = LogisticRegression(
    max_iter=1000,
    random_state=RANDOM_STATE,
)


pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor,
        ),
        (
            "model",
            model,
        ),
    ]
)


# ---------------------------------------------------------
# Train
# ---------------------------------------------------------

print()
print("Training recovery prediction model...")

pipeline.fit(X_train, y_train)

print("Training complete.")


# ---------------------------------------------------------
# Predictions
# ---------------------------------------------------------

y_probability = pipeline.predict_proba(
    X_test
)[:, 1]

y_pred = (
    y_probability >= 0.50
).astype(int)


# ---------------------------------------------------------
# Evaluation
# ---------------------------------------------------------

precision = precision_score(
    y_test,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_test,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_test,
    y_pred,
    zero_division=0,
)

roc_auc = roc_auc_score(
    y_test,
    y_probability,
)


print()
print("=" * 60)
print("MODEL EVALUATION")
print("=" * 60)

print(f"Precision : {precision:.4f}")
print(f"Recall    : {recall:.4f}")
print(f"F1 Score  : {f1:.4f}")
print(f"ROC-AUC   : {roc_auc:.4f}")


print()
print("Confusion Matrix:")
print(
    confusion_matrix(
        y_test,
        y_pred,
    )
)


print()
print("Classification Report:")
print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0,
    )
)


# ---------------------------------------------------------
# Calculate expected recoverable revenue
# ---------------------------------------------------------

test_results = X_test.copy()

test_results["actual_recovered"] = y_test.values

test_results["recovery_probability"] = y_probability

test_results["expected_recovery"] = (
    recovery_df.loc[
        X_test.index,
        "amount",
    ].values
    * y_probability
)


print()
print("=" * 60)
print("EXPECTED RECOVERY")
print("=" * 60)

total_expected_recovery = (
    test_results["expected_recovery"].sum()
)

print(
    "Expected recoverable revenue in test batch: "
    f"₹{total_expected_recovery:,.2f}"
)


# ---------------------------------------------------------
# Save model
# ---------------------------------------------------------

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

joblib.dump(
    pipeline,
    MODEL_PATH,
)

print()
print("=" * 60)
print("MODEL SAVED")
print("=" * 60)

print(f"Model path: {MODEL_PATH}")