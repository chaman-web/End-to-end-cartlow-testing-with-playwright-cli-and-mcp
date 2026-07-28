"""
config.py — Central environment-aware configuration.

Usage:
    from config import Config

    Config.BASE_URL    → current environment base URL
    Config.EMAIL       → test account email

Override defaults by setting environment variables before running pytest:
    ENV=production pytest ...
    EMAIL=other@test.com pytest ...
"""

import os


class Config:
    # ── Environment ────────────────────────────────────────────────────────────
    ENV = os.getenv("ENV", "staging")          # "staging" | "production"

    # ── Base URLs ──────────────────────────────────────────────────────────────
    _DOMAINS = {
        "staging":    "stage.cartlow.com",
        "stage2":     "stage2.cartlow.com",
        "production": "cartlow.com",
    }
    DOMAIN   = _DOMAINS.get(ENV, _DOMAINS["staging"])

    BASE_URL = f"https://{DOMAIN}/uae/en"
    INTL_URL = f"https://{DOMAIN}/intl/en"
    KSA_URL  = f"https://{DOMAIN}/ksa/en"

    CART_URL     = f"{INTL_URL}/checkout/cart"
    CHECKOUT_URL = f"{INTL_URL}/checkout/onepage"

    # ── Test product ───────────────────────────────────────────────────────────
    PDP_URL = (
        f"https://{DOMAIN}/intl/en/gift-cards/nintendo"
        "?mpid=10740946&vid=19079930003&type=digital"
    )

    # ── Credentials ────────────────────────────────────────────────────────────
    EMAIL    = os.getenv("TEST_EMAIL",    "muhammad.akmal@cartlow.com")
    PASSWORD = os.getenv("TEST_PASSWORD", "Test!123")

    # ── Auth ───────────────────────────────────────────────────────────────────
    AUTH_FILE = os.path.join(os.path.dirname(__file__), ".auth_state.json")

    # ── Browser ────────────────────────────────────────────────────────────────
    HEADLESS  = os.getenv("HEADLESS", "true").lower() == "true"
    SLOW_MO   = int(os.getenv("SLOW_MO", "0"))           # ms delay between actions
    VIEWPORT  = {"width": 1280, "height": 800}

    # ── Timeouts (ms) ──────────────────────────────────────────────────────────
    DEFAULT_TIMEOUT   = 60_000
    NAVIGATION_TIMEOUT = 60_000
    SHORT_WAIT        = 2_000
    MEDIUM_WAIT       = 5_000
    LONG_WAIT         = 10_000

    # ── Reports ────────────────────────────────────────────────────────────────
    REPORTS_DIR      = os.path.join(os.path.dirname(__file__), "reports")
    SCREENSHOTS_DIR  = os.path.join(REPORTS_DIR, "screenshots")

    @classmethod
    def is_production(cls) -> bool:
        return cls.ENV == "production"

    @classmethod
    def is_staging(cls) -> bool:
        return cls.ENV in ("staging", "stage2")

    @classmethod
    def summary(cls) -> str:
        return (
            f"ENV={cls.ENV} | "
            f"BASE_URL={cls.BASE_URL} | "
            f"EMAIL={cls.EMAIL} | "
            f"HEADLESS={cls.HEADLESS}"
        )
