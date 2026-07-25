"""
Cartlow INTL Regression Suite — Module 1: Homepage
TC IDs: INTL-001 to INTL-005
All tests run as guest user (no login required).
"""

import pytest
from playwright.sync_api import Page, ConsoleMessage, Browser

INTL_URL = "https://stage.cartlow.com/intl/en"


# ── Module-scoped guest page (navigate to INTL once, share across all tests) ──

@pytest.fixture(scope="module")
def guest_intl_page(browser: Browser):
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.context.add_cookies([
        {"name": "__selected_country", "value": "intl",
         "domain": "stage.cartlow.com", "path": "/"}
    ])
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    yield page
    context.close()


# ══════════════════════════════════════════════════════════════════════════════
# INTL-001 — Open INTL homepage successfully (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_001_homepage_loads(guest_intl_page: Page):
    """INTL-001 — Open INTL homepage successfully."""
    page = guest_intl_page
    assert page.url.startswith(INTL_URL), \
        f"Expected INTL URL, got: {page.url}"
    assert page.title().strip(), \
        "Page title is empty"
    assert page.locator("#app").count() > 0, \
        "#app root element not found"
    print(f"\n   ✅ INTL-001 PASSED — URL: {page.url} | Title: {page.title()}")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-002 — Homepage loads without console errors (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_002_no_console_errors(browser: Browser):
    """INTL-002 — Homepage loads without critical console errors."""
    errors: list[str] = []

    # Known benign staging issues — not app bugs
    skip_patterns = [
        "favicon", "err_blocked", "net::err", "google", "analytics",
        "403", "mp-wallet", "failed to load resource",
    ]

    def capture(msg: ConsoleMessage):
        if msg.type == "error":
            if not any(p in msg.text.lower() for p in skip_patterns):
                errors.append(msg.text)

    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.on("console", capture)
    page.context.add_cookies([
        {"name": "__selected_country", "value": "intl",
         "domain": "stage.cartlow.com", "path": "/"}
    ])
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    context.close()

    if errors:
        print(f"\n   ⚠️  Console errors:\n" + "\n".join(f"      - {e}" for e in errors))
    assert len(errors) == 0, f"Critical console errors found: {errors}"
    print(f"\n   ✅ INTL-002 PASSED — no critical console errors")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-003 — Only Gift Cards are displayed (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_003_only_gift_cards(guest_intl_page: Page):
    """INTL-003 — Verify only Gift Cards are displayed on INTL homepage."""
    page = guest_intl_page
    body = page.locator("body").inner_text().lower()

    assert "gift card" in body, \
        "Gift Cards section not found on INTL homepage"

    physical_terms = ["refurbished", "used device", "grade a", "grade b", "grade c"]
    found = [t for t in physical_terms if t in body]
    assert not found, \
        f"Physical product terms found on INTL homepage: {found}"

    count = len(page.evaluate(
        "() => [...document.querySelectorAll('a[href*=product-detail]')].map(a=>a.href)"
    ))
    print(f"\n   Product cards found: {count}")
    print(f"   ✅ INTL-003 PASSED — only Gift Cards displayed")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-004 — Currency is correct (USD $) (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_004_currency_usd(guest_intl_page: Page):
    """INTL-004 — Verify currency is USD ($) on INTL channel."""
    page = guest_intl_page

    # Check currency shown in product prices (not the country-switcher dropdown)
    # Price elements use $ symbol
    price_text = page.evaluate("""
        () => {
            const els = [...document.querySelectorAll('*')].filter(el =>
                el.children.length === 0 &&
                el.offsetParent !== null &&
                /\\$\\s*[\\d]/.test(el.innerText)
            );
            return els.map(e => e.innerText.trim()).slice(0, 5);
        }
    """)
    assert len(price_text) > 0 or "$" in page.locator("body").inner_text(), \
        "USD ($) price symbol not found on INTL homepage"

    # AED must not appear in price elements
    aed_prices = page.evaluate("""
        () => [...document.querySelectorAll('*')].filter(el =>
            el.children.length === 0 &&
            el.offsetParent !== null &&
            /AED\\s*[\\d]/.test(el.innerText)
        ).map(e => e.innerText.trim())
    """)
    assert len(aed_prices) == 0, \
        f"AED prices shown on INTL channel: {aed_prices}"

    print(f"\n   Price samples: {price_text[:3]}")
    print(f"\n   ✅ INTL-004 PASSED — currency is USD ($)")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-005 — Language is English (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_005_language_english(guest_intl_page: Page):
    """INTL-005 — Verify language is English on INTL channel."""
    page = guest_intl_page

    lang = page.evaluate("() => document.documentElement.lang")
    assert lang.startswith("en"), \
        f"HTML lang='{lang}', expected 'en'"

    assert "/en" in page.url, \
        f"Expected /en in URL, got: {page.url}"

    body = page.locator("body").inner_text()
    for label in ["Search", "Cart"]:
        assert label.lower() in body.lower(), \
            f"English UI label '{label}' not found on page"

    direction = page.evaluate("() => document.documentElement.dir")
    assert direction != "rtl", \
        "Page direction is RTL — expected LTR for English"

    print(f"\n   ✅ INTL-005 PASSED — language is English (lang={lang}, dir={direction})")
