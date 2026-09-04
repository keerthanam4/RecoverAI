from pathlib import Path

import pandas as pd


def main():
    dataset_path = Path(__file__).resolve().parent / "transactions.csv"

    print("Loading RecoverAI transaction dataset...")
    df = pd.read_csv(dataset_path)

    print()
    print("=" * 60)
    print("DATASET OVERVIEW")
    print("=" * 60)

    print(f"Rows: {len(df):,}")
    print(f"Columns: {len(df.columns)}")

    print()
    print("Column names:")
    for column in df.columns:
        print(f" - {column}")

    print()
    print("=" * 60)
    print("MISSING VALUES")
    print("=" * 60)

    missing_values = df.isnull().sum()

    if missing_values.sum() == 0:
        print("✓ No missing values found.")
    else:
        print(missing_values[missing_values > 0])

    print()
    print("=" * 60)
    print("DUPLICATE TRANSACTIONS")
    print("=" * 60)

    duplicate_ids = df["transaction_id"].duplicated().sum()

    print(f"Duplicate transaction IDs: {duplicate_ids}")

    print()
    print("=" * 60)
    print("PAYMENT STATUS")
    print("=" * 60)

    print(df["payment_status"].value_counts())

    print()
    print("=" * 60)
    print("PAYMENT STATUS — PERCENTAGE")
    print("=" * 60)

    status_percentages = (
        df["payment_status"]
        .value_counts(normalize=True)
        .mul(100)
        .round(2)
    )

    print(status_percentages)

    print()
    print("=" * 60)
    print("FAILURE REASONS")
    print("=" * 60)

    print(df["failure_reason"].value_counts())

    print()
    print("=" * 60)
    print("RECOVERY DISTRIBUTION")
    print("=" * 60)

    print(df["recovered"].value_counts())

    print()
    print("=" * 60)
    print("REVENUE ANALYSIS")
    print("=" * 60)

    total_value = df["amount"].sum()

    failed_value = df.loc[
        df["payment_status"] == "failed",
        "amount",
    ].sum()

    abandoned_value = df.loc[
        df["payment_status"] == "abandoned",
        "amount",
    ].sum()

    recovered_value = df.loc[
        df["recovered"] == 1,
        "amount",
    ].sum()

    print(f"Total transaction value: ₹{total_value:,.2f}")
    print(f"Failed payment value:    ₹{failed_value:,.2f}")
    print(f"Abandoned checkout value: ₹{abandoned_value:,.2f}")
    print(f"Recovered value:          ₹{recovered_value:,.2f}")

    revenue_at_risk = failed_value + abandoned_value

    print()
    print(f"Revenue currently at risk: ₹{revenue_at_risk:,.2f}")

    print()
    print("=" * 60)
    print("NUMERIC RANGE CHECKS")
    print("=" * 60)

    print(f"Minimum transaction amount: ₹{df['amount'].min():,.2f}")
    print(f"Maximum transaction amount: ₹{df['amount'].max():,.2f}")

    print(
        f"Minimum previous success rate: "
        f"{df['previous_success_rate'].min():.4f}"
    )

    print(
        f"Maximum previous success rate: "
        f"{df['previous_success_rate'].max():.4f}"
    )

    print(
        f"Minimum retry count: "
        f"{df['retry_count'].min()}"
    )

    print(
        f"Maximum retry count: "
        f"{df['retry_count'].max()}"
    )

    print()
    print("=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()