"""
CheckoutPage — Checkout page interactions.
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class CheckoutPage(BasePage):

    # ── Locators ───────────────────────────────────────────────────────────────
    ADDRESS_SECTION  = "[class*='address'], text=Delivery Address"
    PAYMENT_SECTION  = "[class*='payment'], text=Payment Method"
    PLACE_ORDER_BTN  = "button:has-text('Place Order'), button:has-text('Confirm Order')"
    ORDER_SUMMARY    = "text=Order Summary"
    FIRST_NAME       = "input[name*='firstname'], input[placeholder*='First']"
    LAST_NAME        = "input[name*='lastname'], input[placeholder*='Last']"
    PHONE            = "input[name*='phone'], input[type='tel']"
    ADDRESS_LINE     = "input[name*='street'], input[placeholder*='Address']"
    CITY             = "input[name*='city'], input[placeholder*='City']"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self, checkout_url: str):
        self.goto(checkout_url)
        self.page.wait_for_timeout(5000)

    def fill_address(self, first_name: str, last_name: str, phone: str,
                     address: str, city: str):
        """Fill delivery address fields."""
        self.page.locator(self.FIRST_NAME).first.fill(first_name)
        self.page.locator(self.LAST_NAME).first.fill(last_name)
        self.page.locator(self.PHONE).first.fill(phone)
        self.page.locator(self.ADDRESS_LINE).first.fill(address)
        self.page.locator(self.CITY).first.fill(city)
        self.page.wait_for_timeout(500)

    def select_payment_method(self, method: str):
        """Click a payment method option by label text."""
        self.page.locator(f"text={method}").first.click()
        self.page.wait_for_timeout(1000)

    def click_place_order(self):
        btn = self.page.locator(self.PLACE_ORDER_BTN).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.page.wait_for_timeout(5000)

    def is_order_summary_visible(self) -> bool:
        return self.has_text("Order Summary")

    def is_payment_section_visible(self) -> bool:
        return self.has_text("Payment")
