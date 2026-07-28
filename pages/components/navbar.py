"""
NavbarComponent — Top navigation bar interactions.

Shared across all pages (search bar, channel switcher, cart icon, account menu).
"""

from playwright.sync_api import Page


class NavbarComponent:
    """Represents the top navigation bar present on every page."""

    SEARCH_INPUT    = "input[placeholder*='Search'], input[type='search']"
    CART_ICON       = "[class*='cart-icon'], [href*='checkout/cart'], [class*='cart-btn']"
    ACCOUNT_ICON    = "[class*='account'], [class*='user-icon'], [class*='profile']"
    CHANNEL_BUTTON  = "button:has-text('UAE'), button:has-text('INTL'), button:has-text('KSA')"
    CHANNEL_OPTIONS = "span.cursor-pointer, li[class*='channel'], div[class*='country']"
    LOGO            = "a[href='/'], [class*='logo'] a, [class*='brand'] a"

    def __init__(self, page: Page):
        self.page = page

    def search(self, keyword: str):
        """Type into the search bar and submit."""
        search = self.page.locator(self.SEARCH_INPUT).first
        search.wait_for(state="visible", timeout=8000)
        search.fill(keyword)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(3000)

    def go_to_cart(self):
        """Click the cart icon to open cart page."""
        self.page.locator(self.CART_ICON).first.click()
        self.page.wait_for_timeout(3000)

    def go_to_account(self):
        """Click the account/profile icon."""
        self.page.locator(self.ACCOUNT_ICON).first.click()
        self.page.wait_for_timeout(2000)

    def click_logo(self):
        """Click the site logo to go to homepage."""
        self.page.locator(self.LOGO).first.click()
        self.page.wait_for_timeout(3000)

    def get_active_channel(self) -> str:
        """Return the currently active channel label (e.g. 'UAE', 'INTL')."""
        btn = self.page.locator(self.CHANNEL_BUTTON).first
        return btn.inner_text().strip() if btn.count() > 0 else ""

    def switch_channel(self, channel: str):
        """
        Switch to a different storefront channel.
        channel: 'INTL' | 'UAE' | 'KSA'
        """
        self.page.locator(self.CHANNEL_BUTTON).first.click()
        self.page.wait_for_timeout(1500)
        self.page.evaluate(
            f"() => [...document.querySelectorAll('span,div,li')]"
            f".find(e => e.innerText.trim() === '{channel}' && e.offsetParent)?.click()"
        )
        self.page.wait_for_timeout(5000)
