from pathlib import Path

import pandas as pd

from recovery_executor import (
    execute_payment_link,
    save_audit_record,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DECISIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_decisions.csv"
)


def main():

    print("Loading RecoverAI decisions...")

    df = pd.read_csv(DECISIONS_PATH)

    # -----------------------------------------------------
    # Only use decisions where RecoverAI chose PAYMENT_LINK
    # and the policy approved the action.
    # -----------------------------------------------------

    eligible = df[
        (df["recommended_action"] == "PAYMENT_LINK")
        & (df["policy_approved"] == True)
    ].copy()

    if eligible.empty:
        raise RuntimeError(
            "No approved PAYMENT_LINK recovery "
            "opportunity was found."
        )

    # -----------------------------------------------------
    # Select the highest expected-recovery opportunity.
    # -----------------------------------------------------

    eligible = eligible.sort_values(
        by="expected_recovery",
        ascending=False,
    )

    row = eligible.iloc[0]

    print()
    print("=" * 70)
    print("SELECTED RECOVERAI RECOVERY")
    print("=" * 70)

    print(
        f"Transaction ID: "
        f"{row['transaction_id']}"
    )

    print(
        f"Amount: "
        f"₹{row['amount']:,.2f}"
    )

    print(
        f"Payment status: "
        f"{row['payment_status']}"
    )

    print(
        f"Failure reason: "
        f"{row['failure_reason']}"
    )

    print(
        f"Recovery probability: "
        f"{row['recovery_probability']:.4f}"
    )

    print(
        f"Expected recovery: "
        f"₹{row['expected_recovery']:,.2f}"
    )

    print(
        f"Recommended action: "
        f"{row['recommended_action']}"
    )

    print(
        f"Policy approved: "
        f"{row['policy_approved']}"
    )

    print()
    print(
        "Executing ONE Razorpay Test Mode "
        "Payment Link..."
    )

    # -----------------------------------------------------
    # Execute the real Test Mode action.
    # -----------------------------------------------------

    audit_record = execute_payment_link(row)

    save_audit_record(audit_record)

    print()
    print("=" * 70)
    print("EXECUTION RESULT")
    print("=" * 70)

    print(
        f"Status: "
        f"{audit_record['execution_status']}"
    )

    print(
        f"Razorpay Payment Link ID: "
        f"{audit_record['razorpay_payment_link_id']}"
    )

    print(
        f"Short URL: "
        f"{audit_record['short_url']}"
    )

    if audit_record["error"]:

        print(
            f"Error: "
            f"{audit_record['error']}"
        )

    print()
    print(
        "Audit record saved successfully."
    )


if __name__ == "__main__":
    main()