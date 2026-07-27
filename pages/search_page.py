"""
SearchPage — Search results page interactions.
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class SearchPage(BasePage):

    # ── Locators ───────────────────────────────────────────────────────────────
    PRODUCT_CARDS    = ".product-card, [class*='product-item'], [class*='product-card']"
    FILTER_SIDEBAR   = "[class*='filter'], [class*='sidebar']"
    SORT_DROPDOWN    = "select[name*='sort'], [class*='sort']"
    RESULTS_COUNT    = "[class*='result'], [class*='count']"
    NO_RESULTS_MSG   = "text=No results, text=no products found"

    def __init__(self, page: Page):
        super().__init__(page)

    def get_product_count(self) -> int:
        return self.page.locator(self.PRODUCT_CARDS).count()

    def click_first_product(self):
        self.page.locator(self.PRODUCT_CARDS).first.click()
        self.page.wait_for_timeout(3000)

    def has_results(self) -> bool:
        return self.get_product_count() > 0

    def has_no_results_message(self) -> bool:
        return (
            self.page.locator("text=No results").count() > 0
            or self.page.locator("text=no products found").count() > 0
        )

    def apply_filter(self, filter_name: str):
        """Click a filter option by its label text."""
        self.page.locator(f"text={filter_name}").first.click()
        self.page.wait_for_timeout(2000)
