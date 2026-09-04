from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

TRANSACTIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "transactions.csv"
)

OPPORTUNITIES_PATH = (
    PROJECT_ROOT
    / "data"
    / "recovery_opportunities.csv"
)

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


def money(value):
    return f"₹{value:,.2f}"


def percentage(value):
    return f"{value:.2f}%"


def main():

    print("Loading RecoverAI evaluation data...")

    transactions = pd.read_csv(
        TRANSACTIONS_PATH
    )

    opportunities = pd.read_csv(
        OPPORTUNITIES_PATH
    )

    decisions = pd.read_csv(
        DECISIONS_PATH
    )

    audit = pd.read_csv(
        AUDIT_PATH
    )

    # -----------------------------------------------------
    # DATASET METRICS
    # -----------------------------------------------------

    total_transactions = len(
        transactions
    )

    recovery_opportunities = len(
        opportunities
    )

    # -----------------------------------------------------
    # GROUND-TRUTH RECOVERY
    # -----------------------------------------------------

    recovered_opportunities = opportunities[
        opportunities["recovered"] == True
    ]

    recovered_transaction_count = len(
        recovered_opportunities
    )

    actual_recovered_revenue = (
        recovered_opportunities["amount"].sum()
    )

    opportunity_recovery_rate = (
        recovered_transaction_count
        / recovery_opportunities
        * 100
    )

    # -----------------------------------------------------
    # REVENUE IMPACT
    # -----------------------------------------------------

    revenue_at_risk = (
        opportunities["revenue_at_risk"].sum()
    )

    expected_recovery = (
        opportunities["expected_recovery"].sum()
    )

    actual_recovery_percentage = (
        actual_recovered_revenue
        / revenue_at_risk
        * 100
    )

    expected_recovery_percentage = (
        expected_recovery
        / revenue_at_risk
        * 100
    )

    # -----------------------------------------------------
    # EXPECTED VS HISTORICAL RECOVERY
    # -----------------------------------------------------

    if expected_recovery > 0:

        recovery_estimate_alignment = (
            actual_recovered_revenue
            / expected_recovery
            * 100
        )

    else:

        recovery_estimate_alignment = 0

    recovery_estimate_error = abs(
        actual_recovered_revenue
        - expected_recovery
    )

    # -----------------------------------------------------
    # ACTION DISTRIBUTION
    # -----------------------------------------------------

    action_counts = (
        decisions["recommended_action"]
        .value_counts()
    )

    stop_count = action_counts.get(
        "STOP",
        0,
    )

    payment_link_count = action_counts.get(
        "PAYMENT_LINK",
        0,
    )

    retry_count = action_counts.get(
        "RETRY",
        0,
    )

    reminder_count = action_counts.get(
        "REMINDER",
        0,
    )

    escalation_count = action_counts.get(
        "ESCALATE",
        0,
    )

    # -----------------------------------------------------
    # AUTOMATION
    # -----------------------------------------------------

    automated_actions = (
        retry_count
        + payment_link_count
        + reminder_count
    )

    automated_percentage = (
        automated_actions
        / recovery_opportunities
        * 100
    )

    escalation_percentage = (
        escalation_count
        / recovery_opportunities
        * 100
    )

    stop_percentage = (
        stop_count
        / recovery_opportunities
        * 100
    )

    # -----------------------------------------------------
    # MODEL PROBABILITY SEPARATION
    # -----------------------------------------------------

    model_data = decisions.merge(
        transactions[
            [
                "transaction_id",
                "recovered",
            ]
        ],
        on="transaction_id",
        how="left",
    )

    recovered_probability = (
        model_data.loc[
            model_data["recovered"] == True,
            "recovery_probability",
        ].mean()
    )

    not_recovered_probability = (
        model_data.loc[
            model_data["recovered"] == False,
            "recovery_probability",
        ].mean()
    )

    probability_separation = (
        recovered_probability
        - not_recovered_probability
    )

    # -----------------------------------------------------
    # RECOVERY BY ACTION
    # -----------------------------------------------------

    action_outcomes = (
        model_data
        .groupby("recommended_action")
        .agg(
            transactions=(
                "transaction_id",
                "count",
            ),
            recovered=(
                "recovered",
                "sum",
            ),
            recovery_rate=(
                "recovered",
                "mean",
            ),
            amount=(
                "amount",
                "sum",
            ),
        )
    )

    # -----------------------------------------------------
    # RAZORPAY TEST MODE
    # -----------------------------------------------------

    successful_test_executions = len(
        audit[
            audit["execution_status"]
            == "CREATED"
        ]
    )

    failed_test_executions = len(
        audit[
            audit["execution_status"]
            == "FAILED"
        ]
    )

    already_executed_count = len(
        audit[
            audit["execution_status"]
            == "ALREADY_EXECUTED"
        ]
    )

    test_execution_amount = audit[
        audit["execution_status"]
        == "CREATED"
    ]["amount_inr"].sum()

    # -----------------------------------------------------
    # REPORT
    # -----------------------------------------------------

    print()
    print("=" * 70)
    print("RECOVERAI BATCH EVALUATION REPORT")
    print("=" * 70)

    # -----------------------------------------------------
    # DATASET
    # -----------------------------------------------------

    print()
    print("DATASET")
    print("-" * 70)

    print(
        f"Total transactions: "
        f"{total_transactions:,}"
    )

    print(
        f"Recovery opportunities: "
        f"{recovery_opportunities:,}"
    )

    # -----------------------------------------------------
    # REVENUE
    # -----------------------------------------------------

    print()
    print("REVENUE IMPACT")
    print("-" * 70)

    print(
        f"Revenue at risk: "
        f"{money(revenue_at_risk)}"
    )

    print(
        f"Expected recovery: "
        f"{money(expected_recovery)}"
    )

    print(
        f"Historical recovered revenue: "
        f"{money(actual_recovered_revenue)}"
    )

    print(
        f"Recovery opportunity rate: "
        f"{percentage(opportunity_recovery_rate)}"
    )

    print(
        f"Historical recovery / revenue at risk: "
        f"{percentage(actual_recovery_percentage)}"
    )

    print(
        f"Expected recovery / revenue at risk: "
        f"{percentage(expected_recovery_percentage)}"
    )

    print()
    print(
        "EXPECTED VS HISTORICAL"
    )
    print("-" * 70)

    print(
        f"Expected recovery: "
        f"{money(expected_recovery)}"
    )

    print(
        f"Historical recovery: "
        f"{money(actual_recovered_revenue)}"
    )

    print(
        f"Estimate alignment: "
        f"{percentage(recovery_estimate_alignment)}"
    )

    print(
        f"Absolute estimate difference: "
        f"{money(recovery_estimate_error)}"
    )

    # -----------------------------------------------------
    # RECOVERY STRATEGY
    # -----------------------------------------------------

    print()
    print("RECOVERY STRATEGY")
    print("-" * 70)

    print(
        f"STOP: "
        f"{stop_count:,} "
        f"({stop_percentage:.2f}%)"
    )

    print(
        f"PAYMENT_LINK: "
        f"{payment_link_count:,}"
    )

    print(
        f"RETRY: "
        f"{retry_count:,}"
    )

    print(
        f"REMINDER: "
        f"{reminder_count:,}"
    )

    print(
        f"ESCALATE: "
        f"{escalation_count:,} "
        f"({escalation_percentage:.2f}%)"
    )

    # -----------------------------------------------------
    # STRATEGY OUTCOMES
    # -----------------------------------------------------

    print()
    print("HISTORICAL OUTCOMES BY AI ACTION")
    print("-" * 70)

    for action in [
        "RETRY",
        "PAYMENT_LINK",
        "REMINDER",
        "ESCALATE",
        "STOP",
    ]:

        if action not in action_outcomes.index:
            continue

        row = action_outcomes.loc[action]

        print(
            f"{action:<15} "
            f"{int(row['transactions']):>5} transactions | "
            f"{int(row['recovered']):>5} recovered | "
            f"{row['recovery_rate'] * 100:>6.2f}%"
        )

    # -----------------------------------------------------
    # AUTOMATION
    # -----------------------------------------------------

    print()
    print("AUTOMATION")
    print("-" * 70)

    print(
        f"Automated interventions: "
        f"{automated_actions:,}"
    )

    print(
        f"Automation-eligible rate: "
        f"{automated_percentage:.2f}%"
    )

    print(
        f"Human escalations: "
        f"{escalation_count:,}"
    )

    print(
        f"Stop decisions: "
        f"{stop_count:,}"
    )

    # -----------------------------------------------------
    # MODEL QUALITY
    # -----------------------------------------------------

    print()
    print("MODEL SIGNAL QUALITY")
    print("-" * 70)

    print(
        f"Average recovery probability "
        f"(recovered): "
        f"{recovered_probability:.4f}"
    )

    print(
        f"Average recovery probability "
        f"(not recovered): "
        f"{not_recovered_probability:.4f}"
    )

    print(
        f"Probability separation: "
        f"{probability_separation:.4f}"
    )

    # -----------------------------------------------------
    # RAZORPAY TEST MODE
    # -----------------------------------------------------

    print()
    print("RAZORPAY TEST MODE EXECUTION")
    print("-" * 70)

    print(
        f"Audit events recorded: "
        f"{len(audit):,}"
    )

    print(
        f"Successful executions: "
        f"{successful_test_executions:,}"
    )

    print(
        f"Already executed: "
        f"{already_executed_count:,}"
    )

    print(
        f"Failed executions: "
        f"{failed_test_executions:,}"
    )

    print(
        f"Test transaction value: "
        f"{money(test_execution_amount)}"
    )

    print()
    print("=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()