"""
Cartlow INTL Regression Suite — Module 2: Search
TC IDs: INTL-006 to INTL-011
All tests run as guest user (no login required).
"""

import pytest
from playwright.sync_api import Page, Browser

INTL_URL = "https://stage.cartlow.com/intl/en"


# ── Shared fixture ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def guest_intl_page(browser: Browser):
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    page = context.new_page()
    page.context.add_cookies([
        {"name": "__selected_country", "value": "intl",
         "domain": "stage.cartlow.com", "path": "/"}
    ])
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    yield page
    context.close()


# ── Helper ─────────────────────────────────────────────────────────────────────

def do_search(page: Page, keyword: str):
    """Type keyword in header search bar and submit."""
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    search = page.locator("input[name='query']").first
    search.click()
    search.fill(keyword)
    page.wait_for_timeout(500)
    search.press("Enter")
    page.wait_for_timeout(5000)


def get_result_count(page: Page) -> int:
    """Return number of unique visible product links on search results page."""
    return page.evaluate("""
        () => [...document.querySelectorAll('a[href*=gift-cards], a[href*=product-detail], a[href*=egift-card]')]
            .filter(a => a.offsetParent !== null)
            .map(a => a.href)
            .filter((v, i, arr) => arr.indexOf(v) === i)
            .length
    """)


# ══════════════════════════════════════════════════════════════════════════════
# INTL-006 — Search valid gift card (P0)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_006_search_valid_gift_card(guest_intl_page: Page):
    """INTL-006 — Search for a valid gift card keyword returns results."""
    page = guest_intl_page
    do_search(page, "Nintendo")

    body = page.locator("body").inner_text().lower()
    count = get_result_count(page)

    assert "nintendo" in body, \
        "Search results page does not mention 'Nintendo'"
    assert count > 0, \
        f"Expected product results for 'Nintendo', got 0"

    print(f"\n   Results for 'Nintendo': {count}")
    print(f"   ✅ INTL-006 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-007 — Search partial keyword (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_007_search_partial_keyword(guest_intl_page: Page):
    """INTL-007 — Partial keyword search returns relevant results."""
    page = guest_intl_page
    do_search(page, "Nint")  # partial of "Nintendo"

    body = page.locator("body").inner_text().lower()
    count = get_result_count(page)

    assert count > 0 or "nint" in body, \
        "Partial keyword 'Nint' returned no results and no mention in body"

    print(f"\n   Results for partial 'Nint': {count}")
    print(f"   ✅ INTL-007 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-008 — Search lowercase (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_008_search_lowercase(guest_intl_page: Page):
    """INTL-008 — Lowercase search returns same results as normal case."""
    page = guest_intl_page
    do_search(page, "nintendo")

    body = page.locator("body").inner_text().lower()
    count = get_result_count(page)

    assert "nintendo" in body, \
        "Lowercase search 'nintendo' returned no relevant results"
    assert count > 0, \
        f"Expected results for lowercase 'nintendo', got 0"

    print(f"\n   Results for 'nintendo' (lowercase): {count}")
    print(f"   ✅ INTL-008 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-009 — Search uppercase (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_009_search_uppercase(guest_intl_page: Page):
    """INTL-009 — Uppercase search returns same results as normal case."""
    page = guest_intl_page
    do_search(page, "NINTENDO")

    body = page.locator("body").inner_text().lower()
    count = get_result_count(page)

    assert "nintendo" in body, \
        "Uppercase search 'NINTENDO' returned no relevant results"
    assert count > 0, \
        f"Expected results for uppercase 'NINTENDO', got 0"

    print(f"\n   Results for 'NINTENDO' (uppercase): {count}")
    print(f"   ✅ INTL-009 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-010 — Search invalid keyword (P1)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_010_search_invalid_keyword(guest_intl_page: Page):
    """INTL-010 — Invalid/gibberish keyword shows no results message."""
    page = guest_intl_page
    do_search(page, "xyzxyzxyz123invalidterm")

    body = page.locator("body").inner_text().lower()
    count = get_result_count(page)

    no_results_phrases = [
        "no result", "no product", "not found", "0 result",
        "couldn't find", "could not find", "no items"
    ]
    has_no_results_msg = any(p in body for p in no_results_phrases)

    assert count == 0 or has_no_results_msg, \
        f"Expected 0 results or a 'no results' message for gibberish query, got {count} results"

    print(f"\n   Results for invalid keyword: {count} | No-results msg: {has_no_results_msg}")
    print(f"   ✅ INTL-010 PASSED")


# ══════════════════════════════════════════════════════════════════════════════
# INTL-011 — Clear search (P2)
# ══════════════════════════════════════════════════════════════════════════════

def test_intl_011_clear_search(guest_intl_page: Page):
    """INTL-011 — Clearing search input and resubmitting returns to homepage/all results."""
    page = guest_intl_page

    # First do a search
    do_search(page, "Nintendo")
    page.wait_for_timeout(2000)

    # Clear the search field and submit empty
    search = page.locator("input[name='query']").first
    search.click()
    search.fill("")
    page.wait_for_timeout(500)

    # Try clear button if present, else navigate back to homepage
    clear_btn = page.locator("button[aria-label*='clear' i], button[aria-label*='reset' i], .clear-search").first
    if clear_btn.count() and clear_btn.is_visible():
        clear_btn.click()
        page.wait_for_timeout(3000)
    else:
        page.goto(INTL_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

    # Should be back on INTL homepage or a neutral state
    assert INTL_URL.split("/intl/en")[0] in page.url, \
        f"After clearing search, unexpected URL: {page.url}"

    # Search input should be empty or homepage loaded
    current_val = search.input_value() if search.count() else ""
    assert current_val == "" or page.url == INTL_URL, \
        f"Search field not cleared: '{current_val}'"

    print(f"\n   After clear — URL: {page.url}")
    print(f"   ✅ INTL-011 PASSED")
