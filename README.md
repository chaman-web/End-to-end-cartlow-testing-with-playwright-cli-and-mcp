# Cartlow Playwright Automation Framework

## Project Structure (Page Object Model)

```
playwright cli/
│
├── conftest.py                        # Session auth + all page object fixtures
├── pytest.ini                         # Pytest config (testpaths, markers)
├── requirements.txt                   # Python dependencies
│
├── pages/                             # ── PAGE OBJECT MODEL ──
│   ├── __init__.py
│   ├── base_page.py                   # BasePage: navigation, scroll, wait, channel switch
│   ├── login_page.py                  # Login modal interactions
│   ├── home_page.py                   # Homepage: search, nav links, banners
│   ├── search_page.py                 # Search results: products, filters, sort
│   ├── pdp_page.py                    # Product Detail Page: add to cart, price
│   ├── gift_card_pdp_page.py          # Gift Card PDP: Myself/Gift it, recipient form
│   ├── cart_page.py                   # Cart: remove items, Agree popup, checkout
│   ├── checkout_page.py               # Checkout: address, order summary
│   └── payment_page.py               # Payment: COD, card, Tabby, Tamara
│
├── tests/
│   ├── auth module testing/
│   │   ├── test_login.py
│   │   ├── test_registration_positive.py
│   │   └── test_registration_with_mobile.py
│   │
│   ├── intl regression/
│   │   ├── test_intl_homepage.py
│   │   ├── test_intl_search.py
│   │   ├── test_intl_pdp.py
│   │   ├── test_intl_gift_card_pdp.py
│   │   ├── test_intl_cart.py
│   │   ├── test_intl_checkout_page.py
│   │   ├── test_intl_shipping_fee.py
│   │   ├── test_intl_payment_flow.py
│   │   └── test_intl_full_journey.py
│   │
│   ├── test payment method/
│   │   ├── test_payment_method_uae.py
│   │   ├── test_payment_method_ksa.py
│   │   └── test_payment_method_intl.py
│   │
│   └── e2e checkout/
│       ├── test_e2e_checkout.py
│       ├── test_all_channels_e2e.py
│       └── test_all_channels_e2e_production.py
│
├── reports/                           # HTML reports, logs
└── .auth_state.json                   # Saved session cookies (auto-generated)
```

---

## Page Object Hierarchy

```
BasePage
├── LoginPage
├── HomePage
├── SearchPage
├── PDPPage
│   └── GiftCardPDPPage
├── CartPage
├── CheckoutPage
└── PaymentPage
```

---

## How to Use Page Objects in Tests

### Old way (inline helpers — avoid)
```python
def test_something(browser):
    page = browser.new_page()
    page.goto("https://...")
    page.evaluate("() => ...")
    page.locator("#some-id").fill("value")
```

### New way (POM — recommended)
```python
def test_gc_gift_it(gc_pdp_page: GiftCardPDPPage, cart_page: CartPage):
    cart_page.open(CART_URL)
    cart_page.clear()

    gc_pdp_page.open(PDP_URL)
    gc_pdp_page.select_gift_it()
    gc_pdp_page.fill_gift_form("John Doe", "johndoe@test.com", "Happy Birthday!")
    gc_pdp_page.click_add_to_cart()
    gc_pdp_page.wait_for_view_cart()

    assert gc_pdp_page.is_view_cart_showing()
```

---

## Running Tests

```bash
# Activate venv
source .venv/bin/activate

# Run all intl regression tests (headless, 4 workers)
pytest "tests/intl regression/" -n 4 --dist=loadfile --browser chromium

# Run a specific test file headed (for debugging)
pytest "tests/intl regression/test_intl_gift_card_pdp.py" --headed --browser chromium -v -s

# Run only failed tests
pytest --last-failed --browser chromium

# Run with HTML report
pytest "tests/intl regression/" --browser chromium --html=reports/report.html
```

---

## Key Design Decisions

| Decision | Reason |
|---|---|
| `session_auth` fixture | Login once, reuse cookies — saves ~25s per test |
| `function`-scoped page fixtures | Each test gets a fresh isolated browser context |
| `BasePage` with `goto()` retry | Network flakiness handled centrally |
| `CartPage.clear()` with Agree popup | Cart must be empty before PDP tests or Add to Cart is disabled |
| `GiftCardPDPPage` extends `PDPPage` | Reuses Add to Cart, View Cart logic; adds gift-specific methods |
