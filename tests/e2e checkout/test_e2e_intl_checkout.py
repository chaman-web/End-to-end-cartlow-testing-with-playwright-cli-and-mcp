from playwright.sync_api import Page

BASE_URL  = "https://stage.cartlow.com/uae/en"
INTL_URL  = "https://stage.cartlow.com/intl/en"
EMAIL     = "muhammad.akmal@cartlow.com"
PASSWORD  = "Test!123"
SEARCH    = "pubg"

GIFT_NAME  = "Test Recipient"
GIFT_EMAIL = "recipient@test.com"
GIFT_PHONE = "+971501234567"

CHECKOUT_CARD = "4242424242424242"
EXPIRY        = "1133"
CVV           = "123"
CARDHOLDER    = "Test"


def login(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    for _ in range(20):
        try:
            page.evaluate("document.querySelector('#app').__vue_app__.config.globalProperties.$emitter.emit('open-customer-auth-modal')")
            page.wait_for_timeout(2000)
            if page.locator("#login-email").count() > 0:
                break
        except: pass
    page.locator("#login-email").fill(EMAIL, force=True)
    page.locator("#login-password").fill(PASSWORD, force=True)
    page.evaluate("['#login-email','#login-password'].forEach(s=>{const e=document.querySelector(s);if(e)e.dispatchEvent(new Event('input',{bubbles:true}))})")
    page.wait_for_timeout(1000)
    page.evaluate("() => [...document.querySelectorAll('button')].find(b => b.innerText.trim() === 'Sign In')?.click()")
    page.wait_for_timeout(6000)
    print("✅ Logged in")


def switch_to_intl(page: Page):
    # Click UAE dropdown and select INTL
    page.locator("button:has-text('UAE')").first.click()
    page.wait_for_timeout(1500)
    page.locator("span.cursor-pointer:has-text('INTL')").first.click()
    page.wait_for_timeout(8000)
    # Set the country cookie directly to ensure it persists
    page.context.add_cookies([{
        "name": "__selected_country",
        "value": "intl",
        "domain": "stage.cartlow.com",
        "path": "/"
    }])
    # Navigate to INTL homepage and wait for products to load
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_selector("a[href*='product-detail']", state="attached", timeout=20000)
    page.wait_for_timeout(3000)
    assert "intl" in page.url, f"Expected INTL URL, got: {page.url}"
    print("✅ Switched to INTL channel")


def test_e2e_intl_checkout(page: Page):
    page.set_viewport_size({"width": 1280, "height": 800})

    # 1. Login
    login(page)

    # 2. Switch to INTL
    switch_to_intl(page)

    # 3. Search
    page.goto(f"{INTL_URL}/search?query={SEARCH}", wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    assert "search" in page.url
    print(f"✅ Search — {page.url}")

    # 4. Open first working product with price >= $1
    products = list(dict.fromkeys(page.evaluate(
        "() => [...document.querySelectorAll('a[href*=product-detail]')].map(a => a.href)"
    )))
    assert products, "No products found"

    for link in products:
        page.goto(link, wait_until="domcontentloaded")
        page.wait_for_timeout(6000)
        body = page.locator("body").inner_text()
        # Skip products under $1
        import re
        prices = re.findall(r'\$\s*([\d.]+)', body)
        if prices and float(prices[0]) < 1.0:
            print(f"  ⏭ Skipping {page.title()} (price ${prices[0]} < $1)")
            continue
        if "Keep it for Yourself" in body or "Add To Cart" in body or "View Cart" in body:
            break
    print(f"✅ Product — {page.title()}")

    # 5. Add to cart
    body = page.locator("body").inner_text()

    if "View Cart" in body:
        # Already in cart — go directly
        print("ℹ️  Already in cart — going to cart directly")

    elif "Keep it for Yourself" in body:
        page.locator("div.cursor-pointer:has-text('Keep it for Yourself')").click()
        page.wait_for_timeout(3000)
        body = page.locator("body").inner_text()

        if "View Cart" in body:
            print("✅ Added to cart (Keep it for Yourself)")
        else:
            # Gift flow
            page.locator("div.cursor-pointer:has-text('Gift it to Someone Special')").click()
            page.wait_for_timeout(2000)
            page.locator("input[placeholder='Recipient Name']").fill(GIFT_NAME)
            page.locator("#gift_card_recipient_email").fill(GIFT_EMAIL)
            page.locator("#gift_card_recipient_phone").fill(GIFT_PHONE)
            page.wait_for_timeout(500)
            print("✅ Gift form filled")
            for btn_text in ["Add To Cart", "Add to Cart", "Add Gift to Cart"]:
                btn = page.locator(f"button:has-text('{btn_text}')").first
                if btn.count() and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(4000)
                    print(f"✅ Clicked '{btn_text}'")
                    break

    elif "Add To Cart" in body or "Add to Cart" in body:
        page.locator("button:has-text('Add To Cart'), button:has-text('Add to Cart')").first.click()
        page.wait_for_timeout(4000)
        print("✅ Added to cart")

    # 6. Cart
    page.goto(f"{INTL_URL}/checkout/cart", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    assert "cart" in page.url
    body = page.locator("body").inner_text().lower()
    assert any(k in body for k in ["checkout", "remove", "$", "usd"])
    print(f"✅ Cart verified")

    # 7. Proceed to checkout
    page.goto(f"{INTL_URL}/checkout/onepage", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    assert "onepage" in page.url
    print(f"✅ Checkout — {page.url}")

    # 8. Place Order
    for btn_text in ["Place Order", "Proceed to Pay", "Continue"]:
        btn = page.locator(f"button:has-text('{btn_text}')").first
        if btn.count() and btn.is_visible():
            btn.click()
            page.wait_for_timeout(8000)
            print(f"✅ '{btn_text}' clicked — {page.url}")
            break

    # 9. Payment gateway — Checkout.com (card fields inside iframes)
    if "checkout.com" in page.url or "pay.sandbox" in page.url:
        print("💳 Checkout.com gateway")
        page.wait_for_timeout(4000)

        for frame in page.frames:
            loc = frame.locator("input[name='card-number']")
            if loc.count() and loc.first.is_visible():
                loc.first.click()
                loc.first.type(CHECKOUT_CARD, delay=80)
                print("  Card number entered")
                break

        for frame in page.frames:
            loc = frame.locator("input[name='card-expiry-date'], input[placeholder='MM/YY']")
            if loc.count() and loc.first.is_visible():
                loc.first.click()
                loc.first.type(EXPIRY, delay=150)
                print("  Expiry entered")
                break

        for frame in page.frames:
            loc = frame.locator("input[name='card-cvv'], input[placeholder='CVV']")
            if loc.count() and loc.first.is_visible():
                loc.first.click()
                loc.first.type(CVV, delay=80)
                print("  CVV entered")
                break

        for frame in page.frames:
            loc = frame.locator("input[name='cardholder-name']")
            if loc.count() and loc.first.is_visible():
                loc.first.click()
                loc.first.fill(CARDHOLDER)
                print("  Cardholder entered")
                break

        page.wait_for_timeout(1000)
        print("✅ Card details entered")

        # Wait for Pay button that starts with "Pay " (not "Select ... Pay" or Apple Pay)
        page.wait_for_function(
            """() => {
                const btns = [...document.querySelectorAll('button')];
                return btns.some(b => /^pay\\s/i.test(b.innerText.trim()) && b.offsetParent !== null && !b.disabled);
            }""",
            timeout=20000,
        )
        for btn in page.locator("button").all():
            try:
                txt = btn.inner_text().strip()
                if txt.lower().startswith("pay ") and btn.is_visible():
                    btn.click()
                    print(f"✅ Pay button clicked: '{txt}'")
                    break
            except: continue
        page.wait_for_timeout(10000)
        print(f"  URL after Pay: {page.url}")

        # Wait up to 60s for Cartlow redirect or 3DS auth input
        auth_filled = False
        for _ in range(12):
            if "stage.cartlow.com" in page.url:
                print("  No auth needed — redirected to Cartlow")
                break
            for frame in page.frames:
                try:
                    for inp in frame.query_selector_all("input"):
                        try:
                            if not inp.is_visible(): continue
                            t  = (inp.get_attribute("type") or "").lower()
                            ph = (inp.get_attribute("placeholder") or "").lower()
                            nm = (inp.get_attribute("name") or "").lower()
                            if t == "password" or any(k in ph+nm for k in ["password","code","auth","otp"]):
                                inp.fill("Checkout1!")
                                auth_filled = True
                                print(f"  Auth input filled (frame: {frame.url[:60]})")
                                break
                        except: continue
                    if auth_filled: break
                except: continue
            if auth_filled:
                page.wait_for_timeout(1000)
                for label in ["Continue", "Submit", "Authorize", "Confirm", "OK"]:
                    for frame in page.frames:
                        try:
                            btn = frame.locator(f"button:has-text('{label}')").first
                            if btn.is_visible():
                                btn.click()
                                print(f"  Auth submitted via: {label}")
                                break
                        except: continue
                    else: continue
                    break
                else:
                    page.keyboard.press("Enter")
                    print("  Auth submitted via Enter")
                page.wait_for_timeout(10000)
                print(f"  URL after auth: {page.url}")
                break
            page.wait_for_timeout(5000)

    elif "paymob" in page.url:
        print("💳 Paymob gateway")
        page.wait_for_selector("input[name='number']", state="visible", timeout=15000)
        page.locator("input[name='number']").fill(CHECKOUT_CARD)
        page.locator("input[name='expiry']").fill("11/33")
        page.locator("input[name='cvc']").fill(CVV)
        page.locator("input[name='name']").fill(CARDHOLDER)
        page.wait_for_timeout(600)
        page.locator("button:has-text('Pay')").first.click()
        page.wait_for_timeout(10000)
        print(f"✅ Paymob Pay clicked — {page.url}")

    # 11. Assert success — wait for redirect to Cartlow success page
    page.wait_for_url("**/stage.cartlow.com/**", timeout=45000)
    page.wait_for_timeout(4000)
    print(f"✅ Redirected to Cartlow — {page.url}")
    assert any(k in page.url for k in ["success", "order"]), f"Expected success URL, got: {page.url}"
    print(f"✅ Order placed — {page.url}")
    print("✅ Test PASSED — full INTL E2E checkout complete!")
