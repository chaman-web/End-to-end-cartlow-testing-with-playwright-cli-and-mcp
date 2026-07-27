"""
conftest.py — Session-scoped auth + page object fixtures.

Auth strategy:
  - Login ONCE per session, save cookies to .auth_state.json
  - Every test loads saved state (~1s) instead of re-logging in (~25s)
  - Page object fixtures are function-scoped (fresh context per test)
"""

import json
import os
import pytest
from playwright.sync_api import sync_playwright, Browser, Page

from pages.login_page       import LoginPage
from pages.home_page        import HomePage
from pages.search_page      import SearchPage
from pages.pdp_page         import PDPPage
from pages.gift_card_pdp_page import GiftCardPDPPage
from pages.cart_page        import CartPage
from pages.checkout_page    import CheckoutPage
from pages.payment_page     import PaymentPage

# ── Constants ──────────────────────────────────────────────────────────────────
BASE_URL  = "https://stage.cartlow.com/uae/en"
INTL_URL  = "https://stage.cartlow.com/intl/en"
EMAIL     = "muhammad.akmal@cartlow.com"
PASSWORD  = "Test!123"
AUTH_FILE = os.path.join(os.path.dirname(__file__), ".auth_state.json")


# ── Session auth — login once, save cookies ────────────────────────────────────

def _do_login_and_save():
    """Login headlessly and save auth state to file."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 800})
        page    = context.new_page()

        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(8000)

        login = LoginPage(page)
        login.login(EMAIL, PASSWORD)

        # Switch to INTL channel
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

        context.add_cookies([{
            "name": "__selected_country", "value": "intl",
            "domain": "stage.cartlow.com", "path": "/"
        }])

        storage = context.storage_state()
        with open(AUTH_FILE, "w") as fh:
            json.dump(storage, fh)

        context.close()
        browser.close()
        print(f"\n✅ Auth state saved → {AUTH_FILE}")


@pytest.fixture(scope="session", autouse=True)
def session_auth():
    """Run once before all tests — logs in and writes .auth_state.json."""
    _do_login_and_save()
    yield


@pytest.fixture(scope="session")
def auth_file():
    return AUTH_FILE


@pytest.fixture(scope="session")
def base_url():
    return BASE_URL


@pytest.fixture(scope="session")
def intl_url():
    return INTL_URL


# ── Auth context factory ───────────────────────────────────────────────────────

def _new_auth_context(browser: Browser):
    """Create an isolated browser context with saved auth cookies."""
    auth_path = os.path.normpath(AUTH_FILE)
    if os.path.exists(auth_path):
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            storage_state=auth_path,
        )
        ctx.add_cookies([{
            "name": "__selected_country", "value": "intl",
            "domain": "stage.cartlow.com", "path": "/"
        }])
        return ctx
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    return ctx


# ── Page object fixtures (function-scoped — fresh per test) ───────────────────

@pytest.fixture
def auth_page(browser: Browser) -> Page:
    """A Playwright Page pre-loaded with auth cookies."""
    ctx = _new_auth_context(browser)
    page = ctx.new_page()
    yield page
    ctx.close()


@pytest.fixture
def login_page(auth_page: Page) -> LoginPage:
    return LoginPage(auth_page)


@pytest.fixture
def home_page(auth_page: Page) -> HomePage:
    return HomePage(auth_page)


@pytest.fixture
def search_page(auth_page: Page) -> SearchPage:
    return SearchPage(auth_page)


@pytest.fixture
def pdp_page(auth_page: Page) -> PDPPage:
    return PDPPage(auth_page)


@pytest.fixture
def gc_pdp_page(auth_page: Page) -> GiftCardPDPPage:
    return GiftCardPDPPage(auth_page)


@pytest.fixture
def cart_page(auth_page: Page) -> CartPage:
    return CartPage(auth_page)


@pytest.fixture
def checkout_page(auth_page: Page) -> CheckoutPage:
    return CheckoutPage(auth_page)


@pytest.fixture
def payment_page(auth_page: Page) -> PaymentPage:
    return PaymentPage(auth_page)


# ── Test result hook ───────────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
