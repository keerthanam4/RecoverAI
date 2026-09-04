from dataclasses import asdict

from policy_engine import evaluate_policy


class RecoveryAgent:
    """
    RecoverAI decision-making agent.

    The agent diagnoses the transaction and recommends
    an intervention. The policy engine is the final
    safety gate before execution.
    """

    def diagnose(
        self,
        payment_status: str,
        failure_reason: str,
        recovery_probability: float,
        retry_count: int,
        amount: float,
    ) -> str:

        if payment_status == "abandoned":
            return (
                "Checkout was abandoned before payment "
                "completion. A payment-link based recovery "
                "flow is more appropriate than an automatic "
                "payment retry."
            )

        if retry_count >= 2:
            return (
                "The transaction has already received "
                "multiple recovery attempts. Further "
                "automatic retries could create unnecessary "
                "customer friction."
            )

        if failure_reason == "network_error":
            return (
                "The failure appears potentially temporary. "
                "A controlled retry may be appropriate if "
                "the recovery probability is sufficiently high."
            )

        if failure_reason == "technical_error":
            return (
                "A technical payment failure was detected. "
                "A controlled retry may recover the payment "
                "without requiring aggressive intervention."
            )

        if failure_reason == "bank_decline":
            return (
                "The payment was declined by the bank. "
                "Repeated automatic retries may not be "
                "appropriate, so a softer recovery path "
                "or escalation should be considered."
            )

        if failure_reason == "insufficient_funds":
            return (
                "The payment appears to have failed because "
                "of insufficient funds. A reminder or alternate "
                "payment path is preferable to repeated retries."
            )

        if failure_reason == "authentication_failed":
            return (
                "Authentication failed during payment. "
                "The customer may need to retry through an "
                "appropriate authenticated payment flow."
            )

        return (
            "The transaction requires a conservative recovery "
            "intervention based on its available payment context."
        )

    def decide(
        self,
        amount: float,
        recovery_probability: float,
        retry_count: int,
        payment_status: str,
        failure_reason: str,
    ):

        diagnosis = self.diagnose(
            payment_status=payment_status,
            failure_reason=failure_reason,
            recovery_probability=recovery_probability,
            retry_count=retry_count,
            amount=amount,
        )

        policy_decision = evaluate_policy(
            amount=amount,
            recovery_probability=recovery_probability,
            retry_count=retry_count,
            payment_status=payment_status,
            failure_reason=failure_reason,
        )

        return {
            "diagnosis": diagnosis,
            "decision": asdict(policy_decision),
        }


def main():

    agent = RecoveryAgent()

    examples = [
        {
            "name": "Technical failure",
            "amount": 4_999,
            "recovery_probability": 0.82,
            "retry_count": 0,
            "payment_status": "failed",
            "failure_reason": "technical_error",
        },
        {
            "name": "Abandoned checkout",
            "amount": 3_000,
            "recovery_probability": 0.55,
            "retry_count": 0,
            "payment_status": "abandoned",
            "failure_reason": "none",
        },
        {
            "name": "High-value transaction",
            "amount": 20_000,
            "recovery_probability": 0.85,
            "retry_count": 0,
            "payment_status": "failed",
            "failure_reason": "technical_error",
        },
        {
            "name": "Repeated failure",
            "amount": 4_000,
            "recovery_probability": 0.80,
            "retry_count": 2,
            "payment_status": "failed",
            "failure_reason": "bank_decline",
        },
    ]

    for example in examples:

        name = example.pop("name")

        result = agent.decide(**example)

        print()
        print("=" * 70)
        print(name)
        print("=" * 70)

        print()
        print("Diagnosis:")
        print(result["diagnosis"])

        print()
        print("Decision:")
        print(result["decision"])


if __name__ == "__main__":
    main()