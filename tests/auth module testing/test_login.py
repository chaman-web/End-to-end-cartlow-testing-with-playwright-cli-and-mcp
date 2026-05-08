import pytest
from playwright.sync_api import Page

BASE_URL = "https://stage.cartlow.com/uae/en"
VALID_EMAIL = "muhammad.akmal@cartlow.com"
VALID_PASSWORD = "Test!123"


def open_login_modal(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    for _ in range(15):
        try:
            page.evaluate(
                "document.querySelector('#app').__vue_app__.config.globalProperties.$emitter.emit('open-customer-auth-modal')"
            )
            page.locator("#login-email").wait_for(state="visible", timeout=3000)
            page.wait_for_timeout(500)
            page.locator("#login-email").evaluate("el => el.focus()")
            if page.locator("#login-email").evaluate("el => document.activeElement === el"):
                page.wait_for_timeout(300)
                return
        except Exception:
            page.wait_for_timeout(1500)


def do_login(page: Page, email: str, password: str):
    open_login_modal(page)
    page.locator("#login-email").fill(email)
    page.locator("#login-password").fill(password)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Sign In')").first.click()
    page.wait_for_timeout(5000)


# ── Positive ──────────────────────────────────────────────────────────────────

def test_valid_login(page: Page):
    """Valid credentials — user logs in successfully."""
    do_login(page, VALID_EMAIL, VALID_PASSWORD)
    body = page.locator("body").inner_text().lower()
    assert "account" in body and "sign in" not in page.locator("header, nav").first.inner_text().lower()
    print("✅ Valid login — user is logged in")


def test_logout(page: Page):
    """Login then logout via Account dropdown — returns to logged-out state."""
    do_login(page, VALID_EMAIL, VALID_PASSWORD)
    page.wait_for_timeout(2000)

    # Hover over Account span to reveal dropdown (group-hover:block)
    account = page.locator("span[aria-label='Profile']:has-text('Account')").first
    box = account.bounding_box()
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.wait_for_timeout(1000)

    page.locator("a:has-text('Logout')").first.click()
    page.wait_for_timeout(4000)

    # After logout: hovering Account no longer shows Logout in dropdown
    account = page.locator("span[aria-label='Profile']:has-text('Account')").first
    box = account.bounding_box()
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.wait_for_timeout(1000)
    assert page.locator("a:has-text('Logout')").count() == 0 or \
        not page.locator("a:has-text('Logout')").first.is_visible()
    print("✅ Logout successful")


# ── Negative ──────────────────────────────────────────────────────────────────

def test_empty_credentials(page: Page):
    """Sign In button must be disabled when both fields are empty."""
    open_login_modal(page)
    assert page.locator("button:has-text('Sign In')").first.get_attribute("disabled") is not None
    print("✅ Empty credentials — Sign In is disabled")


def test_empty_email(page: Page):
    """Sign In button must be disabled when email is empty."""
    open_login_modal(page)
    page.locator("#login-password").fill(VALID_PASSWORD, force=True)
    page.wait_for_timeout(500)
    assert page.locator("button:has-text('Sign In')").first.get_attribute("disabled") is not None
    print("✅ Empty email — Sign In is disabled")


def test_empty_password(page: Page):
    """Sign In button must be disabled when password is empty."""
    open_login_modal(page)
    page.locator("#login-email").fill(VALID_EMAIL, force=True)
    page.wait_for_timeout(500)
    assert page.locator("button:has-text('Sign In')").first.get_attribute("disabled") is not None
    print("✅ Empty password — Sign In is disabled")


def test_invalid_email_format(page: Page):
    """Sign In button must be disabled for invalid email format."""
    open_login_modal(page)
    page.locator("#login-email").fill("not-an-email", force=True)
    page.locator("#login-password").fill(VALID_PASSWORD, force=True)
    page.wait_for_timeout(500)
    assert page.locator("button:has-text('Sign In')").first.get_attribute("disabled") is not None
    print("✅ Invalid email format — Sign In is disabled")


def test_invalid_password(page: Page):
    """Wrong password shows an error message."""
    do_login(page, VALID_EMAIL, "WrongPass999!")
    body = page.locator("body").inner_text().lower()
    assert any(k in body for k in ["invalid", "incorrect", "wrong", "error", "failed", "credentials"])
    print("✅ Invalid password — error shown")


def test_invalid_email(page: Page):
    """Non-existent email shows an error message."""
    do_login(page, "nonexistent_xyz_999@cartlow.com", VALID_PASSWORD)
    body = page.locator("body").inner_text().lower()
    assert any(k in body for k in ["invalid", "incorrect", "wrong", "error", "not found", "credentials"])
    print("✅ Invalid email — error shown")
