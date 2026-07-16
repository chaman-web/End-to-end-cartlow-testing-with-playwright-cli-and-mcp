"""
Test: Get all active country codes from the INTL channel phone number dropdown
in the auth modal registration form.
Extracts country name and dial code for each entry and saves to a report.
"""
import pytest
from playwright.sync_api import Page

BASE_URL = "https://stage.cartlow.com/uae/en"
INTL_URL = "https://stage.cartlow.com/intl/en"


def test_get_intl_country_codes(page: Page):
    """Open INTL registration form, click phone dial code, extract all countries."""
    page.set_viewport_size({"width": 1280, "height": 800})

    # Login to UAE then switch to INTL
    page.goto(BASE_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)

    page.locator("button:has-text('UAE')").first.click()
    page.wait_for_timeout(1500)
    page.locator("span.cursor-pointer:has-text('INTL')").first.click()
    page.wait_for_timeout(8000)
    page.context.add_cookies([{
        "name": "__selected_country", "value": "intl",
        "domain": "stage.cartlow.com", "path": "/"
    }])
    page.goto(INTL_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(5000)

    # Open auth modal and go to Create Account
    for _ in range(10):
        try:
            page.evaluate("document.querySelector('#app').__vue_app__.config.globalProperties.$emitter.emit('open-customer-auth-modal')")
            page.wait_for_selector("#login-email", state="visible", timeout=5000)
            break
        except: page.wait_for_timeout(2000)

    page.locator("span:has-text('Create Account')").first.click(force=True)
    page.wait_for_selector("#register-email", state="visible", timeout=10000)
    page.wait_for_timeout(2000)

    # Type phone prefix to switch input to phone mode and reveal dial code button
    page.locator("#register-email").fill("05")
    page.wait_for_timeout(1000)

    # Click the dial code button to open country list
    page.locator("button:has-text('+')").first.click()
    page.wait_for_timeout(2000)

    # Extract all country name + dial code from the dropdown
    body_text = page.locator("body").inner_text()

    # Parse lines like "Albania +355"
    import re
    lines = body_text.split("\n")
    countries = []
    for line in lines:
        line = line.strip()
        match = re.match(r'^(.+?)\s+(\+\d{1,4})$', line)
        if match:
            name = match.group(1).strip()
            code = match.group(2).strip()
            # Filter out non-country items
            if len(name) > 1 and name not in ["INTL", "Account", "Sign In", "Continue"]:
                countries.append({"country": name, "dial_code": code})

    print(f"\n📋 Found {len(countries)} countries in INTL phone dropdown:\n")
    print(f"{'Country':<40} {'Dial Code'}")
    print("-" * 55)
    for c in countries:
        print(f"  {c['country']:<38} {c['dial_code']}")

    # Save to report
    report_path = "reports/intl_country_codes.txt"
    with open(report_path, "w") as f:
        f.write(f"INTL Channel — Active Country Codes ({len(countries)} countries)\n")
        f.write("=" * 55 + "\n")
        f.write(f"{'Country':<40} Dial Code\n")
        f.write("-" * 55 + "\n")
        for c in countries:
            f.write(f"{c['country']:<40} {c['dial_code']}\n")

    print(f"\n📄 Report saved to {report_path}")
    assert len(countries) > 0, "No countries found in dropdown"
    print(f"\n✅ PASSED — {len(countries)} active countries detected")
