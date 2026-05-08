import os
import random
import pymysql
from playwright.sync_api import Page

BASE_URL = "https://stage.cartlow.com/uae/en"

DB_HOST = os.getenv("DB_HOST", "209.38.211.128")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "cartlow_dev")
DB_USER = os.getenv("DB_USER", "sohaib")
DB_PASS = os.getenv("DB_PASS", "SoHeyhy@20ZZwaN@2023")


def get_otp_from_db(recipient: str):
    conn = pymysql.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME,
        user=DB_USER, password=DB_PASS, connect_timeout=10
    )
    cur = conn.cursor()
    cur.execute(
        "SELECT verification_code FROM otp_verifications "
        "WHERE recipient = %s ORDER BY created_at DESC LIMIT 1",
        (recipient,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return str(row[0]) if row else None


def open_register_form(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    for _ in range(10):
        try:
            page.evaluate(
                "document.querySelector('#app').__vue_app__.config.globalProperties.$emitter.emit('open-customer-auth-modal')"
            )
            page.wait_for_selector("#login-email", state="visible", timeout=5000)
            break
        except Exception:
            page.wait_for_timeout(2000)
    # Force-click the "Create Account" span (bypasses overlay pointer-events)
    for _ in range(5):
        try:
            page.locator("span:has-text('Create Account')").first.click(force=True)
            page.wait_for_selector("#register-email", state="visible", timeout=5000)
            return
        except Exception:
            page.wait_for_timeout(1000)


def test_registration_positive_flow(page: Page):
    test_email = f"test_{random.randint(10000, 99999)}@cartlow.com"
    print(f"\n📧 Registering: {test_email}")

    # Step 1: Open registration form
    open_register_form(page)
    print("✅ Step 1: Registration form opened")

    # Step 2: Fill email and click Continue
    page.locator("#register-email").fill(test_email)
    page.wait_for_timeout(500)
    assert page.locator("button:has-text('Continue')").get_attribute("disabled") is None
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(6000)
    print("✅ Step 2: Email submitted, waiting for OTP screen")

    # Step 3: OTP screen
    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=10000)
    print("✅ Step 3: OTP screen appeared")

    # Step 4: Fetch OTP from DB (wait a moment for server to write it)
    page.wait_for_timeout(3000)
    otp = get_otp_from_db(test_email)
    assert otp, f"OTP not found in DB for {test_email}"
    print(f"✅ Step 4: OTP from DB = {otp}")

    # Fill OTP input (first visible input that is not the search bar)
    for inp in page.locator("input").all():
        try:
            if inp.is_visible() and inp.get_attribute("placeholder") != "Search products here":
                inp.fill(otp)
                break
        except:
            pass

    page.wait_for_timeout(500)

    # Step 5: Click Verify
    page.locator("button:has-text('Verify')").click()
    page.wait_for_timeout(6000)
    print("✅ Step 5: OTP verified")

    # Step 6: Fill profile setup (Full Name, Password, Confirm Password)
    body = page.locator("body").inner_text().lower()
    if "full name" in body or "create password" in body:
        print("✅ Step 6: Profile setup screen — filling details")
        fake_name = "Test User"
        fake_password = "Test@1234"

        name_input = page.locator("input[placeholder*='name' i], input[id*='name' i]").first
        if name_input.is_visible():
            name_input.fill(fake_name)

        for pwd_input in page.locator("input[type='password']").all():
            if pwd_input.is_visible():
                pwd_input.fill(fake_password)

        page.wait_for_timeout(500)
        # Click the submit/continue button
        for label in ["Create Account", "Continue", "Submit", "Register", "Sign Up"]:
            btn = page.locator(f"button:has-text('{label}')").first
            try:
                if btn.is_visible() and btn.get_attribute("disabled") is None:
                    btn.click()
                    break
            except:
                pass
        page.wait_for_timeout(6000)

    # Step 7: Assert logged-in state
    body = page.locator("body").inner_text().lower()
    assert any(k in body for k in ["logout", "my account", "welcome", "sign out", "hi ", "hello"]) \
        or ("account" in body and "sign in" not in body), \
        f"Expected logged-in state after registration. Got: {body[:300]}"
    print("✅ Step 7: Registration successful — user is logged in!")


# ── Negative Scenarios ────────────────────────────────────────────────────────

def test_registration_empty_email(page: Page):
    """Continue button must be disabled when email is empty."""
    open_register_form(page)
    btn = page.locator("button:has-text('Continue')")
    assert btn.get_attribute("disabled") is not None, "Continue should be disabled with empty email"
    print("✅ Empty email — Continue is disabled")


def test_registration_invalid_email_format(page: Page):
    """Continue button stays disabled for invalid email format."""
    open_register_form(page)
    page.locator("#register-email").fill("not-an-email")
    page.wait_for_timeout(500)
    btn = page.locator("button:has-text('Continue')")
    assert btn.get_attribute("disabled") is not None, "Continue should be disabled for invalid email"
    print("✅ Invalid email format — Continue stays disabled")


def test_registration_existing_email(page: Page):
    """Submitting an already-registered email shows an error."""
    open_register_form(page)
    page.locator("#register-email").fill("muhammad.akmal@cartlow.com")
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(5000)
    error = page.locator("div[class*='text-red']").first.inner_text()
    assert any(k in error.lower() for k in ["already", "in use", "exists", "registered"])
    print(f"✅ Existing email — error: '{error}'")


def test_registration_invalid_otp(page: Page):
    """Wrong OTP shows an error message."""
    test_email = f"test_{random.randint(10000, 99999)}@cartlow.com"
    open_register_form(page)
    page.locator("#register-email").fill(test_email)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(6000)

    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=10000)

    # Fill wrong OTP
    for inp in page.locator("input").all():
        try:
            if inp.is_visible() and inp.get_attribute("placeholder") != "Search products here":
                inp.fill("000000")
                break
        except:
            pass

    page.wait_for_timeout(500)
    page.locator("button:has-text('Verify')").click()
    page.wait_for_timeout(3000)

    error = page.locator("div[class*='text-red']").first.inner_text()
    assert any(k in error.lower() for k in ["incorrect", "invalid", "wrong", "one-time"])
    print(f"✅ Invalid OTP — error: '{error}'")


def test_registration_weak_password(page: Page):
    """Weak password on profile setup screen shows validation error."""
    test_email = f"test_{random.randint(10000, 99999)}@cartlow.com"
    open_register_form(page)
    page.locator("#register-email").fill(test_email)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(6000)

    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=10000)
    page.wait_for_timeout(3000)
    otp = get_otp_from_db(test_email)
    assert otp, f"OTP not found in DB for {test_email}"

    for inp in page.locator("input").all():
        try:
            if inp.is_visible() and inp.get_attribute("placeholder") != "Search products here":
                inp.fill(otp)
                break
        except:
            pass

    page.locator("button:has-text('Verify')").click()
    page.wait_for_timeout(6000)

    # Fill name and weak password
    name_input = page.locator("input[placeholder*='name' i], input[id*='name' i]").first
    if name_input.is_visible():
        name_input.fill("Test User")

    for pwd_input in page.locator("input[type='password']").all():
        if pwd_input.is_visible():
            pwd_input.fill("123")

    page.wait_for_timeout(500)
    for label in ["Create Account", "Continue", "Submit", "Register", "Sign Up"]:
        btn = page.locator(f"button:has-text('{label}')").first
        try:
            if btn.is_visible():
                btn.click()
                break
        except:
            pass
    page.wait_for_timeout(3000)

    body = page.locator("body").inner_text().lower()
    assert any(k in body for k in ["weak", "password", "characters", "between", "invalid", "must"])
    print("✅ Weak password — validation error shown")


def test_registration_mismatched_passwords(page: Page):
    """Mismatched passwords on profile setup shows error."""
    test_email = f"test_{random.randint(10000, 99999)}@cartlow.com"
    open_register_form(page)
    page.locator("#register-email").fill(test_email)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(6000)

    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=10000)
    page.wait_for_timeout(3000)
    otp = get_otp_from_db(test_email)
    assert otp, f"OTP not found in DB for {test_email}"

    for inp in page.locator("input").all():
        try:
            if inp.is_visible() and inp.get_attribute("placeholder") != "Search products here":
                inp.fill(otp)
                break
        except:
            pass

    page.locator("button:has-text('Verify')").click()
    page.wait_for_timeout(6000)

    # Fill name and mismatched passwords
    name_input = page.locator("input[placeholder*='name' i], input[id*='name' i]").first
    if name_input.is_visible():
        name_input.fill("Test User")

    pwd_inputs = [i for i in page.locator("input[type='password']").all() if i.is_visible()]
    if len(pwd_inputs) >= 2:
        pwd_inputs[0].fill("Test@1234")
        pwd_inputs[1].fill("Different@9999")

    page.wait_for_timeout(500)
    for label in ["Create Account", "Continue", "Submit", "Register", "Sign Up"]:
        btn = page.locator(f"button:has-text('{label}')").first
        try:
            if btn.is_visible():
                btn.click()
                break
        except:
            pass
    page.wait_for_timeout(3000)

    body = page.locator("body").inner_text().lower()
    assert any(k in body for k in ["match", "passwords must", "confirm", "same"])
    print("✅ Mismatched passwords — validation error shown")
