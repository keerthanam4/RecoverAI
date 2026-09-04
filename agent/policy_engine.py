from dataclasses import dataclass


@dataclass
class RecoveryDecision:
    action: str
    approved: bool
    reason: str
    requires_human: bool


# ---------------------------------------------------------
# Policy thresholds
# ---------------------------------------------------------

HIGH_VALUE_THRESHOLD = 10_000

MAX_AUTOMATED_RETRIES = 2

MIN_RECOVERY_PROBABILITY = 0.20

HIGH_RECOVERY_PROBABILITY = 0.70

# High-value transactions require stronger confidence
# before automated recovery is allowed.
HIGH_VALUE_AUTOMATION_PROBABILITY = 0.60


def evaluate_policy(
    amount: float,
    recovery_probability: float,
    retry_count: int,
    payment_status: str,
    failure_reason: str,
):
    """
    Apply deterministic safety and business rules
    before any recovery action is executed.

    The recovery model estimates likelihood.
    This policy engine decides whether that estimate
    is safe enough to translate into an action.
    """

    # Normalize inputs defensively.
    amount = float(amount)
    recovery_probability = float(recovery_probability)
    retry_count = int(retry_count)
    payment_status = str(payment_status).lower()
    failure_reason = str(failure_reason).lower()

    # -----------------------------------------------------
    # Rule 1: Low recovery probability
    # -----------------------------------------------------

    if recovery_probability < MIN_RECOVERY_PROBABILITY:

        return RecoveryDecision(
            action="STOP",
            approved=True,
            reason=(
                "Recovery probability is below the "
                "minimum intervention threshold."
            ),
            requires_human=False,
        )

    # -----------------------------------------------------
    # Rule 2: Retry limit
    # -----------------------------------------------------

    if retry_count >= MAX_AUTOMATED_RETRIES:

        return RecoveryDecision(
            action="ESCALATE",
            approved=True,
            reason=(
                "Maximum automated retry limit reached. "
                "Further automated retries are blocked."
            ),
            requires_human=True,
        )

    # -----------------------------------------------------
    # Rule 3: High-value risk control
    # -----------------------------------------------------
    #
    # High-value transactions are NOT automatically escalated.
    #
    # They can be automated when confidence is sufficiently
    # strong and the recovery mechanism is appropriate.
    #
    # Otherwise a human reviews the opportunity.
    # -----------------------------------------------------

    is_high_value = amount >= HIGH_VALUE_THRESHOLD

    if is_high_value:

        if recovery_probability < HIGH_VALUE_AUTOMATION_PROBABILITY:

            return RecoveryDecision(
                action="ESCALATE",
                approved=True,
                reason=(
                    "High-value transaction with insufficient "
                    "confidence for automated recovery. "
                    "Human review is required."
                ),
                requires_human=True,
            )

    # -----------------------------------------------------
    # Rule 4: Abandoned checkout
    # -----------------------------------------------------
    #
    # An abandoned checkout should use a payment link rather
    # than an automatic payment retry.
    # -----------------------------------------------------

    if payment_status == "abandoned":

        return RecoveryDecision(
            action="PAYMENT_LINK",
            approved=True,
            reason=(
                "Checkout was abandoned. A payment link "
                "provides a customer-controlled recovery "
                "path without automatically retrying payment."
            ),
            requires_human=False,
        )

    # -----------------------------------------------------
    # Rule 5: Strong recovery probability
    # -----------------------------------------------------

    if recovery_probability >= HIGH_RECOVERY_PROBABILITY:

        return RecoveryDecision(
            action="RETRY",
            approved=True,
            reason=(
                "High recovery probability and retry limit "
                "has not been reached."
            ),
            requires_human=False,
        )

    # -----------------------------------------------------
    # Rule 6: Network / technical failure
    # -----------------------------------------------------

    if failure_reason in [
        "network_error",
        "technical_error",
    ]:

        return RecoveryDecision(
            action="RETRY",
            approved=True,
            reason=(
                "Failure appears temporary or technical "
                "and recovery probability is sufficient "
                "for a controlled retry."
            ),
            requires_human=False,
        )

    # -----------------------------------------------------
    # Rule 7: Moderate recovery probability
    # -----------------------------------------------------

    return RecoveryDecision(
        action="REMINDER",
        approved=True,
        reason=(
            "Recovery probability is moderate. "
            "Use a non-invasive reminder instead of "
            "an automatic payment attempt."
        ),
        requires_human=False,
    )