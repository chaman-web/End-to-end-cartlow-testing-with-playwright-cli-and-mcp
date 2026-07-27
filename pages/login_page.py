"""
LoginPage — Handles login modal interactions.
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class LoginPage(BasePage):

    # ── Locators ───────────────────────────────────────────────────────────────
    EMAIL_INPUT    = "#login-email"
    PASSWORD_INPUT = "#login-password"

    def __init__(self, page: Page):
        super().__init__(page)

    def open_login_modal(self):
        """Trigger the login modal via Vue emitter."""
        for _ in range(15):
            try:
                self.page.evaluate(
                    "document.querySelector('#app').__vue_app__.config.globalProperties"
                    ".$emitter.emit('open-customer-auth-modal')"
                )
                self.page.locator(self.EMAIL_INPUT).wait_for(state="visible", timeout=3000)
                self.page.wait_for_timeout(500)
                self.page.locator(self.EMAIL_INPUT).evaluate("el => el.focus()")
                if self.page.locator(self.EMAIL_INPUT).evaluate(
                    "el => document.activeElement === el"
                ):
                    break
            except Exception:
                self.page.wait_for_timeout(1500)

    def fill_email(self, email: str):
        self.page.locator(self.EMAIL_INPUT).fill(email)

    def fill_password(self, password: str):
        self.page.locator(self.PASSWORD_INPUT).fill(password)

    def click_sign_in(self):
        self.page.evaluate(
            "() => [...document.querySelectorAll('button')]"
            ".find(b => b.innerText.trim() === 'Sign In' && b.offsetParent !== null)?.click()"
        )
        self.page.wait_for_timeout(6000)

    def login(self, email: str, password: str):
        """Full login flow: open modal → fill credentials → sign in."""
        self.open_login_modal()
        self.fill_email(email)
        self.fill_password(password)
        self.click_sign_in()

    def is_logged_in(self) -> bool:
        return self.page.locator("text=Hello,").count() > 0
