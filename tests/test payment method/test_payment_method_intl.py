import pytest
from playwright.sync_api import Page

BASE_URL      = "https://stage.cartlow.com/uae/en"
INTL_URL      = "https://stage.cartlow.com/intl/en"
EMAIL         = "muhammad.akmal@cartlow.com"
PASSWORD      = "Test!123"
CHECKOUT_CARD = "4242424242424242"
EXPIRY        = "1133"
CVV           = "123"
CARDHOLDER    = "Test"
BANK_PASSWORD = "Checkout1!"
NOON_CARD     = "4000000000002503"
NOON_EXPIRY   = "11/33"
NOON_CVV      = "123"
NOON_AUTH     = "1234"



# ── Helpers ───────────────────────────────────────────────────────────────────

def login_and_switch_intl(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    for _ in range(15):
        try:
            page.evaluate("document.querySelector('#app').__vue_app__.config.globalProperties.$emitter.emit('open-customer-auth-modal')")
            page.locator("#login-email").wait_for(state="visible", timeout=3000)
            page.wait_for_timeout(500)
            page.locator("#login-email").evaluate("el => el.focus()")
            if page.locator("#login-email").evaluate("el => document.activeElement === el"):
                break
        except: page.wait_for_timeout(1500)
    page.locator("#login-email").fill(EMAIL)
    page.locator("#login-password").fill(PASSWORD)
    page.wait_for_timeout(500)
    page.locator("button:has-text('Sign In')").first.click()
    page.wait_for_timeout(6000)
    print("✅ Logged in")

    # Switch to INTL channel
    page.locator("button:has-text('UAE')").first.click()
    page.wait_for_timeout(1500)
    page.locator("span.cursor-pointer:has-text('INTL')").first.click()
    page.wait_for_timeout(8000)
    page.context.add_cookies([{"name": "__selected_country", "value": "intl", "domain": "stage.cartlow.com", "path": "/"}])
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_selector("a[href*='product-detail']", state="attached", timeout=20000)
    page.wait_for_timeout(3000)
    print("✅ Switched to INTL")


def ensure_intl_cart_has_item(page: Page):
    page.goto(f"{INTL_URL}/checkout/cart", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    has_items = page.locator("a[href*='checkout/onepage']").count() > 0
    if has_items:
        print("  Cart has items ✅"); return
    print("  Cart empty — adding product...")
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_selector("a[href*='product-detail']", state="attached", timeout=20000)
    page.wait_for_timeout(3000)
    products = list(dict.fromkeys(page.evaluate(
        "() => [...document.querySelectorAll('a[href*=product-detail]')].map(a => a.href)"
    )))
    import re
    for link in products:
        page.goto(link, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        body = page.locator("body").inner_text()
        prices = re.findall(r'\$\s*([\d.]+)', body)
        if prices and float(prices[0]) < 1.0:
            continue
        if "View Cart" in body:
            print(f"  In cart: {page.title()}"); return
        # Scroll down to reveal Add to Cart button
        for _ in range(15):
            page.mouse.wheel(0, 200)
            page.wait_for_timeout(300)
        page.wait_for_timeout(1000)
        body = page.locator("body").inner_text()
        if "View Cart" in body:
            print(f"  In cart: {page.title()}"); return
        # Try Add to Cart button first (visible after scroll)
        for btn_text in ["Add To Cart", "Add to Cart"]:
            btn = page.locator(f"button:has-text('{btn_text}')").first
            if btn.count() and btn.is_visible():
                btn.click(force=True)
                page.wait_for_timeout(4000)
                if "View Cart" in page.locator("body").inner_text():
                    print(f"  Added: {page.title()}"); return
        # Fallback: Keep it for Yourself
        keep_btn = page.locator("div.cursor-pointer:has-text('Keep it for Yourself')").first
        if keep_btn.count() and keep_btn.is_visible():
            keep_btn.click()
            page.wait_for_timeout(3000)
            if "View Cart" in page.locator("body").inner_text():
                print(f"  Added: {page.title()}"); return


def go_to_intl_checkout(page: Page):
    page.goto(f"{INTL_URL}/checkout/cart", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    # Use the visible Checkout link (last one is the visible one)
    links = page.locator("a[href*='checkout/onepage']")
    if links.count() > 0:
        links.last.click()
    else:
        # Direct navigation fallback
        page.goto(f"{INTL_URL}/checkout/onepage", wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    assert "onepage" in page.url, f"Expected checkout page, got: {page.url}"


def detect_payment_methods(page: Page) -> list[dict]:
    go_to_intl_checkout(page)
    print(f"  Checkout URL: {page.url}")
    methods = page.evaluate("""
        () => [...document.querySelectorAll('input[type=radio][name="payment[method]"]')]
            .map(el => {
                const label = document.querySelector(`label[for="${el.id}"]`);
                return {
                    id: el.id,
                    label: label ? label.innerText.trim().split('\\n')[0].substring(0, 60) : el.id
                };
            })
    """)
    print(f"\n📋 Detected {len(methods)} payment method(s):")
    for m in methods:
        print(f"   - {m['id']}: {m['label']}")
    return methods


def select_payment_method(page: Page, method_id: str):
    page.evaluate(f"document.getElementById('{method_id}').click()")
    page.wait_for_timeout(1000)
    assert page.evaluate(f"document.getElementById('{method_id}').checked"), \
        f"Payment method '{method_id}' was not selected"


def place_order(page: Page) -> str:
    page.locator("button:has-text('Place Order')").first.click()
    page.wait_for_timeout(10000)
    url = page.url
    print(f"   Gateway URL: {url}")
    return url


def _handle_3ds_and_wait(page: Page):
    page.wait_for_timeout(8000)
    auth_filled = False
    for _ in range(12):
        if "stage.cartlow.com" in page.url and "checkout/onepage" not in page.url:
            print("  No 3DS needed — on Cartlow"); break
        for frame in page.frames:
            try:
                for inp in frame.query_selector_all("input"):
                    if not inp.is_visible(): continue
                    t  = (inp.get_attribute("type") or "").lower()
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    nm = (inp.get_attribute("name") or "").lower()
                    if t == "password" or any(k in ph+nm for k in ["password","code","auth","otp"]):
                        inp.fill(BANK_PASSWORD)
                        auth_filled = True
                        print(f"  3DS filled (frame: {frame.url[:60]})"); break
            except: continue
            if auth_filled: break
        if auth_filled:
            page.wait_for_timeout(1000)
            submitted = False
            for lbl in ["Continue","Submit","Authorize","Confirm","OK","Proceed"]:
                for frame in page.frames:
                    try:
                        btn = frame.locator(f"button:has-text('{lbl}')").first
                        if btn.is_visible():
                            btn.click(); submitted = True
                            print(f"  3DS submitted via: {lbl}"); break
                    except: continue
                if submitted: break
            if not submitted:
                page.keyboard.press("Enter")
                print("  3DS submitted via Enter")
            page.wait_for_timeout(10000); break
        page.wait_for_timeout(5000)

    page.wait_for_url("**/stage.cartlow.com/**", timeout=45000)
    page.wait_for_timeout(5000)
    for _ in range(10):
        if any(k in page.url for k in ["success", "order"]): break
        page.wait_for_timeout(3000)
    assert any(k in page.url for k in ["success", "order", "payment/wait"]), \
        f"Expected success page, got: {page.url}"


def handle_checkout_com(page: Page):
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
    page.wait_for_function(
        "() => [...document.querySelectorAll('button')].some(b => /^pay\\s/i.test(b.innerText.trim()) && b.offsetParent !== null && !b.disabled)",
        timeout=20000
    )
    for btn in page.locator("button").all():
        try:
            txt = btn.inner_text().strip()
            if txt.lower().startswith("pay ") and btn.is_visible():
                btn.click(); break
        except: continue
    _handle_3ds_and_wait(page)


# ── Test ──────────────────────────────────────────────────────────────────────



def handle_noonpay(page):
    """NoonPay: fill card details and handle bank auth page (OTP = 1234)."""
    page.wait_for_timeout(4000)
    # Card number
    for sel in ["input[name='cardNumber']", "input[placeholder*='card' i]", "input[id*='card-number' i]"]:
        inp = page.locator(sel).first
        if inp.count() and inp.is_visible():
            inp.click(); inp.type(NOON_CARD, delay=80); break
    # Expiry
    for sel in ["input[name='expiryDate']", "input[placeholder*='MM' i]", "input[id*='expiry' i]"]:
        inp = page.locator(sel).first
        if inp.count() and inp.is_visible():
            inp.click(); inp.type(NOON_EXPIRY, delay=100); break
    # CVV
    for sel in ["input[name='cvv']", "input[placeholder*='CVV' i]", "input[id*='cvv' i]"]:
        inp = page.locator(sel).first
        if inp.count() and inp.is_visible():
            inp.fill(NOON_CVV); break
    page.wait_for_timeout(1000)
    # Click Pay / Submit
    for btn_text in ["Pay", "Submit", "Confirm", "Continue"]:
        btn = page.locator(f"button:has-text('{btn_text}')").first
        if btn.count() and btn.is_visible() and btn.get_attribute("disabled") is None:
            btn.click(); break
    page.wait_for_timeout(8000)
    # Bank auth page — enter 1234
    for frame in [page] + list(page.frames):
        try:
            for sel in ["input[name='otp']", "input[name='password']", "input[type='tel']",
                        "input[placeholder*='OTP' i]", "input[placeholder*='code' i]", "input[placeholder*='auth' i]"]:
                inp = frame.locator(sel).first
                if inp.count() and inp.is_visible():
                    inp.fill(NOON_AUTH)
                    print(f"  NoonPay auth filled")
                    break
        except: continue
    page.wait_for_timeout(500)
    for btn_text in ["Submit", "Confirm", "Continue", "Verify", "OK"]:
        try:
            btn = page.locator(f"button:has-text('{btn_text}')").first
            if btn.count() and btn.is_visible():
                btn.click(); break
        except: continue
    page.wait_for_timeout(10000)
    print(f"  NoonPay — URL after auth: {page.url}")

def test_payment_methods_intl(page: Page):
    """Dynamically detect and test each payment method on the INTL checkout page."""
    page.set_viewport_size({"width": 1280, "height": 800})

    login_and_switch_intl(page)
    ensure_intl_cart_has_item(page)
    methods = detect_payment_methods(page)
    assert methods, "No payment methods found on INTL checkout page"

    results = {}

    for method in methods:
        mid   = method["id"]
        label = method["label"]
        print(f"\n{'='*50}")
        print(f"💳 Testing: {label} ({mid})")

        try:
            ensure_intl_cart_has_item(page)
            go_to_intl_checkout(page)
            select_payment_method(page, mid)
            print(f"   ✅ Selected: {label}")

            gateway_url = place_order(page)

            if "checkout.com" in gateway_url or "pay.sandbox" in gateway_url:
                print("   💳 Checkout.com gateway")
                handle_checkout_com(page)
                results[mid] = "✅ PASSED"

            elif "coinpayment" in gateway_url.lower() or "coinpayment" in mid.lower():
                assert "checkout/onepage" not in gateway_url
                print(f"   ✅ Crypto gateway reached")
                results[mid] = "✅ PASSED (gateway reached)"

            else:
                assert "checkout/onepage" not in gateway_url, f"Still on checkout: {gateway_url}"
                results[mid] = f"✅ PASSED (→ {gateway_url[:60]})"

            print(f"   {results[mid]}")

        except Exception as e:
            results[mid] = f"❌ FAILED: {str(e)[:100]}"
            print(f"   {results[mid]}")

    # Summary
    print(f"\n{'='*50}")
    print("📊 INTL Payment Method Test Results:")
    for mid, result in results.items():
        lbl = next((m["label"] for m in methods if m["id"] == mid), mid)
        print(f"   {result} — {lbl}")

    failed = [k for k, v in results.items() if "FAILED" in v]
    assert not failed, f"Failed payment methods: {failed}"
