"""
CartPage — Shopping cart interactions.
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class CartPage(BasePage):

    # ── Locators ───────────────────────────────────────────────────────────────
    # Visible Remove button: span[role="button"] with SVG icon + "Remove" text
    REMOVE_BTN       = 'span[role="button"][tabindex="0"]:has-text("Remove")'
    AGREE_BTN        = "button:has-text('Agree')"
    CHECKOUT_BTN     = "button:has-text('Proceed to Checkout'), button:has-text('Checkout')"
    CART_ITEM        = "[class*='cart-item'], [class*='main-A']"
    ORDER_SUMMARY    = "[class*='order-summary'], text=Order Summary"
    EMPTY_CART_MSG   = "text=empty, text=no items"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self, cart_url: str):
        self.goto(cart_url)
        self.page.wait_for_timeout(4000)

    def is_empty(self) -> bool:
        body = self.body_text().lower()
        return any(kw in body for kw in ["empty", "no items", "your cart is"])

    def get_item_count(self) -> int:
        return self.page.locator(self.REMOVE_BTN).count()

    def clear(self):
        """Remove all items from cart, handling the Agree confirmation popup."""
        remove_btn = self.page.locator(self.REMOVE_BTN)

        if remove_btn.count() == 0:
            return

        removed = 0
        for _ in range(20):
            if remove_btn.count() == 0:
                break
            try:
                remove_btn.first.click(timeout=5000)
                self.page.wait_for_timeout(1500)
                # Handle confirmation popup
                agree = self.page.locator(self.AGREE_BTN)
                if agree.count() > 0:
                    agree.first.click(timeout=5000)
                    self.page.wait_for_timeout(3000)
                removed += 1
            except Exception:
                break

        self.page.wait_for_timeout(2000)
        if removed:
            print(f"   Cleared {removed} cart item(s) ✅")

    def click_checkout(self):
        btn = self.page.locator(self.CHECKOUT_BTN).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.page.wait_for_timeout(4000)

    def has_product(self, name: str) -> bool:
        return name in self.body_text()
