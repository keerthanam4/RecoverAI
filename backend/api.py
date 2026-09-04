from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_decisions.csv"
)

AUDIT_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_execution_audit.csv"
)
TRANSACTIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "transactions.csv"
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="RecoverAI API",
    description="AI Revenue Recovery backend for Razorpay Buildathon",
    version="1.0.0",
)


# ============================================================
# CORS
# Allows the React frontend running on localhost:5173
# to communicate with this backend.
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_decisions():
    """Load RecoverAI recovery decisions."""

    if not DECISIONS_PATH.exists():
        raise FileNotFoundError(
            f"Recovery decisions file not found: "
            f"{DECISIONS_PATH}"
        )

    return pd.read_csv(DECISIONS_PATH)


def load_audit():
    """Load Razorpay execution audit."""

    if not AUDIT_PATH.exists():
        return pd.DataFrame()

    return pd.read_csv(AUDIT_PATH)


def clean_value(value):
    """Convert pandas/numpy values into JSON-safe values."""

    if pd.isna(value):
        return None

    if hasattr(value, "item"):
        return value.item()

    return value


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/")
def root():
    return {
        "service": "RecoverAI API",
        "status": "running",
        "version": "1.0.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "decisions_file": DECISIONS_PATH.exists(),
        "audit_file": AUDIT_PATH.exists(),
    }


# ============================================================
# SUMMARY
# ============================================================

@app.get("/api/summary")
def summary():

    decisions = load_decisions()
    audit = load_audit()
    transactions = pd.read_csv(TRANSACTIONS_PATH)

    recovery_opportunities = len(decisions)

    revenue_at_risk = float(
        decisions["amount"].sum()
    )

    expected_recovery = float(
        decisions["expected_recovery"].sum()
    )

    action_counts = (
        decisions["recommended_action"]
        .value_counts()
        .to_dict()
    )

    stop_count = int(
        action_counts.get("STOP", 0)
    )

    payment_link_count = int(
        action_counts.get("PAYMENT_LINK", 0)
    )

    retry_count = int(
        action_counts.get("RETRY", 0)
    )

    reminder_count = int(
        action_counts.get("REMINDER", 0)
    )

    escalation_count = int(
        action_counts.get("ESCALATE", 0)
    )

    automated_actions = (
        retry_count
        + payment_link_count
        + reminder_count
    )

    automation_rate = (
        automated_actions
        / recovery_opportunities
        * 100
        if recovery_opportunities
        else 0
    )

    successful_executions = 0
    failed_executions = 0
    test_transaction_value = 0.0

    if not audit.empty:

        successful_executions = int(
            (
                audit["execution_status"]
                == "CREATED"
            ).sum()
        )

        failed_executions = int(
            (
                audit["execution_status"]
                == "FAILED"
            ).sum()
        )

        if "amount_inr" in audit.columns:

            test_transaction_value = float(
                audit[
                    audit["execution_status"]
                    == "CREATED"
                ]["amount_inr"].sum()
            )

    return {
        "total_transactions": 10000,
        "recovery_opportunities": recovery_opportunities,
        "revenue_at_risk": revenue_at_risk,
        "expected_recovery": expected_recovery,
        "stop_count": stop_count,
        "payment_link_count": payment_link_count,
        "retry_count": retry_count,
        "reminder_count": reminder_count,
        "escalation_count": escalation_count,
        "automated_actions": automated_actions,
        "automation_rate": round(
            automation_rate,
            2,
        ),
        "human_escalations": escalation_count,
        "test_interventions": len(audit),
        "successful_executions": successful_executions,
        "failed_executions": failed_executions,
        "test_transaction_value": test_transaction_value,
    }


# ============================================================
# ACTION DISTRIBUTION
# ============================================================

@app.get("/api/actions")
def actions():

    decisions = load_decisions()

    counts = (
        decisions["recommended_action"]
        .value_counts()
        .to_dict()
    )

    return {
        "actions": [
            {
                "name": "STOP",
                "value": int(
                    counts.get("STOP", 0)
                ),
            },
            {
                "name": "PAYMENT LINK",
                "value": int(
                    counts.get(
                        "PAYMENT_LINK",
                        0,
                    )
                ),
            },
            {
                "name": "RETRY",
                "value": int(
                    counts.get("RETRY", 0)
                ),
            },
            {
                "name": "REMINDER",
                "value": int(
                    counts.get("REMINDER", 0)
                ),
            },
            {
                "name": "ESCALATE",
                "value": int(
                    counts.get("ESCALATE", 0)
                ),
            },
        ]
    }


# ============================================================
# TOP RECOVERY OPPORTUNITIES
# ============================================================
@app.get("/api/opportunities")
def opportunities(limit: int = 10):

    decisions = load_decisions()

    # Rank opportunities by expected recoverable revenue.
    top = (
        decisions
        .copy()
        .sort_values(
            "expected_recovery",
            ascending=False,
        )
        .head(limit)
        .reset_index(drop=True)
    )

    records = []

    for index, row in top.iterrows():

        records.append(
            {
                "priority_rank": index + 1,

                "transaction_id": clean_value(
                    row["transaction_id"]
                ),

                "payment_status": clean_value(
                    row["payment_status"]
                ),

                "failure_reason": clean_value(
                    row["failure_reason"]
                ),

                "amount": clean_value(
                    row["amount"]
                ),

                "recovery_probability": clean_value(
                    row["recovery_probability"]
                ),

                "expected_recovery": clean_value(
                    row["expected_recovery"]
                ),

                "recommended_action": clean_value(
                    row["recommended_action"]
                ),

                "retry_count": clean_value(
                    row["retry_count"]
                ),

                "policy_approved": clean_value(
                    row["policy_approved"]
                ),

                "requires_human": clean_value(
                    row["requires_human"]
                ),
            }
        )

    return {
        "opportunities": records
    }
# ============================================================
# EXECUTION AUDIT
# ============================================================

@app.get("/api/executions")
def executions():

    audit = load_audit()

    if audit.empty:
        return {
            "executions": []
        }

    audit = audit.copy()

    # --------------------------------------------------------
    # Convert timestamps so execution records can be ordered.
    # --------------------------------------------------------

    audit["_timestamp"] = pd.to_datetime(
        audit["timestamp"],
        errors="coerce"
    )

    audit = audit.sort_values(
        "_timestamp"
    )

    # --------------------------------------------------------
    # Select the best current state for each transaction.
    #
    # Priority:
    # CREATED          -> actual Razorpay execution
    # ALREADY_EXECUTED  -> idempotent reuse of existing link
    # FAILED            -> only shown if no successful state exists
    # --------------------------------------------------------

    priority = {
        "FAILED": 1,
        "ALREADY_EXECUTED": 2,
        "CREATED": 3,
    }

    audit["_priority"] = (
        audit["execution_status"]
        .astype(str)
        .map(priority)
        .fillna(0)
    )

    audit = audit.sort_values(
        ["transaction_id", "_priority", "_timestamp"]
    )

    # Keep the highest-priority/latest state for each transaction.
    latest = (
        audit
        .drop_duplicates(
            subset=["transaction_id"],
            keep="last"
        )
        .copy()
    )

    records = []

    for _, row in latest.iterrows():

        records.append(
            {
                "timestamp": clean_value(
                    row.get("timestamp")
                ),

                "transaction_id": clean_value(
                    row.get("transaction_id")
                ),

                "amount_inr": clean_value(
                    row.get("amount_inr")
                ),

                "recovery_probability": clean_value(
                    row.get("recovery_probability")
                ),

                "expected_recovery": clean_value(
                    row.get("expected_recovery")
                ),

                "action": clean_value(
                    row.get("action")
                ),

                "policy_approved": clean_value(
                    row.get("policy_approved")
                ),

                "execution_status": clean_value(
                    row.get("execution_status")
                ),

                "razorpay_payment_link_id": clean_value(
                    row.get(
                        "razorpay_payment_link_id"
                    )
                ),

                "short_url": clean_value(
                    row.get("short_url")
                ),

                "error": clean_value(
                    row.get("error")
                ),
            }
        )

    return {
        "executions": records
    }
# ============================================================
# SINGLE RECOVERY OPPORTUNITY
# ============================================================

@app.get("/api/recovery/{transaction_id}")
def recovery_detail(transaction_id: str):

    decisions = load_decisions()

    matches = decisions[
        decisions["transaction_id"].astype(str)
        == str(transaction_id)
    ]

    if matches.empty:
        return {
            "found": False,
            "transaction_id": transaction_id,
        }

    row = matches.iloc[0]

    return {
        "found": True,
        "transaction": {
            "transaction_id": clean_value(
                row["transaction_id"]
            ),

            "amount": clean_value(
                row["amount"]
            ),

            "payment_status": clean_value(
                row["payment_status"]
            ),

            "failure_reason": clean_value(
                row["failure_reason"]
            ),

            "retry_count": clean_value(
                row["retry_count"]
            ),

            "recovery_probability": clean_value(
                row["recovery_probability"]
            ),

            "expected_recovery": clean_value(
                row["expected_recovery"]
            ),

            "diagnosis": clean_value(
                row["diagnosis"]
            ),

            "recommended_action": clean_value(
                row["recommended_action"]
            ),

            "policy_approved": clean_value(
                row["policy_approved"]
            ),

            "requires_human": clean_value(
                row["requires_human"]
            ),

            "priority_score": clean_value(
    row["expected_recovery"]
),
            "policy_reason": clean_value(
                row["policy_reason"]
            ),

            "risk_level": (
                "HIGH"
                if float(row["recovery_probability"]) < 0.40
                else (
                    "MEDIUM"
                    if float(row["recovery_probability"]) < 0.70
                    else "LOW"
                )
            ),

            "decision_summary": (
                "Human review required for a high-value "
                "transaction with limited recovery confidence."
                if (
                    row["recommended_action"] == "ESCALATE"
                    and float(row["amount"]) >= 10000
                )
                else (
                    "Customer-controlled payment recovery "
                    "recommended for the abandoned checkout."
                    if row["recommended_action"] == "PAYMENT_LINK"
                    else (
                        "Controlled retry recommended because "
                        "the failure appears potentially recoverable."
                        if row["recommended_action"] == "RETRY"
                        else (
                            "Non-invasive customer reminder recommended."
                            if row["recommended_action"] == "REMINDER"
                            else (
                                "Recovery intervention stopped because "
                                "expected recovery confidence is too low."
                                if row["recommended_action"] == "STOP"
                                else "Human review required."
                            )
                        )
                    )
                )
            ),

            "execution_status": clean_value(
                row["execution_status"]
            ),
        },
    }
# ============================================================
# EXECUTE ONE APPROVED PAYMENT LINK RECOVERY
# ============================================================

@app.post("/api/recovery/{transaction_id}/execute")
def execute_recovery(transaction_id: str):

    decisions = load_decisions()

    matches = decisions[
        decisions["transaction_id"].astype(str)
        == str(transaction_id)
    ]

    if matches.empty:
        return {
            "success": False,
            "transaction_id": transaction_id,
            "status": "NOT_FOUND",
            "message": "Transaction was not found.",
        }

    row = matches.iloc[0]

    recommended_action = str(
        row["recommended_action"]
    ).strip()

    policy_approved = bool(
        row["policy_approved"]
    )

    requires_human = bool(
        row["requires_human"]
    )

    # --------------------------------------------------------
    # POLICY GATE
    # --------------------------------------------------------

    if recommended_action != "PAYMENT_LINK":
        return {
            "success": False,
            "transaction_id": transaction_id,
            "status": "BLOCKED",
            "message": (
                "Execution blocked: recommended action "
                f"is {recommended_action}, not PAYMENT_LINK."
            ),
        }

    if not policy_approved:
        return {
            "success": False,
            "transaction_id": transaction_id,
            "status": "BLOCKED",
            "message": (
                "Execution blocked by the policy engine."
            ),
        }

    if requires_human:
        return {
            "success": False,
            "transaction_id": transaction_id,
            "status": "HUMAN_REVIEW_REQUIRED",
            "message": (
                "Execution blocked because human review "
                "is required."
            ),
        }

    # --------------------------------------------------------
    # RAZORPAY TEST MODE EXECUTION
    # --------------------------------------------------------

    from backend.recovery_executor import (
        execute_payment_link,
        save_audit_record,
    )

    try:

        record = execute_payment_link(row)

        save_audit_record(record)

        # ----------------------------------------------------
        # UPDATE RECOVERY DECISION STATUS
        # ----------------------------------------------------

        if record["execution_status"] in (
            "CREATED",
            "ALREADY_EXECUTED",
        ):

            decisions.loc[
                decisions["transaction_id"].astype(str)
                == str(transaction_id),
                "execution_status",
            ] = "EXECUTED"

            decisions.to_csv(
                PROJECT_ROOT
                / "data"
                / "recovery_decisions.csv",
                index=False,
            )

        return {
            "success": record["execution_status"] in (
                "CREATED",
                "ALREADY_EXECUTED",
            ),
            "transaction_id": transaction_id,
            "status": record["execution_status"],
            "razorpay_payment_link_id": record.get(
                "razorpay_payment_link_id"
            ),
            "short_url": record.get(
                "short_url"
            ),
            "amount_inr": record.get(
                "amount_inr"
            ),
            "error": record.get(
                "error"
            ),
        }

    except Exception as exc:

        return {
            "success": False,
            "transaction_id": transaction_id,
            "status": "FAILED",
            "message": str(exc),
        }

@app.get("/api/evaluation")
def evaluation_summary():

    transactions = pd.read_csv(
        PROJECT_ROOT / "data" / "transactions.csv"
    )

    opportunities = pd.read_csv(
        PROJECT_ROOT / "data" / "recovery_opportunities.csv"
    )

    decisions = pd.read_csv(
        PROJECT_ROOT / "data" / "recovery_decisions.csv"
    )

    recovered = opportunities[
        opportunities["recovered"] == True
    ]

    total_transactions = len(transactions)
    recovery_opportunities = len(opportunities)
    recovered_transactions = len(recovered)

    revenue_at_risk = float(
        opportunities["revenue_at_risk"].sum()
    )

    expected_recovery = float(
        opportunities["expected_recovery"].sum()
    )

    historical_recovery = float(
        recovered["amount"].sum()
    )

    recovery_rate = (
    recovered_transactions
    / recovery_opportunities
    * 100
    if recovery_opportunities > 0
    else 0
)

    expected_recovery_rate = (
        expected_recovery
        / revenue_at_risk
        * 100
        if revenue_at_risk > 0
        else 0
    )
    historical_recovery_rate = (
        historical_recovery
        / revenue_at_risk
        * 100
        if revenue_at_risk > 0
        else 0
    )

    estimate_alignment = (
        historical_recovery
        / expected_recovery
        * 100
        if expected_recovery > 0
        else 0
    )

    merged = decisions.merge(
        transactions[
            [
                "transaction_id",
                "recovered",
            ]
        ],
        on="transaction_id",
        how="left",
    )

    recovered_probability = float(
        merged.loc[
            merged["recovered"] == True,
            "recovery_probability",
        ].mean()
    )

    not_recovered_probability = float(
        merged.loc[
            merged["recovered"] == False,
            "recovery_probability",
        ].mean()
    )

    probability_separation = (
        recovered_probability
        - not_recovered_probability
    )

    action_counts = (
        decisions["recommended_action"]
        .value_counts()
    )
    action_data = decisions.merge(
        transactions[
            [
                "transaction_id",
                "recovered",
            ]
        ],
        on="transaction_id",
        how="left",
    )

    strategy_performance = {}

    for action in [
        "RETRY",
        "PAYMENT_LINK",
        "REMINDER",
        "ESCALATE",
        "STOP",
    ]:

        action_rows = action_data[
            action_data["recommended_action"]
            == action
        ]

        count = len(action_rows)

        recovered_count = int(
            action_rows["recovered"].sum()
        )

        strategy_recovery_rate = (
    recovered_count / count * 100
    if count > 0
    else 0
)

        strategy_performance[action] = {
            "transactions": count,
            "recovered": recovered_count,
            "recovery_rate": strategy_recovery_rate,
        }

    return {
        "total_transactions": total_transactions,

        "recovery_opportunities":
            recovery_opportunities,

        "recovered_transactions":
            recovered_transactions,

        "revenue_at_risk":
            revenue_at_risk,

        "expected_recovery":
            expected_recovery,

        "historical_recovery":
            historical_recovery,

        "recovery_rate":
            recovery_rate,

        "expected_recovery_rate":
            expected_recovery_rate,

        "historical_recovery_rate":
            historical_recovery_rate,

        "estimate_alignment":
            estimate_alignment,

        "recovered_probability":
            recovered_probability,

        "not_recovered_probability":
            not_recovered_probability,

        "probability_separation":
            probability_separation,

                "strategy_counts": {
            "STOP": int(
                action_counts.get("STOP", 0)
            ),

            "PAYMENT_LINK": int(
                action_counts.get(
                    "PAYMENT_LINK",
                    0,
                )
            ),

            "RETRY": int(
                action_counts.get(
                    "RETRY",
                    0,
                )
            ),

            "REMINDER": int(
                action_counts.get(
                    "REMINDER",
                    0,
                )
            ),

            "ESCALATE": int(
                action_counts.get(
                    "ESCALATE",
                    0,
                )
            ),
        },

        "strategy_performance":
            strategy_performance,
    }
    