from pathlib import Path

import pandas as pd

from recovery_agent import RecoveryAgent


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

INPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_opportunities.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_decisions.csv"
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

MAX_BATCH_SIZE = 2_990


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("Loading recovery opportunities...")

    df = pd.read_csv(INPUT_PATH)

    print(
        f"Recovery opportunities loaded: "
        f"{len(df):,}"
    )

    # Safety check
    df = df.head(MAX_BATCH_SIZE).copy()

    agent = RecoveryAgent()

    results = []

    print()
    print("Running RecoverAI recovery agent...")
    print()

    for index, row in df.iterrows():

        result = agent.decide(
            amount=float(row["amount"]),
            recovery_probability=float(
                row["recovery_probability"]
            ),
            retry_count=int(row["retry_count"]),
            payment_status=row["payment_status"],
            failure_reason=row["failure_reason"],
        )

        decision = result["decision"]

        # -------------------------------------------------
        # Execution simulation
        # -------------------------------------------------
        #
        # We are NOT calling real payment APIs yet.
        #
        # This stage simulates the controlled execution
        # layer so we can test the complete decision flow.
        #

        if decision["approved"]:

            if decision["action"] in [
                "RETRY",
                "PAYMENT_LINK",
                "REMINDER",
            ]:
                execution_status = "SIMULATED_EXECUTION"

            elif decision["action"] == "ESCALATE":
                execution_status = "ESCALATED"

            elif decision["action"] == "STOP":
                execution_status = "STOPPED"

            else:
                execution_status = "NOT_EXECUTED"

        else:
            execution_status = "BLOCKED"

        # -------------------------------------------------
        # Store result
        # -------------------------------------------------

        results.append(
            {
                "transaction_id": row[
                    "transaction_id"
                ],
                "amount": row["amount"],
                "payment_status": row[
                    "payment_status"
                ],
                "failure_reason": row[
                    "failure_reason"
                ],
                "retry_count": row[
                    "retry_count"
                ],
                "recovery_probability": row[
                    "recovery_probability"
                ],
                "expected_recovery": row[
                    "expected_recovery"
                ],
                "diagnosis": result[
                    "diagnosis"
                ],
                "recommended_action": decision[
                    "action"
                ],
                "policy_approved": decision[
                    "approved"
                ],
                "policy_reason": decision[
                    "reason"
                ],
                "requires_human": decision[
                    "requires_human"
                ],
                "execution_status": execution_status,
            }
        )

    results_df = pd.DataFrame(results)

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    results_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    # -----------------------------------------------------
    # Summary
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("RECOVERY AGENT BATCH RESULTS")
    print("=" * 70)

    print()
    print(
        f"Transactions processed: "
        f"{len(results_df):,}"
    )

    print()
    print("Recommended actions:")

    print(
        results_df[
            "recommended_action"
        ].value_counts()
    )

    print()
    print("Execution status:")

    print(
        results_df[
            "execution_status"
        ].value_counts()
    )

    print()
    print("Revenue at risk:")

    print(
        f"₹{results_df['amount'].sum():,.2f}"
    )

    print()
    print("Expected recoverable revenue:")

    print(
        f"₹{results_df['expected_recovery'].sum():,.2f}"
    )

    print()
    print(
        "Human escalations:"
    )

    print(
        results_df[
            "requires_human"
        ].sum()
    )

    print()
    print(
        f"Saved to: {OUTPUT_PATH}"
    )


if __name__ == "__main__":
    main()