"""
tests/helpers.py — Shared test helpers for Cartlow automation suite.

Centralised here to avoid duplication across test modules.
All test logic lives in individual test files — these are pure utilities.
"""

import re
from playwright.sync_api import Page

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_URL = "https://stage.cartlow.com/uae/en"
INTL_URL = "https://stage.cartlow.com/intl/en"
CART_URL = f"{INTL_URL}/checkout/cart"
PDP_URL  = (
    "https://stage.cartlow.com/intl/en/gift-cards/nintendo"
    "?mpid=10740946&vid=19079930003&type=digital"
)
EMAIL    = "muhammad.akmal@cartlow.com"
PASSWORD = "Test!123"


# ── Auth ───────────────────────────────────────────────────────────────────────

def login_and_switch_intl(page: Page):
    """Full login + switch to INTL channel (used in module-scoped fixtures)."""
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)

    for _ in range(15):
        try:
            page.evaluate(
                "document.querySelector('#app').__vue_app__.config.globalProperties"
                ".$emitter.emit('open-customer-auth-modal')"
            )
            page.locator("#login-email").wait_for(state="visible", timeout=3000)
            page.wait_for_timeout(500)
            page.locator("#login-email").evaluate("el => el.focus()")
            if page.locator("#login-email").evaluate("el => document.activeElement === el"):
                break
        except Exception:
            page.wait_for_timeout(1500)

    page.locator("#login-email").fill(EMAIL)
    page.locator("#login-password").fill(PASSWORD)
    page.wait_for_timeout(500)
    page.evaluate(
        "() => [...document.querySelectorAll('button')]"
        ".find(b => b.innerText.trim() === 'Sign In' && b.offsetParent !== null)?.click()"
    )
    page.wait_for_timeout(6000)

    # Switch to INTL
    page.evaluate(
        "() => [...document.querySelectorAll('button')]"
        ".find(b => b.innerText.includes('UAE'))?.click()"
    )
    page.wait_for_timeout(2000)
    page.evaluate(
        "() => [...document.querySelectorAll('span,div,li')]"
        ".find(e => e.innerText.trim() === 'INTL' && e.offsetParent)?.click()"
    )
    page.wait_for_timeout(8000)
    page.context.add_cookies([{
        "name": "__selected_country", "value": "intl",
        "domain": "stage.cartlow.com", "path": "/"
    }])


# ── Cart ───────────────────────────────────────────────────────────────────────

def clear_cart(page: Page):
    """
    Remove all items from cart.
    Handles the Agree/Disagree confirmation popup that appears on Remove click.
    Uses the correct visible Remove button selector confirmed from live DOM inspection.
    """
    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    # Visible Remove button: span[role="button"][tabindex="0"] with SVG icon + "Remove" text
    remove_btn = page.locator('span[role="button"][tabindex="0"]:has-text("Remove")')

    if remove_btn.count() == 0:
        return

    removed = 0
    for _ in range(20):
        if remove_btn.count() == 0:
            break
        try:
            remove_btn.first.click(timeout=5000)
            page.wait_for_timeout(1500)
            # Handle confirmation popup
            agree = page.locator("button:has-text('Agree')")
            if agree.count() > 0:
                agree.first.click(timeout=5000)
                page.wait_for_timeout(3000)
            removed += 1
        except Exception:
            break

    page.wait_for_timeout(2000)
    if removed:
        print(f"   Cleared {removed} cart item(s) ✅")


def ensure_cart_has_item(page: Page):
    """Ensure at least one Nintendo $35 gift card is in the cart."""
    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    body = page.locator("body").inner_text()
    if "Nintendo" in body and "Remove" in body:
        return  # already has item

    # Add from PDP
    page.goto(PDP_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    for _ in range(15):
        page.mouse.wheel(0, 200)
        page.wait_for_timeout(200)
    page.wait_for_timeout(1000)

    body = page.locator("body").inner_text()
    if "View Cart" not in body:
        page.evaluate(
            "() => [...document.querySelectorAll('button,div,a')]"
            ".find(e => /add.to.cart/i.test(e.innerText) && e.offsetParent)?.click()"
        )
        page.wait_for_timeout(4000)

    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)


# ── Price extraction ───────────────────────────────────────────────────────────

def get_price(page: Page, label: str) -> float:
    """Extract dollar amount following a label in the cart/order summary."""
    body = " ".join(page.locator("body").inner_text().split())
    pattern = rf"{re.escape(label)}.*?\$\s*([\d,]+\.?\d*)"
    match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0
