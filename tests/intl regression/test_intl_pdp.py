"""
Cartlow INTL Regression Suite — Module 3: Product Detail Page (PDP)
TC IDs: INTL-012 to INTL-016
All tests run as guest user (no login required).
Uses Nintendo $35 gift card as the reference PDP.
"""

import pytest
from playwright.sync_api import Page, Browser

INTL_URL = "https://stage.cartlow.com/intl/en"
PDP_URL  = "https://stage.cartlow.com/intl/en/gift-cards/nintendo?mpid=10740946&vid=19079930003&type=digital"


# ── Module-scoped shared PDP page ─────────────────────────────────────────────

@pytest.fixture(scope="module")
def pdp_page(browser: Browser):
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.context.add_cookies([
        {"name": "__selected_country", "value": "intl",
         "domain": "stage.cartlow.com", "path": "/"}
    ])
    page.goto(PDP_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    yield page
    context.close()


# ══════════════════════════════════════════════════════════════════════════════
# INTL-012 — Open PDP successfully (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_012_open_pdp(pdp_page: Page):
    """INTL-012 — Open Product Detail Page successfully."""
    page = pdp_page

    assert "gift-cards" in page.url or "product-detail" in page.url, \
        f"Not on a PDP — URL: {page.url}"
    assert page.locator("#app").count() > 0, \
        "#app root element not found on PDP"
    assert page.title().strip(), \
        "PDP title is empty"

    print(f"\n   URL   : {page.url}")
    print(f"   Title : {page.title()}")
    print(f"   ✅ INTL-012 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-013 — Verify product title (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_013_product_title(pdp_page: Page):
    """INTL-013 — Verify product title is visible and non-empty on PDP."""
    page = pdp_page

    # H1 should be present and non-empty
    assert page.locator("h1").count() > 0, "No <h1> found on PDP"
    title = page.locator("h1").first.inner_text().strip()
    assert title, "Product title (h1) is empty"

    # Page <title> should match or contain the product name
    assert title.lower()[:6] in page.title().lower(), \
        f"Page title '{page.title()}' does not reflect H1 '{title}'"

    print(f"\n   Product title : {title}")
    print(f"   ✅ INTL-013 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-014 — Verify product price (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_014_product_price(pdp_page: Page):
    """INTL-014 — Verify product price is displayed in USD ($) on PDP."""
    page = pdp_page

    # Find a visible element with $XX price pattern
    price_els = page.evaluate("""
        () => [...document.querySelectorAll('*')]
            .filter(e =>
                e.children.length === 0 &&
                e.offsetParent !== null &&
                /\\$\\s*\\d+/.test(e.innerText) &&
                e.innerText.trim().length < 30
            )
            .map(e => e.innerText.trim())
            .slice(0, 5)
    """)

    assert len(price_els) > 0, \
        "No USD ($) price found on PDP"

    # Price must be > $0
    import re
    amounts = [float(m) for p in price_els for m in re.findall(r'[\d.]+', p) if float(m) > 0]
    assert amounts, f"All prices are $0 on PDP — prices found: {price_els}"

    print(f"\n   Price(s) found : {price_els[:3]}")
    print(f"   ✅ INTL-014 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-015 — Verify Add to Cart button (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_015_add_to_cart_button(pdp_page: Page):
    """INTL-015 — Verify Add to Cart button is visible and clickable on PDP."""
    page = pdp_page

    add_btn = page.locator("button:has-text('Add To Cart'), button:has-text('Add to Cart')").first
    assert add_btn.count() > 0, \
        "Add to Cart button not found on PDP"
    assert add_btn.is_visible(), \
        "Add to Cart button is not visible"
    assert add_btn.is_enabled(), \
        "Add to Cart button is disabled"

    print(f"\n   Button text : {add_btn.inner_text().strip()}")
    print(f"   ✅ INTL-015 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-016 — Verify product image loads (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_016_product_image_loads(pdp_page: Page):
    """INTL-016 — Verify product image is visible and loaded (naturalWidth > 0)."""
    page = pdp_page

    # Find product images (exclude nav/logo icons — require reasonable size)
    loaded_images = page.evaluate("""
        () => [...document.querySelectorAll('img')]
            .filter(img =>
                img.offsetParent !== null &&
                img.naturalWidth >= 50 &&
                img.naturalHeight >= 50 &&
                !img.src.includes('logo') &&
                !img.src.includes('icon')
            )
            .map(img => ({
                src: img.src.substring(0, 80),
                width: img.naturalWidth,
                height: img.naturalHeight
            }))
    """)

    assert len(loaded_images) > 0, \
        "No product image found (naturalWidth >= 50) on PDP"

    for img in loaded_images[:3]:
        print(f"\n   Image : {img['src']} ({img['width']}x{img['height']})")

    print(f"   ✅ INTL-016 PASSED — {len(loaded_images)} image(s) loaded")
