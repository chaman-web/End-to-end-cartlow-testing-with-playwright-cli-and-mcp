"""
PaymentPage — Payment method selection and processing.
"""

from playwright.sync_api import Page
from pages.base_page import BasePage


class PaymentPage(BasePage):

    # ── Locators ───────────────────────────────────────────────────────────────
    COD_OPTION         = "text=Cash on Delivery, text=COD"
    CARD_OPTION        = "text=Credit Card, text=Debit Card, text=Card"
    TABBY_OPTION       = "text=Tabby"
    TAMARA_OPTION      = "text=Tamara"
    WALLET_OPTION      = "text=Wallet"
    CARD_NUMBER        = "input[name*='card'], input[placeholder*='Card Number']"
    CARD_EXPIRY        = "input[name*='expiry'], input[placeholder*='MM/YY']"
    CARD_CVV           = "input[name*='cvv'], input[placeholder*='CVV']"
    CONFIRM_BTN        = "button:has-text('Confirm'), button:has-text('Pay Now')"

    def __init__(self, page: Page):
        super().__init__(page)

    def select_cod(self):
        self.page.locator(self.COD_OPTION).first.click()
        self.page.wait_for_timeout(1000)

    def select_card(self):
        self.page.locator(self.CARD_OPTION).first.click()
        self.page.wait_for_timeout(1000)

    def select_tabby(self):
        self.page.locator(self.TABBY_OPTION).first.click()
        self.page.wait_for_timeout(1000)

    def select_tamara(self):
        self.page.locator(self.TAMARA_OPTION).first.click()
        self.page.wait_for_timeout(1000)

    def fill_card_details(self, number: str, expiry: str, cvv: str):
        self.page.locator(self.CARD_NUMBER).fill(number)
        self.page.locator(self.CARD_EXPIRY).fill(expiry)
        self.page.locator(self.CARD_CVV).fill(cvv)
        self.page.wait_for_timeout(500)

    def confirm_payment(self):
        btn = self.page.locator(self.CONFIRM_BTN).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()
        self.page.wait_for_timeout(5000)

    def get_available_methods(self) -> list:
        """Return all visible payment method option texts."""
        options = self.page.evaluate("""
            () => [...document.querySelectorAll('input[type="radio"]')]
                .filter(r => r.offsetParent !== null)
                .map(r => {
                    const label = document.querySelector(`label[for="${r.id}"]`);
                    return label ? label.innerText.trim() : r.value;
                })
                .filter(Boolean)
        """)
        return options
