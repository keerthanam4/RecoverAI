import os

import razorpay
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()


KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


if not KEY_ID:
    raise RuntimeError(
        "RAZORPAY_KEY_ID is missing from .env"
    )

if not KEY_SECRET:
    raise RuntimeError(
        "RAZORPAY_KEY_SECRET is missing from .env"
    )


# Create Razorpay client
client = razorpay.Client(
    auth=(KEY_ID, KEY_SECRET)
)


def get_client():
    """Return the authenticated Razorpay client."""
    return client


def main():
    print("Razorpay client initialized successfully.")
    print(f"Test Mode: {KEY_ID.startswith('rzp_test_')}")
    print("Secret loaded: True")


if __name__ == "__main__":
    main()