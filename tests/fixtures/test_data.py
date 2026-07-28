"""
tests/fixtures/test_data.py — Static test data for all test suites.

Centralised here so test files never contain raw strings for
card numbers, addresses, credentials, or product URLs.
"""

# ── Gift Card ──────────────────────────────────────────────────────────────────
GIFT_CARD = {
    "name":    "Nintendo",
    "amount":  35.00,
    "currency": "USD",
    "pdp_url": (
        "https://stage.cartlow.com/intl/en/gift-cards/nintendo"
        "?mpid=10740946&vid=19079930003&type=digital"
    ),
}

# ── Recipient data (used in gift card tests) ───────────────────────────────────
RECIPIENTS = {
    "valid_email": {
        "name":    "John Doe",
        "contact": "johndoe@test.com",
        "message": "Happy Birthday!",
    },
    "valid_mobile": {
        "name":    "Jane Smith",
        "contact": "0501234567",
        "message": "Congrats!",
    },
    "invalid_contact": {
        "name":    "Bad User",
        "contact": "not-valid",
        "message": "",
    },
    "empty_name": {
        "name":    "",
        "contact": "test@test.com",
        "message": "",
    },
    "long_message": {
        "name":    "Test User",
        "contact": "test@test.com",
        "message": "A" * 500,
    },
}

# ── Addresses ──────────────────────────────────────────────────────────────────
ADDRESSES = {
    "uae_default": {
        "full_name":    "Test User",
        "mobile":       "0501234567",
        "address":      "123 Test Street",
        "city":         "Dubai",
        "country":      "UAE",
    },
    "intl_default": {
        "full_name":    "Test User",
        "mobile":       "0501234567",
        "address":      "456 INTL Ave",
        "city":         "Dubai",
        "country":      "International",
    },
}

# ── Payment Cards ──────────────────────────────────────────────────────────────
CARDS = {
    "checkout_success": {
        "number":     "4242424242424242",
        "expiry":     "1133",
        "expiry_fmt": "11/33",
        "cvv":        "123",
        "name":       "Test User",
        "bank_pass":  "Checkout1!",
        "label":      "Checkout.com — success",
    },
    "checkout_decline": {
        "number":     "4000000000000002",
        "expiry":     "1133",
        "expiry_fmt": "11/33",
        "cvv":        "123",
        "name":       "Test User",
        "bank_pass":  "",
        "label":      "Checkout.com — generic decline",
    },
    "noon_success": {
        "number":     "4000000000002503",
        "expiry":     "1133",
        "expiry_fmt": "11/33",
        "cvv":        "123",
        "name":       "Test User",
        "bank_pass":  "1234",
        "label":      "Noon Pay — success",
    },
}

# ── Test Users ─────────────────────────────────────────────────────────────────
USERS = {
    "default": {
        "email":    "muhammad.akmal@cartlow.com",
        "password": "Test!123",
    },
}
