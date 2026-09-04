import sys
from pathlib import Path

import pytest

# Allow imports from the agent directory when running pytest
AGENT_DIR = Path(__file__).resolve().parent

if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))

from policy_engine import evaluate_policy


@pytest.mark.parametrize(
    "case",
    [
        {
            "name": "Strong recovery candidate",
            "amount": 4_999,
            "recovery_probability": 0.84,
            "retry_count": 0,
            "payment_status": "failed",
            "failure_reason": "technical_error",
            "expected_action": "RETRY",
            "expected_human": False,
        },
        {
            "name": "High-value transaction",
            "amount": 20_000,
            "recovery_probability": 0.85,
            "retry_count": 0,
            "payment_status": "failed",
            "failure_reason": "technical_error",
            "expected_action": "RETRY",
            "expected_human": False,
        },
        {
            "name": "Retry limit reached",
            "amount": 4_000,
            "recovery_probability": 0.80,
            "retry_count": 2,
            "payment_status": "failed",
            "failure_reason": "technical_error",
            "expected_action": "ESCALATE",
            "expected_human": True,
        },
        {
            "name": "Low recovery probability",
            "amount": 2_000,
            "recovery_probability": 0.10,
            "retry_count": 0,
            "payment_status": "failed",
            "failure_reason": "bank_decline",
            "expected_action": "STOP",
            "expected_human": False,
        },
        {
            "name": "Abandoned checkout",
            "amount": 3_000,
            "recovery_probability": 0.55,
            "retry_count": 0,
            "payment_status": "abandoned",
            "failure_reason": "none",
            "expected_action": "PAYMENT_LINK",
            "expected_human": False,
        },
    ],
)
def test_recovery_policy(case):
    """Verify that the policy engine returns the expected safe action."""

    decision = evaluate_policy(
        amount=case["amount"],
        recovery_probability=case["recovery_probability"],
        retry_count=case["retry_count"],
        payment_status=case["payment_status"],
        failure_reason=case["failure_reason"],
    )

    assert decision.approved is True
    assert decision.action == case["expected_action"]
    assert decision.requires_human is case["expected_human"]


def test_retry_limit_is_enforced():
    """Automated retries must stop after the configured retry limit."""

    decision = evaluate_policy(
        amount=4_000,
        recovery_probability=0.95,
        retry_count=2,
        payment_status="failed",
        failure_reason="technical_error",
    )

    assert decision.action == "ESCALATE"
    assert decision.requires_human is True


def test_low_probability_stops_recovery():
    """Very low recovery probability must not trigger payment attempts."""

    decision = evaluate_policy(
        amount=5_000,
        recovery_probability=0.05,
        retry_count=0,
        payment_status="failed",
        failure_reason="bank_decline",
    )

    assert decision.action == "STOP"
    assert decision.requires_human is False


def test_abandoned_checkout_uses_payment_link():
    """Abandoned checkout should use a customer-controlled payment link."""

    decision = evaluate_policy(
        amount=3_000,
        recovery_probability=0.55,
        retry_count=0,
        payment_status="abandoned",
        failure_reason="none",
    )

    assert decision.action == "PAYMENT_LINK"
    assert decision.requires_human is False