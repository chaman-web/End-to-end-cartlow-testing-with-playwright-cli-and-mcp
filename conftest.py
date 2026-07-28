"""
conftest.py — Session-scoped auth + page object fixtures.

Auth strategy:
  - Login ONCE per session, save cookies to .auth_state.json
  - Every test loads saved state (~1s) instead of re-logging in (~25s)
  - Page object fixtures are function-scoped (fresh context per test)

Config:
  - All URLs, credentials, and timeouts come from config.py
  - Override via environment variables (see .env.example)
"""

import json
import os
import pytest
from playwright.sync_api import sync_playwright, Browser, Page

from config import Config
from pages.login_page         import LoginPage
from pages.home_page          import HomePage
from pages.search_page        import SearchPage
from pages.pdp_page           import PDPPage
from pages.gift_card_pdp_page import GiftCardPDPPage
from pages.cart_page          import CartPage
from pages.checkout_page      import CheckoutPage
from pages.payment_page       import PaymentPage


# ── Session auth — login once, save cookies ────────────────────────────────────

def _do_login_and_save():
    """Login headlessly and save auth state to file."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport=Config.VIEWPORT)
        page    = context.new_page()

        page.goto(Config.BASE_URL, wait_until="domcontentloaded", timeout=Config.NAVIGATION_TIMEOUT)
        page.wait_for_timeout(Config.LONG_WAIT)

        login = LoginPage(page)
        login.login(Config.EMAIL, Config.PASSWORD)

        # Switch to INTL channel
        page.evaluate(
            "() => [...document.querySelectorAll('button')]"
            ".find(b => b.innerText.includes('UAE'))?.click()"
        )
        page.wait_for_timeout(Config.SHORT_WAIT)
        page.evaluate(
            "() => [...document.querySelectorAll('span,div,li')]"
            ".find(e => e.innerText.trim() === 'INTL' && e.offsetParent)?.click()"
        )
        page.wait_for_timeout(Config.LONG_WAIT)

        context.add_cookies([{
            "name": "__selected_country", "value": "intl",
            "domain": Config.DOMAIN, "path": "/"
        }])

        os.makedirs(Config.REPORTS_DIR, exist_ok=True)
        os.makedirs(Config.SCREENSHOTS_DIR, exist_ok=True)

        storage = context.storage_state()
        with open(Config.AUTH_FILE, "w") as fh:
            json.dump(storage, fh)

        context.close()
        browser.close()
        print(f"\n✅ Auth state saved → {Config.AUTH_FILE}")
        print(f"   {Config.summary()}")


@pytest.fixture(scope="session", autouse=True)
def session_auth():
    """Run once before all tests — logs in and writes .auth_state.json."""
    _do_login_and_save()
    yield


# ── Auth context factory ───────────────────────────────────────────────────────

def _new_auth_context(browser: Browser):
    """Create an isolated browser context with saved auth cookies."""
    auth_path = os.path.normpath(Config.AUTH_FILE)
    if os.path.exists(auth_path):
        ctx = browser.new_context(
            viewport=Config.VIEWPORT,
            storage_state=auth_path,
        )
    else:
        ctx = browser.new_context(viewport=Config.VIEWPORT)

    ctx.add_cookies([{
        "name": "__selected_country", "value": "intl",
        "domain": Config.DOMAIN, "path": "/"
    }])
    return ctx


# ── Screenshot on failure ──────────────────────────────────────────────────────

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep     = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)

    # Capture screenshot on test failure
    if rep.when == "call" and rep.failed:
        page: Page | None = item.funcargs.get("auth_page")
        if page:
            safe_name = item.nodeid.replace("/", "_").replace("::", "__").replace(" ", "_")
            screenshot_path = os.path.join(
                Config.SCREENSHOTS_DIR, f"FAILED__{safe_name}.png"
            )
            try:
                page.screenshot(path=screenshot_path, full_page=True)
                print(f"\n📸 Screenshot saved → {screenshot_path}")
            except Exception:
                pass


# ── Config fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def config():
    """Expose the Config class to tests."""
    return Config


@pytest.fixture(scope="session")
def base_url():
    return Config.BASE_URL


@pytest.fixture(scope="session")
def intl_url():
    return Config.INTL_URL


@pytest.fixture(scope="session")
def auth_file():
    return Config.AUTH_FILE


# ── Base authenticated page fixture ───────────────────────────────────────────

@pytest.fixture
def auth_page(browser: Browser) -> Page:
    """A Playwright Page pre-loaded with auth cookies. Fresh per test."""
    ctx  = _new_auth_context(browser)
    page = ctx.new_page()
    yield page
    ctx.close()


# ── Page object fixtures (function-scoped — fresh per test) ───────────────────

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
def checkout_page_obj(auth_page: Page) -> CheckoutPage:
    """Named checkout_page_obj to avoid clash with module-level checkout_page fixtures."""
    return CheckoutPage(auth_page)


@pytest.fixture
def payment_page(auth_page: Page) -> PaymentPage:
    return PaymentPage(auth_page)
