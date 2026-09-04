from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .razorpay_client import get_client


PROJECT_ROOT = Path(__file__).resolve().parents[1]

AUDIT_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_execution_audit.csv"
)


def execute_payment_link(row):
    """
    Execute one approved PAYMENT_LINK recovery action
    against Razorpay Test Mode.

    Safety guarantees:
    1. Only PAYMENT_LINK actions reach this function.
    2. Previously successful executions are not duplicated.
    3. Razorpay API failures are recorded as FAILED.
    4. Every execution attempt produces an audit record.
    """

    transaction_id = str(row["transaction_id"]).strip()

    amount_inr = float(row["amount"])
    recovery_probability = float(row["recovery_probability"])
    expected_recovery = float(row["expected_recovery"])

    # -----------------------------------------------------
    # IDEMPOTENCY CHECK
    # -----------------------------------------------------
    # Never create another Payment Link if this transaction
    # already has a successful execution.
    # -----------------------------------------------------

    if AUDIT_PATH.exists():
        try:
            audit_df = pd.read_csv(AUDIT_PATH)

            if not audit_df.empty:
                matching = audit_df[
                    audit_df["transaction_id"]
                    .astype(str)
                    .str.strip()
                    == transaction_id
                ]

                successful = matching[
                    (
                        matching["action"]
                        .astype(str)
                        .str.strip()
                        == "PAYMENT_LINK"
                    )
                    &
                    (
                        matching["execution_status"]
                        .astype(str)
                        .str.strip()
                        .isin(
                            [
                                "CREATED",
                                "ALREADY_EXECUTED",
                            ]
                        )
                    )
                ]

                if not successful.empty:
                    previous = successful.iloc[-1]

                    return {
                        "timestamp": datetime.now(
                            timezone.utc
                        ).isoformat(),

                        "transaction_id": transaction_id,

                        "amount_inr": amount_inr,

                        "recovery_probability":
                            recovery_probability,

                        "expected_recovery":
                            expected_recovery,

                        "action": "PAYMENT_LINK",

                        "policy_approved": True,

                        "execution_status":
                            "ALREADY_EXECUTED",

                        "razorpay_payment_link_id":
                            str(
                                previous.get(
                                    "razorpay_payment_link_id",
                                    ""
                                )
                            ),

                        "short_url":
                            str(
                                previous.get(
                                    "short_url",
                                    ""
                                )
                            ),

                        "error": "",
                    }

        except Exception as exc:
            print(
                f"Warning: could not inspect audit trail: {exc}"
            )

    # -----------------------------------------------------
    # RAZORPAY TEST MODE
    # -----------------------------------------------------

    client = get_client()

    amount_paise = int(
        round(amount_inr * 100)
    )

    payment_link_data = {
        "amount": amount_paise,

        "currency": "INR",

        "accept_partial": False,

        "description": (
            f"RecoverAI recovery for "
            f"{transaction_id}"
        ),

        "reference_id": (
            f"recoverai_{transaction_id}"
        ),

        "customer": {
            "name": "RecoverAI Test Customer",
            "email": "demo@example.com",
            "contact": "9876543210",
        },

        "notify": {
            "sms": False,
            "email": False,
        },

        "reminder_enable": False,

        "notes": {
            "source": "RecoverAI",

            "transaction_id":
                transaction_id,

            "recovery_probability":
                str(recovery_probability),

            "expected_recovery":
                str(expected_recovery),
        },
    }

    created_at = datetime.now(
        timezone.utc
    ).isoformat()

    # -----------------------------------------------------
    # CREATE RAZORPAY PAYMENT LINK
    # -----------------------------------------------------

    try:
        response = client.payment_link.create(
            payment_link_data
        )

        audit_record = {
            "timestamp": created_at,

            "transaction_id":
                transaction_id,

            "amount_inr":
                amount_inr,

            "recovery_probability":
                recovery_probability,

            "expected_recovery":
                expected_recovery,

            "action":
                "PAYMENT_LINK",

            "policy_approved":
                True,

            "execution_status":
                "CREATED",

            "razorpay_payment_link_id":
                response.get("id", ""),

            "short_url":
                response.get("short_url", ""),

            "error":
                "",
        }

    except Exception as exc:

        audit_record = {
            "timestamp": created_at,

            "transaction_id":
                transaction_id,

            "amount_inr":
                amount_inr,

            "recovery_probability":
                recovery_probability,

            "expected_recovery":
                expected_recovery,

            "action":
                "PAYMENT_LINK",

            "policy_approved":
                True,

            "execution_status":
                "FAILED",

            "razorpay_payment_link_id":
                "",

            "short_url":
                "",

            "error":
                str(exc),
        }

    return audit_record


def save_audit_record(record):
    """Append one execution record to the audit CSV."""

    audit_df = pd.DataFrame([record])

    if AUDIT_PATH.exists():

        audit_df.to_csv(
            AUDIT_PATH,
            mode="a",
            header=False,
            index=False,
        )

    else:

        audit_df.to_csv(
            AUDIT_PATH,
            index=False,
        )


def main():

    print(
        "RecoverAI Razorpay execution module ready."
    )

    print(
        f"Audit path: {AUDIT_PATH}"
    )


if __name__ == "__main__":
    main()