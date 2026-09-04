from razorpay_client import get_client


def create_test_payment_link():
    """
    Create ONE Razorpay Test Mode Payment Link.

    This is a controlled demonstration action.
    """

    client = get_client()

    payment_link_data = {
        "amount": 49900,
        "currency": "INR",
        "accept_partial": False,
        "description": "RecoverAI test recovery",
        "reference_id": "recoverai_demo_001",
        "expire_by": 0,
        "customer": {
            "name": "RecoverAI Demo Customer",
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
            "purpose": "AI revenue recovery demonstration",
        },
    }

    print("Creating Razorpay Test Mode Payment Link...")

    response = client.payment_link.create(
        payment_link_data
    )

    print()
    print("=" * 60)
    print("PAYMENT LINK CREATED")
    print("=" * 60)

    print("ID:", response.get("id"))
    print("Status:", response.get("status"))
    print("Short URL:", response.get("short_url"))
    print(
        "Amount:",
        response.get("amount"),
        response.get("currency"),
    )

    return response


if __name__ == "__main__":
    create_test_payment_link()