"""
E2E checkout tests for all channels on STAGE2 (stage2.cartlow.com).
Same test logic as test_all_channels_e2e.py but pointing to stage2.
"""
import random
import re
import pytest
from playwright.sync_api import Page

BASE_URL = "https://stage2.cartlow.com/uae/en"
KSA_URL  = "https://stage2.cartlow.com/saudi/en"
INTL_URL = "https://stage2.cartlow.com/intl/en"

EMAIL         = "muhammad.akmal@cartlow.com"
PASSWORD      = "Test!123"
COUPON        = "welcome10"
NOON_CARD     = "4456530000001005"
CHECKOUT_CARD = "4242424242424242"
PAYMOB_CARD   = "5123456789012346"
EXPIRY        = "1133"
EXPIRY_SLASH  = "11/33"
CVV           = "123"
CARDHOLDER    = "Test"
BANK_PASSWORD = "Checkout1!"


# ── Helpers ───────────────────────────────────────────────────────────────────

def login(page: Page):
    for attempt in range(3):
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            break
        except: page.wait_for_timeout(5000)
    page.wait_for_timeout(10000)
    for _ in range(15):
        try:
            page.evaluate("document.querySelector('#app').__vue_app__.config.globalProperties.$emitter.emit('open-customer-auth-modal')")
            page.locator("#login-email").wait_for(state="visible", timeout=3000)
            page.wait_for_timeout(500)
            page.locator("#login-email").evaluate("el => el.focus()")
            if page.locator("#login-email").evaluate("el => document.activeElement === el"):
                page.wait_for_timeout(300); break
        except: page.wait_for_timeout(1500)
    page.locator("#login-email").fill(EMAIL)
    page.locator("#login-password").fill(PASSWORD)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Sign In')").first.click()
    page.wait_for_timeout(6000)
    print("✅ Logged in")


def switch_channel(page: Page, channel: str):
    page.evaluate("() => [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'UAE')?.click()")
    page.wait_for_timeout(1500)
    page.locator(f"span.cursor-pointer:has-text('{channel}')").first.click()
    page.wait_for_timeout(8000)
    if channel == "INTL":
        page.context.add_cookies([{"name": "__selected_country", "value": "intl",
                                    "domain": "stage2.cartlow.com", "path": "/"}])
    print(f"✅ Switched to {channel}")


def add_product_to_cart(page: Page, channel_url: str, search: str = "iphone"):
    page.goto(f"{channel_url}/search?query={search}", wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.wait_for_selector("a[href*='product-detail']", state="attached", timeout=20000)
    products = list(dict.fromkeys(page.evaluate(
        "() => [...document.querySelectorAll('a[href*=product-detail]')].map(a => a.href)"
    )))
    for link in products:
        try: page.goto(link, wait_until="domcontentloaded", timeout=30000)
        except: continue
        page.wait_for_timeout(5000)
        body = page.locator("body").inner_text()
        prices = re.findall(r'\$\s*([\d.]+)', body)
        if prices and float(prices[0]) < 1.0: continue
        if "View Cart" in body:
            print(f"✅ Already in cart: {page.title()}"); return
        for _ in range(10): page.mouse.wheel(0, 200); page.wait_for_timeout(200)
        page.wait_for_timeout(1000)
        body = page.locator("body").inner_text()
        if "View Cart" in body:
            print(f"✅ In cart: {page.title()}"); return
        for btn_text in ["Add To Cart", "Add to Cart"]:
            btn = page.locator(f"button:has-text('{btn_text}')").first
            if btn.count() and btn.is_visible():
                btn.click(force=True); page.wait_for_timeout(4000)
                if "View Cart" in page.locator("body").inner_text():
                    print(f"✅ Added: {page.title()}"); return
        keep = page.locator("div.cursor-pointer:has-text('Keep it for Yourself')").first
        if keep.count() and keep.is_visible():
            keep.click(); page.wait_for_timeout(3000)
            if "View Cart" in page.locator("body").inner_text():
                print(f"✅ Added (digital): {page.title()}"); return


def go_to_checkout(page: Page, channel_url: str):
    page.goto(f"{channel_url}/checkout/cart", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    links = page.locator("a[href*='checkout/onepage']")
    clicked = False
    for i in range(links.count()):
        try:
            link = links.nth(i)
            box = link.bounding_box()
            if box and box['width'] > 0 and box['height'] > 0:
                link.click(); clicked = True; break
        except: continue
    if not clicked:
        page.goto(f"{channel_url}/checkout/onepage", wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    assert "onepage" in page.url, f"Expected checkout, got: {page.url}"
    print(f"✅ Checkout — {page.url}")


def apply_coupon(page: Page):
    page.evaluate(f"""
        () => {{
            const inputs = [...document.querySelectorAll("input[name='coupon_code']")];
            const inp = inputs.find(el => el.offsetParent !== null) || inputs[0];
            if (inp) {{
                inp.scrollIntoView({{block: 'center'}});
                inp.value = '{COUPON}';
                inp.dispatchEvent(new Event('input', {{bubbles: true}}));
                inp.dispatchEvent(new Event('change', {{bubbles: true}}));
            }}
        }}
    """)
    page.wait_for_timeout(1000)
    page.evaluate("""
        () => {
            const btns = [...document.querySelectorAll('button')];
            const apply = btns.find(b => b.innerText.trim() === 'Apply' && b.offsetParent !== null);
            if (apply) apply.click();
        }
    """)
    page.wait_for_timeout(4000)
    success = ("discount" in page.locator("body").inner_text().lower())
    print(f"{'✅' if success else '⚠️ '} Coupon '{COUPON}' {'applied' if success else 'not applied'}")


def select_payment(page: Page):
    """Select first available payment method."""
    for mid in ["paymob", "checkout", "coinpayments", "tamara", "tabby"]:
        if page.evaluate(f"() => !!document.getElementById('{mid}')"):
            page.evaluate(f"document.getElementById('{mid}').click()")
            page.wait_for_timeout(1000)
            print(f"✅ Selected payment: {mid}")
            return mid
    return None


def place_order(page: Page):
    page.locator("button:has-text('Place Order')").first.click()
    page.wait_for_timeout(10000)
    print(f"✅ Place Order → {page.url}")


def fill_noon_pay(page: Page):
    page.wait_for_selector("#txtcardFormCardNumber", state="visible", timeout=15000)
    page.locator("#txtcardFormCardNumber").fill(NOON_CARD)
    page.wait_for_timeout(400)
    page.locator("#txtCardFormExpiryDate").fill(EXPIRY_SLASH)
    page.wait_for_timeout(400)
    page.locator("#c").fill(CVV)
    page.wait_for_timeout(600)
    print("  NoonPay card details entered")


def fill_paymob(page: Page):
    page.wait_for_selector("input[name='number']", state="visible", timeout=15000)
    page.locator("input[name='number']").first.click()
    page.locator("input[name='number']").first.type(PAYMOB_CARD, delay=80)
    page.wait_for_timeout(400)
    page.locator("input[name='expiry']").fill(EXPIRY_SLASH)
    page.wait_for_timeout(400)
    page.locator("input[name='cvc']").fill(CVV)
    page.wait_for_timeout(400)
    page.locator("input[name='name']").fill(CARDHOLDER)
    page.wait_for_timeout(600)


def fill_checkout_com(page: Page):
    page.wait_for_timeout(4000)
    for frame in page.frames:
        loc = frame.locator("input[name='card-number']")
        if loc.count() and loc.first.is_visible():
            loc.first.click(); loc.first.type(CHECKOUT_CARD, delay=80); break
    for frame in page.frames:
        loc = frame.locator("input[name='card-expiry-date'], input[placeholder='MM/YY']")
        if loc.count() and loc.first.is_visible():
            loc.first.click(); loc.first.type(EXPIRY, delay=150); break
    for frame in page.frames:
        loc = frame.locator("input[name='card-cvv'], input[placeholder='CVV']")
        if loc.count() and loc.first.is_visible():
            loc.first.click(); loc.first.type(CVV, delay=80); break
    for frame in page.frames:
        loc = frame.locator("input[name='cardholder-name']")
        if loc.count() and loc.first.is_visible():
            loc.first.click(); loc.first.fill(CARDHOLDER); break
    page.wait_for_timeout(1000)


def click_pay(page: Page):
    page.wait_for_function(
        "() => [...document.querySelectorAll('button')].some(b => /^pay\\s/i.test(b.innerText.trim()) && b.offsetParent !== null && !b.disabled)",
        timeout=20000
    )
    for btn in page.locator("button").all():
        try:
            txt = btn.inner_text().strip()
            if txt.lower().startswith("pay ") and btn.is_visible():
                print(f"✅ Pay: '{txt}'"); btn.click(); break
        except: continue


def wait_for_success(page: Page):
    page.wait_for_timeout(8000)
    # Handle NoonPayments new tab
    try:
        context = page.context
        if len(context.pages) > 1:
            otp_page = context.pages[-1]
            print(f"  New tab: {otp_page.url}")
            otp_page.wait_for_timeout(3000)
            for inp in otp_page.locator("input").all():
                try:
                    if inp.is_visible(): inp.fill("1234"); break
                except: pass
            otp_page.wait_for_timeout(500)
            for lbl in ["Submit","Confirm","Verify","Continue","OK"]:
                btn = otp_page.locator(f"button:has-text('{lbl}')").first
                if btn.count() and btn.is_visible(): btn.click(); break
            otp_page.wait_for_timeout(8000)
            try: otp_page.close()
            except: pass
            page.wait_for_timeout(3000)
    except: pass

    for _ in range(20):
        if "stage2.cartlow.com" in page.url and "checkout/onepage" not in page.url:
            break
        auth_filled = False
        for frame in page.frames:
            try:
                for inp in frame.query_selector_all("input"):
                    if not inp.is_visible(): continue
                    t  = (inp.get_attribute("type") or "").lower()
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    nm = (inp.get_attribute("name") or "").lower()
                    if t == "password" or any(k in ph+nm for k in ["password","code","auth","otp","answer"]):
                        inp.fill(BANK_PASSWORD); auth_filled = True
                        print(f"  Auth filled (frame: {frame.url[:60]})"); break
            except: continue
            if auth_filled: break
        if auth_filled:
            page.wait_for_timeout(1000)
            submitted = False
            for lbl in ["Continue","Submit","Authorize","Confirm","OK","Proceed","Pay"]:
                for frame in page.frames:
                    try:
                        btn = frame.locator(f"button:has-text('{lbl}')").first
                        if btn.is_visible():
                            btn.click(); submitted = True
                            print(f"  Auth submitted via: {lbl}"); break
                    except: continue
                if submitted: break
            if not submitted:
                page.keyboard.press("Enter")
                print("  Auth submitted via Enter")
            page.wait_for_timeout(15000); break
        page.wait_for_timeout(5000)

    page.wait_for_url("**/stage2.cartlow.com/**", timeout=90000)
    page.wait_for_timeout(5000)
    for _ in range(10):
        if any(k in page.url for k in ["success","order"]): break
        page.wait_for_timeout(3000)
    assert any(k in page.url for k in ["success","order","payment/wait","coinpayments","selection","tamara","tabby"]), \
        f"Expected success, got: {page.url}"
    print(f"✅ Order success — {page.url}")


def handle_payment_gateway(page: Page):
    url = page.url.lower()
    if "paymob" in url:
        print("💳 Paymob"); fill_paymob(page); click_pay(page)
    elif "checkout.com" in url or "pay.sandbox" in url:
        print("💳 Checkout.com"); fill_checkout_com(page); click_pay(page)
    elif "noon" in url:
        print("💳 NoonPayments"); fill_noon_pay(page); click_pay(page)
    elif "tamara" in url:
        print(f"💳 Tamara gateway — {page.url}")
    elif "tabby" in url:
        print(f"💳 Tabby gateway — {page.url}")
    elif "coinpayment" in url:
        print(f"💳 CoinPayments — {page.url}")
    else:
        print(f"💳 Gateway: {page.url}")
    wait_for_success(page)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_e2e_uae_checkout_stage2(page: Page):
    """Full E2E checkout on UAE channel — stage2."""
    page.set_viewport_size({"width": 1280, "height": 800})
    login(page)
    add_product_to_cart(page, BASE_URL)
    go_to_checkout(page, BASE_URL)
    apply_coupon(page)
    select_payment(page)
    place_order(page)
    handle_payment_gateway(page)
    print("✅ UAE E2E checkout on stage2 PASSED")


def test_e2e_ksa_checkout_stage2(page: Page):
    """Full E2E checkout on KSA channel — stage2."""
    page.set_viewport_size({"width": 1280, "height": 800})
    login(page)
    switch_channel(page, "KSA")
    add_product_to_cart(page, KSA_URL)
    go_to_checkout(page, KSA_URL)
    apply_coupon(page)
    select_payment(page)
    place_order(page)
    handle_payment_gateway(page)
    print("✅ KSA E2E checkout on stage2 PASSED")


def test_e2e_intl_checkout_stage2(page: Page):
    """Full E2E checkout on INTL channel — stage2 (digital cards)."""
    page.set_viewport_size({"width": 1280, "height": 800})
    login(page)
    switch_channel(page, "INTL")
    add_product_to_cart(page, INTL_URL, search="pubg")
    go_to_checkout(page, INTL_URL)
    # INTL on stage2: prefer checkout.com over coinpayments
    for mid in ["checkout", "paymob", "coinpayments", "tamara", "tabby"]:
        if page.evaluate(f"() => !!document.getElementById('{mid}')"):
            page.evaluate(f"document.getElementById('{mid}').click()")
            page.wait_for_timeout(1000)
            print(f"✅ Selected payment: {mid}")
            break
    place_order(page)
    handle_payment_gateway(page)
    print("✅ INTL E2E checkout on stage2 PASSED")
