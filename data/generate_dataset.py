import random
from pathlib import Path

import numpy as np
import pandas as pd


# Make the generated dataset reproducible.
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

NUM_TRANSACTIONS = 10_000

PAYMENT_METHODS = [
    "upi",
    "card",
    "netbanking",
    "wallet",
]

FAILURE_REASONS = [
    "insufficient_funds",
    "bank_decline",
    "network_error",
    "authentication_failed",
    "technical_error",
]


def generate_customer_profiles(num_customers: int = 2_500):
    """Generate reusable customer profiles."""

    customers = []

    for i in range(1, num_customers + 1):
        previous_transactions = random.randint(1, 40)

        # Give each customer a different historical success rate.
        historical_success_rate = np.clip(
            np.random.beta(8, 2),
            0.15,
            0.99,
        )

        previous_successes = int(
            round(previous_transactions * historical_success_rate)
        )

        previous_failures = (
            previous_transactions - previous_successes
        )

        customer_lifetime_value = round(
            random.uniform(1_000, 150_000),
            2,
        )

        customers.append(
            {
                "customer_id": f"cust_{i:05d}",
                "previous_transactions": previous_transactions,
                "previous_successes": previous_successes,
                "previous_failures": previous_failures,
                "customer_lifetime_value": customer_lifetime_value,
            }
        )

    return customers


def choose_payment_status():
    """Choose whether the transaction succeeded, failed, or was abandoned."""

    value = random.random()

    if value < 0.70:
        return "success"
    elif value < 0.92:
        return "failed"
    else:
        return "abandoned"


def calculate_recovery_probability(
    amount,
    payment_status,
    failure_reason,
    previous_success_rate,
    retry_count,
    days_since_failure,
    checkout_abandoned,
):
    """
    Generate a realistic synthetic probability of eventual recovery.

    This is used only to generate synthetic outcomes.
    It is NOT our final ML model.
    """

    probability = 0.50

    # Customer history
    probability += (previous_success_rate - 0.50) * 0.45

    # Payment amount
    if amount <= 2_000:
        probability += 0.08
    elif amount >= 20_000:
        probability -= 0.08

    # Failure reason
    if failure_reason == "network_error":
        probability += 0.12
    elif failure_reason == "technical_error":
        probability += 0.08
    elif failure_reason == "insufficient_funds":
        probability -= 0.03
    elif failure_reason == "bank_decline":
        probability -= 0.10
    elif failure_reason == "authentication_failed":
        probability -= 0.08

    # Repeated recovery attempts reduce the probability.
    probability -= retry_count * 0.12

    # Older failures are harder to recover.
    probability -= min(days_since_failure / 30, 0.30)

    # Abandoned checkouts still have recovery potential.
    if checkout_abandoned:
        probability += 0.05

    # Successful payments are already recovered.
    if payment_status == "success":
        probability = 1.0

    return float(np.clip(probability, 0.02, 0.98))


def main():
    print("Generating RecoverAI synthetic transaction dataset...")

    customers = generate_customer_profiles()

    customer_lookup = {
        customer["customer_id"]: customer
        for customer in customers
    }

    customer_ids = list(customer_lookup.keys())

    records = []

    for i in range(1, NUM_TRANSACTIONS + 1):
        customer_id = random.choice(customer_ids)
        customer = customer_lookup[customer_id]

        amount = round(
            np.clip(
                np.random.lognormal(mean=7.2, sigma=1.0),
                100,
                100_000,
            ),
            2,
        )

        payment_method = random.choice(PAYMENT_METHODS)
        payment_status = choose_payment_status()

        if payment_status == "failed":
            failure_reason = random.choice(FAILURE_REASONS)
            retry_count = random.randint(0, 3)
            days_since_failure = round(
                random.uniform(0.1, 14),
                2,
            )
        elif payment_status == "abandoned":
            failure_reason = "none"
            retry_count = 0
            days_since_failure = round(
                random.uniform(0.1, 7),
                2,
            )
        else:
            failure_reason = "none"
            retry_count = 0
            days_since_failure = 0.0

        checkout_abandoned = int(
            payment_status == "abandoned"
        )

        previous_success_rate = round(
            customer["previous_successes"]
            / customer["previous_transactions"],
            4,
        )

        recovery_probability = calculate_recovery_probability(
            amount=amount,
            payment_status=payment_status,
            failure_reason=failure_reason,
            previous_success_rate=previous_success_rate,
            retry_count=retry_count,
            days_since_failure=days_since_failure,
            checkout_abandoned=checkout_abandoned,
        )

        recovered = int(
            random.random() < recovery_probability
        )

        # Successful transactions are already recovered.
        if payment_status == "success":
            recovered = 1

        records.append(
            {
                "transaction_id": f"txn_{i:06d}",
                "customer_id": customer_id,
                "amount": amount,
                "payment_method": payment_method,
                "payment_status": payment_status,
                "failure_reason": failure_reason,
                "previous_transactions": customer[
                    "previous_transactions"
                ],
                "previous_successes": customer[
                    "previous_successes"
                ],
                "previous_failures": customer[
                    "previous_failures"
                ],
                "previous_success_rate": previous_success_rate,
                "retry_count": retry_count,
                "days_since_failure": days_since_failure,
                "checkout_abandoned": checkout_abandoned,
                "customer_lifetime_value": customer[
                    "customer_lifetime_value"
                ],
                "recovered": recovered,
            }
        )

    df = pd.DataFrame(records)

    output_path = Path(__file__).resolve().parent / "transactions.csv"

    df.to_csv(output_path, index=False)

    print()
    print("Dataset generation complete.")
    print(f"Rows generated: {len(df):,}")
    print(f"Columns generated: {len(df.columns)}")
    print(f"Saved to: {output_path}")
    print()

    print("Payment status distribution:")
    print(df["payment_status"].value_counts())

    print()
    print("Total transaction value:")
    print(f"₹{df['amount'].sum():,.2f}")

    print()
    print("Recovered transaction value:")
    print(
        f"₹{df.loc[df['recovered'] == 1, 'amount'].sum():,.2f}"
    )


if __name__ == "__main__":
    main()