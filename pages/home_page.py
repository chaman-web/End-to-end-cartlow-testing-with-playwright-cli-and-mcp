"""
HomePage — Cartlow storefront homepage interactions.
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class HomePage(BasePage):

    # ── Locators ───────────────────────────────────────────────────────────────
    SEARCH_INPUT     = "input[type='search'], input[placeholder*='Search'], #search-input"
    SEARCH_BUTTON    = "button[type='submit'], button:has-text('Search')"
    NAV_LINKS        = "nav a"
    BANNER_CONTAINER = ".banner, .hero, [class*='banner'], [class*='hero']"

    def __init__(self, page: Page):
        super().__init__(page)

    def open(self, base_url: str):
        """Navigate to homepage."""
        self.goto(base_url)
        self.page.wait_for_timeout(5000)

    def search(self, keyword: str):
        """Type keyword in search bar and submit."""
        self.page.locator(self.SEARCH_INPUT).first.fill(keyword)
        self.page.wait_for_timeout(300)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(3000)

    def get_nav_links(self) -> list:
        """Return all visible nav link texts."""
        links = self.page.locator(self.NAV_LINKS)
        return [links.nth(i).inner_text().strip() for i in range(links.count())]

    def is_banner_visible(self) -> bool:
        return self.page.locator(self.BANNER_CONTAINER).first.is_visible()

    def click_gift_cards(self):
        """Navigate to Gift Cards section."""
        self.page.locator("text=Gift Cards").first.click()
        self.page.wait_for_timeout(3000)
