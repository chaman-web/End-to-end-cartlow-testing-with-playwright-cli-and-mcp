"""
PDPPage — Product Detail Page interactions (standard products).
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class PDPPage(BasePage):

    # ── Locators ───────────────────────────────────────────────────────────────
    ADD_TO_CART_BTN  = "button:has-text('Add To Cart'), button:has-text('Add to Cart')"
    VIEW_CART_BTN    = "button:has-text('View Cart'), a:has-text('View Cart')"
    PRODUCT_TITLE    = "h1, [class*='product-title'], [class*='product-name']"
    PRODUCT_PRICE    = "[class*='price']"
    QUANTITY_INPUT   = "input[type='number'][name*='qty'], input[name='qty']"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self, url: str):
        """Navigate to PDP and scroll to reveal all options."""
        self.goto(url)
        self.page.wait_for_timeout(8000)
        self.scroll_down(steps=15)
        self.page.wait_for_timeout(2000)

    def get_product_title(self) -> str:
        return self.page.locator(self.PRODUCT_TITLE).first.inner_text().strip()

    def get_price(self) -> str:
        return self.page.locator(self.PRODUCT_PRICE).first.inner_text().strip()

    def is_add_to_cart_visible(self) -> bool:
        return self.page.locator(self.ADD_TO_CART_BTN).first.is_visible()

    def is_view_cart_showing(self) -> bool:
        return self.has_text("View Cart")

    def click_add_to_cart(self):
        btn = self.page.locator(self.ADD_TO_CART_BTN).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click(force=True)
        self.page.wait_for_timeout(4000)

    def wait_for_view_cart(self, timeout_s: int = 10):
        for _ in range(timeout_s):
            if self.is_view_cart_showing():
                return
            self.page.wait_for_timeout(1000)
