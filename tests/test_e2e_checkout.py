from playwright.sync_api import Page

BASE_URL  = "https://stage.cartlow.com/uae/en"
EMAIL     = "muhammad.akmal@cartlow.com"
PASSWORD  = "Test!123"
SEARCH    = "iphone"

CHECKOUT_CARD = "4242424242424242"
PAYMOB_CARD   = "5123456789012346"
EXPIRY        = "1133"       # typed as digits; field auto-formats to 11/33
EXPIRY_SLASH  = "11/33"
CVV           = "123"
CARDHOLDER    = "Test"
BANK_PASSWORD = "Checkout1!"


# ── helpers ───────────────────────────────────────────────────────────────────

def login(page: Page):
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    for _ in range(10):
        try:
            page.evaluate(
                "document.querySelector('#app').__vue_app__"
                ".config.globalProperties.$emitter.emit('open-customer-auth-modal')"
            )
            break
        except Exception:
            page.wait_for_timeout(2000)
    page.wait_for_selector("#login-email", state="visible", timeout=20000)
    page.fill("#login-email", EMAIL)
    page.fill("#login-password", PASSWORD)
    page.locator("button:has-text('Sign In')").first.click()
    page.wait_for_timeout(6000)
    print(f"✅ Logged in — {page.url}")


def fill_paymob(page: Page):
    """Paymob: direct inputs on the page (no iframes needed)."""
    page.wait_for_selector("input[name='number']", state="visible", timeout=15000)
    page.locator("input[name='number']").fill(PAYMOB_CARD)
    page.wait_for_timeout(400)
    page.locator("input[name='expiry']").fill(EXPIRY_SLASH)
    page.wait_for_timeout(400)
    page.locator("input[name='cvc']").fill(CVV)
    page.wait_for_timeout(400)
    page.locator("input[name='name']").fill(CARDHOLDER)
    page.wait_for_timeout(600)
    print("  Paymob fields filled")


def fill_checkout_com(page: Page):
    """Checkout.com: each card field lives in its own iframe."""
    page.wait_for_timeout(4000)

    # Card number
    for frame in page.frames:
        loc = frame.locator("input[name='card-number']")
        if loc.count() and loc.first.is_visible():
            loc.first.click()
            loc.first.type(CHECKOUT_CARD, delay=80)
            print("  Card number entered")
            break
    page.wait_for_timeout(600)

    # Expiry — type digits only, field auto-formats to MM/YY
    for frame in page.frames:
        loc = frame.locator("input[name='card-expiry-date'], input[placeholder='MM/YY']")
        if loc.count() and loc.first.is_visible():
            loc.first.click()
            loc.first.type(EXPIRY, delay=150)
            print("  Expiry entered")
            break
    page.wait_for_timeout(600)

    # CVV
    for frame in page.frames:
        loc = frame.locator("input[name='card-cvv'], input[placeholder='CVV']")
        if loc.count() and loc.first.is_visible():
            loc.first.click()
            loc.first.type(CVV, delay=80)
            print("  CVV entered")
            break
    page.wait_for_timeout(600)

    # Cardholder name — required to enable Pay button
    for frame in page.frames:
        loc = frame.locator("input[name='cardholder-name']")
        if loc.count() and loc.first.is_visible():
            loc.first.click()
            loc.first.fill(CARDHOLDER)
            print("  Cardholder name entered")
            break
    page.wait_for_timeout(1000)


# ── test ──────────────────────────────────────────────────────────────────────

def test_e2e_checkout(page: Page):
    page.set_viewport_size({"width": 1280, "height": 800})

    # 1. Login
    login(page)

    # 2. Search
    page.goto(f"{BASE_URL}/search?query={SEARCH}", wait_until="domcontentloaded")
    page.wait_for_timeout(10000)
    page.wait_for_selector("a[href*='product-detail']", state="attached", timeout=20000)
    assert "search" in page.url
    print(f"✅ Search — {page.url}")

    # 3. Open a product (skip 404s)
    hrefs = page.evaluate("() => [...document.querySelectorAll('a')].map(a => a.href)")
    products = [h for h in hrefs if "product-detail" in h]
    assert products, "No product links on search page"

    loaded = False
    for link in products:
        page.goto(link, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        t = page.title().lower()
        if "oops" in t or "couldn't find" in t or "404" in t:
            print(f"  ⏭ 404 — {link}")
            continue
        loaded = True
        break
    assert loaded, "No working product found"
    print(f"✅ Product — {page.url}")

    # 4. Add to Cart — retry next product if quantity not available or cart empty
    added_to_cart = False
    remaining_products = products[products.index(link):]  # start from current product

    for product_url in remaining_products:
        # Navigate to product if not already there
        if page.url != product_url:
            page.goto(product_url, wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            t = page.title().lower()
            if "oops" in t or "couldn't find" in t or "404" in t:
                print(f"  ⏭ 404 — {product_url}")
                continue

        # Scroll down to reveal buttons
        for _ in range(10):
            page.mouse.wheel(0, 150)
            page.wait_for_timeout(300)
        page.wait_for_timeout(2000)

        body = page.locator("body").inner_text()

        if "View Cart" in body:
            print("ℹ️  Already in cart — going to cart directly")
            added_to_cart = True
            break

        print(f"ℹ️  Clicking Add To Cart on {product_url}")
        page.locator(
            "button:has-text('Add To Cart'), button:has-text('Add to Cart')"
        ).first.click(force=True)
        page.wait_for_timeout(4000)

        # Check result
        body_after = page.locator("body").inner_text()
        if "View Cart" in body_after:
            print("✅ Item added to cart")
            added_to_cart = True
            break
        elif any(k in body_after.lower() for k in ["not available", "out of stock", "quantity"]):
            print(f"  ⚠️  Not available — trying next product")
            continue
        else:
            # Assume added (no error shown)
            added_to_cart = True
            break

    assert added_to_cart, "Could not add any product to cart"

    # 5. Cart page
    page.goto(f"{BASE_URL}/checkout/cart", wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    assert "cart" in page.url
    body = page.locator("body").inner_text().lower()
    assert any(k in body for k in ["remove", "checkout", "aed"])
    print("✅ Cart verified")

    # 6. Checkout
    links = page.locator("a").filter(has_text="Checkout")
    for i in range(links.count()):
        if links.nth(i).is_visible():
            links.nth(i).click()
            break
    page.wait_for_timeout(8000)
    assert "checkout" in page.url, f"Checkout not loaded: {page.url}"
    print(f"✅ Checkout — {page.url}")

    # 7. Place Order
    place = page.locator("button:has-text('Place Order')").first
    place.wait_for(state="visible", timeout=15000)
    place.click()
    page.wait_for_timeout(10000)
    print(f"✅ Place Order clicked — {page.url}")

    # 8. Fill payment card details
    url = page.url.lower()
    if "paymob" in url:
        print("💳 Paymob gateway")
        fill_paymob(page)
    else:
        print("💳 Checkout.com gateway")
        fill_checkout_com(page)
    print("✅ Card details entered")

    # 9. Scroll down to reveal Pay button, wait until enabled, then click
    for _ in range(5):
        page.mouse.wheel(0, 200)
        page.wait_for_timeout(300)

    page.wait_for_function(
        """() => {
            const btns = [...document.querySelectorAll('button')];
            const pay = btns.find(b =>
                /^pay\\s/i.test(b.innerText.trim()) &&
                b.offsetParent !== null &&
                !b.disabled
            );
            return !!pay;
        }""",
        timeout=20000,
    )

    # Click the Pay button that starts with "Pay " (not "Select ... Pay")
    all_btns = page.locator("button").all()
    for btn in all_btns:
        try:
            txt = btn.inner_text().strip()
            if txt.lower().startswith("pay ") and btn.is_visible():
                btn.click()
                print(f"✅ Pay button clicked: {repr(txt)}")
                break
        except Exception:
            continue

    # 10. Bank authorization modal (may appear for 3DS) — enter "Checkout1!"
    page.wait_for_timeout(5000)
    print(f"  URL after Pay: {page.url}")

    # If already redirected to success page, skip auth
    if "success" in page.url.lower() or "order" in page.url.lower() and "stage.cartlow" in page.url.lower():
        print("  No auth modal needed — already on success/order page")
    else:
        # Look for authorization input in page or any frame (up to 30s)
        auth_filled = False
        for _ in range(6):
            all_inputs = list(page.query_selector_all("input"))
            for frame in page.frames:
                try:
                    all_inputs += list(frame.query_selector_all("input"))
                except Exception:
                    pass

            for inp in all_inputs:
                try:
                    if not inp.is_visible():
                        continue
                    t  = (inp.get_attribute("type") or "").lower()
                    ph = (inp.get_attribute("placeholder") or "").lower()
                    nm = (inp.get_attribute("name") or "").lower()
                    if t == "password" or any(k in ph+nm for k in ["password", "code", "auth"]):
                        inp.fill(BANK_PASSWORD)
                        auth_filled = True
                        print("  Auth password entered")
                        break
                except Exception:
                    continue

            if auth_filled:
                break
            page.wait_for_timeout(5000)

        if auth_filled:
            # Submit authorization
            page.wait_for_timeout(1000)
            for btn_text in ["Continue", "Submit", "Authorize", "Confirm", "OK", "Proceed"]:
                for btn in page.locator(f"button:has-text('{btn_text}')").all():
                    if btn.is_visible():
                        btn.click()
                        print(f"  Auth submitted via: {btn_text}")
                        break
                else:
                    continue
                break
            else:
                page.keyboard.press("Enter")
                print("  Auth submitted via Enter")

            page.wait_for_timeout(8000)
            print(f"  URL after auth: {page.url}")

    # 11. Wait for redirect to Cartlow success/order page
    page.wait_for_url("**/stage.cartlow.com/**", timeout=45000)
    page.wait_for_timeout(4000)
    print(f"✅ Redirected to Cartlow — {page.url}")

    # 12. Verify thank you / success page
    final_body = page.locator("body").inner_text().lower()
    assert any(k in page.url.lower() for k in ["success", "order", "thank"]) or \
           any(k in final_body for k in ["thank", "order", "success", "placed"]), \
        f"Success page not reached. URL: {page.url}"
    print("✅ Order success page verified")

    # 13. Click order ID link (e.g. "ORD-1003206003") → order detail page
    order_link = page.locator("a[href*='/orders/view/']").first
    order_link.wait_for(state="visible", timeout=10000)
    order_id_text = order_link.inner_text().strip()
    order_link.click()
    page.wait_for_timeout(5000)
    print(f"✅ Clicked order ID: {order_id_text} — {page.url}")
    assert "orders" in page.url.lower() or "order" in page.url.lower(), \
        f"Order detail page not reached. URL: {page.url}"
    print("✅ Test PASSED — full E2E checkout complete!")
