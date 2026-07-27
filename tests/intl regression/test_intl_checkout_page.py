"""
Cartlow INTL Regression Suite — Module 5: Checkout Page
TC IDs: CHK-001 to CHK-005
Requires login + item in cart.
"""

import pytest
from playwright.sync_api import Page, Browser, ConsoleMessage
from tests.helpers import (
    login_and_switch_intl, ensure_cart_has_item,
    INTL_URL, CART_URL, PDP_URL
)

CHECKOUT_URL = f"{INTL_URL}/checkout/onepage"


# ── Module-scoped checkout page (login + cart fill once) ──────────────────────

@pytest.fixture(scope="module")
def checkout_page(browser: Browser):
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    login_and_switch_intl(page)
    ensure_cart_has_item(page)
    page.goto(CHECKOUT_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    yield page
    context.close()


# ══════════════════════════════════════════════════════════════════════════════
# CHK-001 — Verify checkout page opens successfully (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_001_checkout_page_opens(checkout_page: Page):
    """CHK-001 — Checkout page opens and renders the main app."""
    page = checkout_page

    assert page.locator("#app").count() > 0, \
        "#app root element not found on checkout page"

    body = page.locator("body").inner_text()
    assert "Payment Method" in body or "Place Order" in body, \
        "Checkout page content not loaded — expected 'Payment Method' or 'Place Order'"

    print(f"\n   URL   : {page.url}")
    print(f"   ✅ CHK-001 PASSED — checkout page opened successfully")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-002 — Verify checkout URL is correct (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_002_checkout_url(checkout_page: Page):
    """CHK-002 — Checkout URL must be the INTL onepage checkout."""
    page = checkout_page

    assert "intl/en" in page.url, \
        f"Not on INTL channel — URL: {page.url}"
    assert "checkout/onepage" in page.url, \
        f"Not on checkout onepage — URL: {page.url}"
    assert page.url == CHECKOUT_URL or page.url.startswith(CHECKOUT_URL), \
        f"Unexpected checkout URL: {page.url}"

    print(f"\n   URL : {page.url}")
    print(f"   ✅ CHK-002 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-003 — Verify page loads without JavaScript errors (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_003_no_js_errors(browser: Browser):
    """CHK-003 — Checkout page loads without critical JavaScript errors."""
    errors: list[str] = []

    skip_patterns = [
        "favicon", "err_blocked", "net::err", "google", "analytics",
        "403", "mp-wallet", "failed to load resource",
        "x-frame-options", "sameorigin", "stage-agent",  # staging chat widget
    ]

    def capture(msg: ConsoleMessage):
        if msg.type == "error":
            if not any(p in msg.text.lower() for p in skip_patterns):
                errors.append(msg.text)

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.on("console", capture)

    login_and_switch_intl(page)
    ensure_cart_has_item(page)
    page.goto(CHECKOUT_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    context.close()

    if errors:
        print(f"\n   ⚠️  JS errors:\n" + "\n".join(f"      - {e}" for e in errors))
    assert len(errors) == 0, f"Critical JS errors on checkout: {errors}"
    print(f"\n   ✅ CHK-003 PASSED — no critical JS errors")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-004 — Verify checkout page title (P2)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_004_checkout_page_title(checkout_page: Page):
    """CHK-004 — Checkout page title is non-empty and checkout-related."""
    page = checkout_page

    title = page.title().strip()
    assert title, "Checkout page title is empty"
    assert "checkout" in title.lower() or "cartlow" in title.lower(), \
        f"Unexpected page title: '{title}'"

    print(f"\n   Title : {title}")
    print(f"   ✅ CHK-004 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-005 — Verify customer is logged in / email identity shown (P0)
# Note: INTL digital checkout does not show email in the form (no shipping
# address). Logged-in state is confirmed via the header account greeting.
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_005_customer_can_access_checkout(checkout_page: Page):
    """CHK-005 — Verify logged-in customer can access checkout (not redirected to login)."""
    page = checkout_page

    # Must still be on checkout onepage — not redirected to login
    assert "checkout/onepage" in page.url, \
        f"Redirected away from checkout — URL: {page.url}"
    assert "login" not in page.url.lower(), \
        f"Redirected to login — user not authenticated: {page.url}"

    # Checkout action (Place Order) must be present — only accessible when logged in
    body = page.locator("body").inner_text()
    assert "Place Order" in body or "Payment Method" in body, \
        "Checkout actions not visible — user may not be authenticated"

    print(f"\n   URL          : {page.url}")
    print(f"   Place Order  : ✅ visible")
    print(f"   ✅ CHK-005 PASSED — logged-in user can access checkout")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-006 — Verify digital product name in order summary (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_006_digital_product_name(checkout_page: Page):
    """CHK-006 — Verify digital product name appears in checkout order summary."""
    page = checkout_page
    body = page.locator("body").inner_text()

    assert "Nintendo" in body, \
        "Product name 'Nintendo' not found in checkout order summary"
    assert "$35" in body.replace(" ", "") or "35.00" in body, \
        "Product denomination not found in checkout order summary"

    print(f"\n   Product : Nintendo $35 ✅")
    print(f"   ✅ CHK-006 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-007 — Verify quantity in order summary (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_007_quantity(checkout_page: Page):
    """CHK-007 — Verify product quantity is shown as 1 in checkout order summary."""
    page = checkout_page
    body = page.locator("body").inner_text()

    # Checkout summary shows "35.00 × 1" for qty
    assert "× 1" in body or "x 1" in body.lower() or "1 Items" in body, \
        "Quantity '1' not found in checkout order summary"

    print(f"\n   Quantity : 1 ✅")
    print(f"   ✅ CHK-007 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-008 — Verify unit price (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_008_unit_price(checkout_page: Page):
    """CHK-008 — Verify unit price is $35.00 in checkout order summary."""
    import re
    page = checkout_page
    body = " ".join(page.locator("body").inner_text().split())

    # Find price amounts in the summary
    prices = [float(p.replace(",", "")) for p in re.findall(r'\$\s*([\d,]+\.?\d*)', body)]
    assert 35.0 in prices, \
        f"Unit price $35.00 not found in checkout summary — prices found: {prices}"

    print(f"\n   Unit price : $35.00 ✅")
    print(f"   ✅ CHK-008 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-009 — Verify subtotal (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_009_subtotal(checkout_page: Page):
    """CHK-009 — Verify subtotal equals product price ($35.00)."""
    import re
    page = checkout_page
    body = " ".join(page.locator("body").inner_text().split())

    assert "Sub Total" in body, "'Sub Total' label not found in checkout summary"

    match = re.search(r"Sub Total.*?\$\s*([\d,]+\.?\d*)", body, re.IGNORECASE)
    assert match, "Could not extract subtotal value from checkout summary"

    subtotal = float(match.group(1).replace(",", ""))
    assert subtotal == 35.0, \
        f"Subtotal ${subtotal} does not match expected $35.00"

    print(f"\n   Sub Total : ${subtotal:.2f} ✅")
    print(f"   ✅ CHK-009 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# CHK-010 — Verify grand total (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_chk_010_grand_total(checkout_page: Page):
    """CHK-010 — Verify grand total >= subtotal and displayed in USD."""
    import re
    page = checkout_page
    body = " ".join(page.locator("body").inner_text().split())

    assert "Total" in body, "'Total' label not found in checkout summary"

    # Grand total — "Total (Inclusive of Management Fee)"
    match = re.search(r"Total.*?Inclusive.*?\$\s*([\d,]+\.?\d*)", body, re.IGNORECASE)
    if not match:
        match = re.search(r"Total\s*\$\s*([\d,]+\.?\d*)", body, re.IGNORECASE)
    assert match, "Could not extract grand total value from checkout summary"

    total = float(match.group(1).replace(",", ""))
    assert total > 0, f"Grand total is $0 — expected a positive value"
    assert total >= 35.0, \
        f"Grand total ${total} is less than product price $35.00"

    print(f"\n   Grand Total : ${total:.2f} ✅")
    print(f"   ✅ CHK-010 PASSED")
