"""
E2E checkout tests for all channels on PRODUCTION.
Runs the full flow: login → channel → search → cart → checkout → payment gateway.
Stops before clicking Pay (no real charges).
"""
import re
import pytest
from playwright.sync_api import Page

BASE_URL = "https://www.cartlow.com/uae/en"
KSA_URL  = "https://www.cartlow.com/saudi/en"
INTL_URL = "https://www.cartlow.com/intl/en"

EMAIL    = "muhammad.akmal@cartlow.com"
PASSWORD = "Test!123"
COUPON   = "welcome10"


# ── Helpers ───────────────────────────────────────────────────────────────────

def login(page: Page):
    for attempt in range(3):
        try:
            page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
            break
        except Exception:
            page.wait_for_timeout(5000)
    page.wait_for_timeout(10000)
    for _ in range(15):
        try:
            page.evaluate("document.querySelector('#app').__vue_app__.config.globalProperties.$emitter.emit('open-customer-auth-modal')")
            page.locator("#login-email").wait_for(state="visible", timeout=3000)
            page.wait_for_timeout(500)
            page.locator("#login-email").evaluate("el => el.focus()")
            if page.locator("#login-email").evaluate("el => document.activeElement === el"):
                page.wait_for_timeout(300)
                break
        except: page.wait_for_timeout(1500)
    page.locator("#login-email").fill(EMAIL)
    page.locator("#login-password").fill(PASSWORD)
    page.wait_for_timeout(500)
    # Dismiss download app popup if blocking Sign In
    try:
        close = page.locator("button[aria-label='Close download app modal']")
        if close.is_visible():
            close.click()
            page.wait_for_timeout(500)
    except: pass
    page.locator("button:has-text('Sign In')").first.click()
    page.wait_for_timeout(6000)
    print("✅ Logged in")


def switch_channel(page: Page, channel: str):
    page.locator("button:has-text('UAE')").first.click()
    page.wait_for_timeout(1500)
    page.locator(f"span.cursor-pointer:has-text('{channel}')").first.click()
    page.wait_for_timeout(8000)
    if channel == "INTL":
        page.context.add_cookies([{"name": "__selected_country", "value": "intl",
                                    "domain": "www.cartlow.com", "path": "/"}])
    print(f"✅ Switched to {channel}")


def add_product_to_cart(page: Page, channel_url: str, search: str = "iphone"):
    page.goto(f"{channel_url}/search?query={search}", wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.wait_for_selector("a[href*='product-detail']", state="attached", timeout=20000)
    products = list(dict.fromkeys(page.evaluate(
        "() => [...document.querySelectorAll('a[href*=product-detail]')].map(a => a.href)"
    )))
    for link in products:
        try:
            page.goto(link, wait_until="domcontentloaded", timeout=30000)
        except Exception:
            continue
        page.wait_for_timeout(5000)
        body = page.locator("body").inner_text()
        prices = re.findall(r'\$\s*([\d.]+)', body)
        if prices and float(prices[0]) < 1.0:
            continue
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
                btn.click(force=True)
                page.wait_for_timeout(4000)
                if "View Cart" in page.locator("body").inner_text():
                    print(f"✅ Added: {page.title()}"); return
        keep = page.locator("div.cursor-pointer:has-text('Keep it for Yourself')").first
        if keep.count() and keep.is_visible():
            keep.click()
            page.wait_for_timeout(3000)
            if "View Cart" in page.locator("body").inner_text():
                print(f"✅ Added (digital): {page.title()}"); return


def go_to_checkout(page: Page, channel_url: str):
    page.goto(f"{channel_url}/checkout/cart", wait_until="domcontentloaded")
    page.wait_for_timeout(5000)
    links = page.locator("a[href*='checkout/onepage']")
    if links.count() > 0:
        links.last.click()
    else:
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
    success = (page.locator("svg.text-green-600").first.is_visible()
               or "discount" in page.locator("body").inner_text().lower())
    print(f"{'✅' if success else '⚠️ '} Coupon '{COUPON}' {'applied' if success else 'not applied'}")


def verify_payment_gateway_loads(page: Page):
    """Place order and verify payment gateway page loads — stop before paying."""
    page.locator("button:has-text('Place Order')").first.click()
    page.wait_for_timeout(12000)
    url = page.url
    print(f"✅ Gateway URL: {url}")
    assert "cartlow.com/checkout/onepage" not in url, \
        f"Still on checkout page — Place Order may have failed"
    # Wait for gateway to render
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(3000)
    body = page.evaluate("() => document.body.innerText")
    assert len(body) > 50, f"Gateway page appears empty. URL: {url}"
    print(f"✅ Payment gateway loaded (NOT clicking Pay — production mode)")


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_e2e_uae_checkout_production(page: Page):
    """E2E checkout on UAE production — verifies gateway loads, stops before Pay."""
    page.set_viewport_size({"width": 1280, "height": 800})
    login(page)
    add_product_to_cart(page, BASE_URL)
    go_to_checkout(page, BASE_URL)
    apply_coupon(page)
    verify_payment_gateway_loads(page)
    print("✅ UAE production checkout flow PASSED")


def test_e2e_ksa_checkout_production(page: Page):
    """E2E checkout on KSA production — verifies gateway loads, stops before Pay."""
    page.set_viewport_size({"width": 1280, "height": 800})
    login(page)
    switch_channel(page, "KSA")
    add_product_to_cart(page, KSA_URL)
    go_to_checkout(page, KSA_URL)
    apply_coupon(page)
    verify_payment_gateway_loads(page)
    print("✅ KSA production checkout flow PASSED")


def test_e2e_intl_checkout_production(page: Page):
    """E2E checkout on INTL production — verifies gateway loads, stops before Pay."""
    page.set_viewport_size({"width": 1280, "height": 800})
    login(page)
    switch_channel(page, "INTL")
    add_product_to_cart(page, INTL_URL, search="pubg")
    go_to_checkout(page, INTL_URL)
    verify_payment_gateway_loads(page)
    print("✅ INTL production checkout flow PASSED")
