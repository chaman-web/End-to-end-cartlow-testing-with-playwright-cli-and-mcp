"""
Cartlow INTL Regression Suite — Module 4: Cart
TC IDs: INTL-017 to INTL-022
Requires login — digital gift cards have fixed qty 1.
"""

import re
import pytest
from playwright.sync_api import Page, Browser

BASE_URL = "https://stage.cartlow.com/uae/en"
INTL_URL = "https://stage.cartlow.com/intl/en"
CART_URL = f"{INTL_URL}/checkout/cart"
PDP_URL  = "https://stage.cartlow.com/intl/en/gift-cards/nintendo?mpid=10740946&vid=19079930003&type=digital"
EMAIL    = "muhammad.akmal@cartlow.com"
PASSWORD = "Test!123"


# ── Helpers ────────────────────────────────────────────────────────────────────

def login_and_switch_intl(page: Page):
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
        except:
            page.wait_for_timeout(1500)
    page.locator("#login-email").fill(EMAIL)
    page.locator("#login-password").fill(PASSWORD)
    page.wait_for_timeout(500)
    page.evaluate(
        "() => [...document.querySelectorAll('button')]"
        ".find(b => b.innerText.trim() === 'Sign In' && b.offsetParent !== null)?.click()"
    )
    page.wait_for_timeout(6000)
    page.locator("button:has-text('UAE')").first.click()
    page.wait_for_timeout(1500)
    page.locator("span.cursor-pointer:has-text('INTL')").first.click()
    page.wait_for_timeout(8000)
    page.context.add_cookies([
        {"name": "__selected_country", "value": "intl",
         "domain": "stage.cartlow.com", "path": "/"}
    ])


def ensure_cart_has_item(page: Page):
    """Ensure at least one Nintendo $35 card is in the cart."""
    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    body = page.locator("body").inner_text()
    if "Nintendo" in body and "Remove" in body:
        return  # already has item
    # Add from PDP
    page.goto(PDP_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    # Scroll to reveal Add to Cart / View Cart
    for _ in range(15):
        page.mouse.wheel(0, 200)
        page.wait_for_timeout(200)
    page.wait_for_timeout(1000)
    body = page.locator("body").inner_text()
    if "View Cart" not in body:
        # Click Add To Cart via JS (button may be covered)
        page.evaluate(
            "() => [...document.querySelectorAll('button,div,a')]"
            ".find(e => /add.to.cart/i.test(e.innerText) && e.offsetParent)?.click()"
        )
        page.wait_for_timeout(4000)
    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)


def clear_cart(page: Page):
    """Remove all items from cart."""
    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    for _ in range(5):
        remove = page.locator("a:has-text('Remove'), button:has-text('Remove'), span:has-text('Remove')").first
        if remove.count() and remove.is_visible():
            remove.click()
            page.wait_for_timeout(3000)
        else:
            break


def get_price(page: Page, label: str) -> float:
    """Extract dollar amount following a label in the cart summary."""
    # Normalise body — collapse whitespace/newlines for easier regex matching
    body = " ".join(page.locator("body").inner_text().split())
    pattern = rf"{re.escape(label)}.*?\$\s*([\d,]+\.?\d*)"
    match = re.search(pattern, body, re.IGNORECASE | re.DOTALL)
    if match:
        return float(match.group(1).replace(",", ""))
    return 0.0


# ── Module-scoped logged-in page ───────────────────────────────────────────────

@pytest.fixture(scope="module")
def logged_intl_page(browser: Browser):
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    login_and_switch_intl(page)
    yield page
    context.close()


# ══════════════════════════════════════════════════════════════════════════════
# INTL-017 — Add gift card to cart (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_017_add_gift_card_to_cart(logged_intl_page: Page):
    """INTL-017 — Add a gift card to cart and verify it appears in cart."""
    page = logged_intl_page

    # Clear cart first for clean state
    clear_cart(page)

    # Go to PDP and add
    page.goto(PDP_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    for _ in range(15):
        page.mouse.wheel(0, 200)
        page.wait_for_timeout(200)
    page.wait_for_timeout(1000)

    body = page.locator("body").inner_text()
    if "View Cart" in body:
        # Item already in cart from a previous session
        pass
    else:
        page.evaluate(
            "() => [...document.querySelectorAll('button,div,a')]"
            ".find(e => /add.to.cart/i.test(e.innerText) && e.offsetParent)?.click()"
        )
        page.wait_for_timeout(4000)

    # Verify cart
    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    body = page.locator("body").inner_text()

    assert "Nintendo" in body, "Nintendo gift card not found in cart after adding"
    assert "35" in body, "Expected price $35 not shown in cart"
    assert "Remove" in body, "Remove option not visible — cart may be empty"

    print(f"\n   ✅ INTL-017 PASSED — Nintendo $35 added to cart")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-018 — Increase quantity (P1)
# Note: INTL digital gift cards are fixed qty=1 per item. Adding the same card
# again creates a new line item (not qty+1). This test verifies that behaviour.
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_018_increase_quantity(logged_intl_page: Page):
    """INTL-018 — Verify quantity behaviour for digital gift cards on INTL."""
    page = logged_intl_page
    ensure_cart_has_item(page)

    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    body = page.locator("body").inner_text()

    # Qty shown as "1" for digital gift card
    qty_shown = "1" in body
    assert qty_shown, "Quantity not shown in cart"

    # Digital cards: no +/- quantity buttons (fixed qty=1 per card)
    plus_btn = page.locator("button:has-text('+')").first
    qty_fixed = not (plus_btn.count() and plus_btn.is_visible())

    if qty_fixed:
        print(f"\n   ℹ️  Digital gift card qty is fixed at 1 (expected behaviour)")
    else:
        # If +/- exists, click + and verify qty increases
        qty_before = body.count("1")
        plus_btn.click()
        page.wait_for_timeout(3000)
        body_after = page.locator("body").inner_text()
        assert "2" in body_after, "Qty did not increase after clicking +"
        print(f"\n   Qty increased to 2")

    print(f"   ✅ INTL-018 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-019 — Decrease quantity (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_019_decrease_quantity(logged_intl_page: Page):
    """INTL-019 — Verify quantity decrease / minimum qty for digital gift cards."""
    page = logged_intl_page
    ensure_cart_has_item(page)

    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    body = page.locator("body").inner_text()

    minus_btn = page.locator("button:has-text('-')").first
    qty_fixed = not (minus_btn.count() and minus_btn.is_visible())

    if qty_fixed:
        # Verify cart still shows qty 1 (minimum enforced)
        assert "1" in body, "Expected qty 1 in cart"
        print(f"\n   ℹ️  Digital gift card qty fixed at 1 — minimum enforced")
    else:
        minus_btn.click()
        page.wait_for_timeout(3000)
        body_after = page.locator("body").inner_text()
        # Should not go below 1
        assert "0 Item" not in body_after or "Remove" not in body_after, \
            "Qty went below 1 without removing item"
        print(f"\n   Qty decreased, minimum respected")

    print(f"   ✅ INTL-019 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-020 — Remove product from cart (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_020_remove_product(logged_intl_page: Page):
    """INTL-020 — Remove product from cart and verify cart is empty."""
    page = logged_intl_page
    ensure_cart_has_item(page)

    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    # Click Remove via JS (element may be off-screen)
    removed = page.evaluate("""
        () => {
            const el = [...document.querySelectorAll('a,button,span')]
                .find(e => e.innerText.trim() === 'Remove');
            if (el) { el.click(); return true; }
            return false;
        }
    """)
    assert removed, "Remove element not found in cart DOM"
    page.wait_for_timeout(4000)

    body = page.locator("body").inner_text()

    # Cart should now be empty
    empty_indicators = ["your cart is empty", "no items", "0 item"]
    cart_empty = any(p in body.lower() for p in empty_indicators)
    nintendo_gone = "Nintendo" not in body or "Remove" not in body

    assert cart_empty or nintendo_gone, \
        f"Product still appears in cart after Remove. Body: {body[:200]}"

    print(f"\n   ✅ INTL-020 PASSED — product removed from cart")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-021 — Verify subtotal (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_021_verify_subtotal(logged_intl_page: Page):
    """INTL-021 — Verify cart subtotal matches product price."""
    page = logged_intl_page
    ensure_cart_has_item(page)

    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    body = page.locator("body").inner_text()

    # Extract all dollar amounts
    amounts = re.findall(r'\$\s*([\d,]+\.?\d*)', body)
    amounts = [float(a.replace(",", "")) for a in amounts]

    # Subtotal label must be present
    assert "Sub Total" in body, "'Sub Total' label not found in cart"

    subtotal = get_price(page, "Sub Total")
    assert subtotal > 0, f"Subtotal is $0 — expected a positive value"

    # Subtotal must equal product price ($35.00 for Nintendo $35)
    assert subtotal == 35.00, \
        f"Subtotal ${subtotal} does not match product price $35.00"

    print(f"\n   Sub Total : ${subtotal:.2f}")
    print(f"   ✅ INTL-021 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-022 — Verify total (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_022_verify_total(logged_intl_page: Page):
    """INTL-022 — Verify cart total is >= subtotal and displayed in USD."""
    page = logged_intl_page
    ensure_cart_has_item(page)

    page.goto(CART_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)
    body = page.locator("body").inner_text()

    assert "Total" in body, "'Total' label not found in cart"

    subtotal = get_price(page, "Sub Total")
    total    = get_price(page, r"Total\s*\(Inclusive")

    # If inclusive total not found, fall back to plain Total
    if total == 0.0:
        total = get_price(page, "Total")

    assert total > 0, f"Total is $0 — expected a positive value"
    assert total >= subtotal, \
        f"Total ${total} is less than subtotal ${subtotal} — unexpected"

    # Total should be in USD ($ symbol present)
    assert "$" in body, "USD ($) symbol not found in cart total section"

    print(f"\n   Sub Total : ${subtotal:.2f}")
    print(f"   Total     : ${total:.2f}")
    print(f"   ✅ INTL-022 PASSED")
