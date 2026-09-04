from pathlib import Path

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "transactions.csv"
)


# ============================================================
# FEATURES
# ============================================================

NUMERIC_FEATURES = [
    "amount",
    "previous_transactions",
    "previous_successes",
    "previous_failures",
    "previous_success_rate",
    "retry_count",
    "days_since_failure",
    "checkout_abandoned",
    "customer_lifetime_value",
]

CATEGORICAL_FEATURES = [
    "payment_method",
    "payment_status",
    "failure_reason",
]

TARGET = "recovered"


# ============================================================
# MODEL
# ============================================================

def build_model():

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
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ]
    )

    classifier = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "classifier",
                classifier,
            ),
        ]
    )


# ============================================================
# TRAIN + EVALUATE
# ============================================================

def train_and_evaluate():

    print("Loading RecoverAI transaction dataset...")

    df = pd.read_csv(DATA_PATH)

    print(
        f"Rows loaded: {len(df):,}"
    )

    X = df[
        NUMERIC_FEATURES
        + CATEGORICAL_FEATURES
    ]

    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )

    model = build_model()

    print()
    print("Training recovery prediction model...")

    model.fit(
        X_train,
        y_train,
    )

    probabilities = model.predict_proba(
        X_test
    )[:, 1]

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    metrics = {
        "roc_auc": roc_auc_score(
            y_test,
            probabilities,
        ),
        "accuracy": accuracy_score(
            y_test,
            predictions,
        ),
        "precision": precision_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        "f1": f1_score(
            y_test,
            predictions,
            zero_division=0,
        ),
    }

    print()
    print("=" * 70)
    print("RECOVERAI RECOVERY MODEL EVALUATION")
    print("=" * 70)

    print()
    print(
        f"Training rows: {len(X_train):,}"
    )

    print(
        f"Test rows:     {len(X_test):,}"
    )

    print()

    for name, value in metrics.items():

        print(
            f"{name.upper():10s}: "
            f"{value:.4f}"
        )

    print()
    print("=" * 70)

    return model, metrics


# ============================================================
# PREDICTION HELPER
# ============================================================

def predict_recovery_probability(
    model,
    transaction: dict,
) -> float:

    row = pd.DataFrame(
        [transaction]
    )

    probability = model.predict_proba(
        row
    )[0, 1]

    return float(
        max(
            0.0,
            min(
                1.0,
                probability,
            ),
        )
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    train_and_evaluate()