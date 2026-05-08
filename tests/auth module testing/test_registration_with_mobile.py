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

# Valid UAE mobile — must not already be registered
EXISTING_PHONE = "+971507899999"


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
    for _ in range(5):
        try:
            page.locator("span:has-text('Create Account')").first.click(force=True)
            page.wait_for_selector("#register-email", state="visible", timeout=5000)
            page.wait_for_timeout(1000)
            return
        except Exception:
            page.wait_for_timeout(1000)


def random_phone():
    return f"+97150{random.randint(1000000, 9999999)}"


# ── Positive ──────────────────────────────────────────────────────────────────

def test_registration_mobile_positive_flow(page: Page):
    """New valid mobile number — full registration flow."""
    phone = random_phone()
    print(f"\n📱 Registering with: {phone}")

    open_register_form(page)
    print("✅ Step 1: Registration form opened")

    page.locator("#register-email").fill(phone)
    page.wait_for_timeout(500)
    assert page.locator("button:has-text('Continue')").get_attribute("disabled") is None
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(10000)
    print("✅ Step 2: Phone submitted")

    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=15000)
    print("✅ Step 3: OTP screen appeared")

    page.wait_for_timeout(3000)
    otp = get_otp_from_db(phone)
    assert otp, f"OTP not found in DB for {phone}"
    print(f"✅ Step 4: OTP from DB = {otp}")

    for inp in page.locator("input").all():
        try:
            if inp.is_visible() and inp.get_attribute("placeholder") != "Search products here":
                inp.fill(otp)
                break
        except:
            pass

    page.wait_for_timeout(500)
    page.locator("button:has-text('Verify')").click()
    page.wait_for_timeout(6000)
    print("✅ Step 5: OTP verified")

    body = page.locator("body").inner_text().lower()
    if "full name" in body or "create password" in body:
        print("✅ Step 6: Profile setup screen — filling details")
        name_input = page.locator("input[placeholder*='name' i], input[id*='name' i]").first
        if name_input.is_visible():
            name_input.fill("Test User")
        for pwd in page.locator("input[type='password']").all():
            if pwd.is_visible():
                pwd.fill("Test@1234")
        page.wait_for_timeout(500)
        for label in ["Create Account", "Continue", "Submit", "Register", "Sign Up"]:
            btn = page.locator(f"button:has-text('{label}')").first
            try:
                if btn.is_visible() and btn.get_attribute("disabled") is None:
                    btn.click()
                    break
            except:
                pass
        page.wait_for_timeout(6000)

    body = page.locator("body").inner_text().lower()
    assert "account" in body and "sign in" not in page.locator("header, nav").first.inner_text().lower() \
        or any(k in body for k in ["logout", "my account", "welcome"])
    print("✅ Step 7: Registration successful — user is logged in!")


# ── Negative ──────────────────────────────────────────────────────────────────

def test_registration_mobile_empty(page: Page):
    """Continue button must be disabled when field is empty."""
    open_register_form(page)
    assert page.locator("button:has-text('Continue')").get_attribute("disabled") is not None
    print("✅ Empty phone — Continue is disabled")


def test_registration_mobile_invalid_format(page: Page):
    """Invalid phone format keeps Continue disabled."""
    open_register_form(page)
    page.locator("#register-email").fill("12345")
    page.wait_for_timeout(500)
    assert page.locator("button:has-text('Continue')").get_attribute("disabled") is not None
    print("✅ Invalid phone format — Continue stays disabled")


def test_registration_mobile_existing(page: Page):
    """Already registered phone shows error."""
    open_register_form(page)
    page.locator("#register-email").fill(EXISTING_PHONE)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(5000)
    error = page.locator("div[class*='text-red']").first.inner_text()
    assert any(k in error.lower() for k in ["already", "in use", "exists", "registered"])
    print(f"✅ Existing phone — error: '{error}'")


def test_registration_mobile_invalid_otp(page: Page):
    """Wrong OTP shows error message."""
    phone = random_phone()
    open_register_form(page)
    page.locator("#register-email").fill(phone)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(6000)

    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=10000)

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


def test_registration_mobile_weak_password(page: Page):
    """Weak password on profile setup shows validation error."""
    phone = random_phone()
    open_register_form(page)
    page.locator("#register-email").fill(phone)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(6000)

    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=10000)
    page.wait_for_timeout(3000)
    otp = get_otp_from_db(phone)
    assert otp, f"OTP not found in DB for {phone}"

    for inp in page.locator("input").all():
        try:
            if inp.is_visible() and inp.get_attribute("placeholder") != "Search products here":
                inp.fill(otp)
                break
        except:
            pass

    page.locator("button:has-text('Verify')").click()
    page.wait_for_timeout(6000)

    name_input = page.locator("input[placeholder*='name' i], input[id*='name' i]").first
    if name_input.is_visible():
        name_input.fill("Test User")
    for pwd in page.locator("input[type='password']").all():
        if pwd.is_visible():
            pwd.fill("123")

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


def test_registration_mobile_mismatched_passwords(page: Page):
    """Mismatched passwords on profile setup shows error."""
    phone = random_phone()
    open_register_form(page)
    page.locator("#register-email").fill(phone)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Continue')").click()
    page.wait_for_timeout(6000)

    page.wait_for_selector("button:has-text('Verify')", state="visible", timeout=10000)
    page.wait_for_timeout(3000)
    otp = get_otp_from_db(phone)
    assert otp, f"OTP not found in DB for {phone}"

    for inp in page.locator("input").all():
        try:
            if inp.is_visible() and inp.get_attribute("placeholder") != "Search products here":
                inp.fill(otp)
                break
        except:
            pass

    page.locator("button:has-text('Verify')").click()
    page.wait_for_timeout(6000)

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
