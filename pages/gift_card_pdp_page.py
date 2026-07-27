"""
GiftCardPDPPage — Gift Card Product Detail Page.
Extends PDPPage with gift recipient option interactions.

DOM facts (confirmed from live inspection):
  - Radio inputs : name="pdp_gift_recipient_choice"
  - value="self"    → Myself (Keep it for you)
  - value="someone" → Gift it (Send to someone)
  - Labels         : class="pdp-gift-recipient-option"
  - Default        : Myself (value="self")
  - Gift form fields:
      #gift-card-recipient-name     — Recipient name (required)
      #gift-card-recipient-contact  — Email or mobile number (required)
      #gift-card-recipient-note     — Personal message (optional)
"""

from playwright.sync_api import Page
from pages.pdp_page import PDPPage


class GiftCardPDPPage(PDPPage):

    # ── Locators ───────────────────────────────────────────────────────────────
    RADIO_MYSELF      = "input[name='pdp_gift_recipient_choice'][value='self']"
    RADIO_GIFT_IT     = "input[name='pdp_gift_recipient_choice'][value='someone']"
    RECIPIENT_LABEL   = "label.pdp-gift-recipient-option"
    RECIPIENT_NAME    = "#gift-card-recipient-name"
    RECIPIENT_CONTACT = "#gift-card-recipient-contact"
    RECIPIENT_NOTE    = "#gift-card-recipient-note"

    def __init__(self, page: Page):
        super().__init__(page)

    # ── Option selection ───────────────────────────────────────────────────────

    def select_myself(self):
        """Select the 'Myself / Keep it for you' option."""
        self.page.evaluate(
            "() => { const input = document.querySelector"
            "('input[name=\"pdp_gift_recipient_choice\"][value=\"self\"]');"
            " if (input) input.closest('label')?.click(); }"
        )
        self.page.wait_for_timeout(1000)

    def select_gift_it(self):
        """Select the 'Gift it / Send to someone' option."""
        self.page.evaluate(
            "() => { const input = document.querySelector"
            "('input[name=\"pdp_gift_recipient_choice\"][value=\"someone\"]');"
            " if (input) input.closest('label')?.click(); }"
        )
        self.page.wait_for_timeout(1000)

    def get_selected_option(self) -> str | None:
        """Return the currently checked radio value ('self' or 'someone')."""
        return self.page.evaluate("""
            () => {
                const radios = [...document.querySelectorAll(
                    'input[name="pdp_gift_recipient_choice"]'
                )];
                const checked = radios.find(r => r.checked);
                return checked ? checked.value : null;
            }
        """)

    def is_gift_it_selected(self) -> bool:
        return self.get_selected_option() == "someone"

    def is_myself_selected(self) -> bool:
        return self.get_selected_option() == "self"

    # ── Gift form ──────────────────────────────────────────────────────────────

    def is_gift_form_visible(self) -> bool:
        return self.page.locator(self.RECIPIENT_NAME).is_visible()

    def fill_recipient_name(self, name: str):
        field = self.page.locator(self.RECIPIENT_NAME)
        field.wait_for(state="visible", timeout=8000)
        field.fill(name)
        self.page.wait_for_timeout(300)

    def fill_recipient_contact(self, contact: str):
        """Fill email or mobile number. Always fill name first."""
        field = self.page.locator(self.RECIPIENT_CONTACT)
        field.wait_for(state="visible", timeout=5000)
        field.fill(contact)
        self.page.wait_for_timeout(300)

    def fill_personal_message(self, message: str):
        if not message:
            return
        note = self.page.locator(self.RECIPIENT_NOTE)
        note.wait_for(state="visible", timeout=5000)
        note.fill(message)
        self.page.wait_for_timeout(300)

    def fill_gift_form(self, name: str, contact: str, message: str = ""):
        """Fill the full gift recipient form (name + contact + optional message)."""
        self.fill_recipient_name(name)
        self.fill_recipient_contact(contact)
        self.fill_personal_message(message)

    # ── Validation helpers ─────────────────────────────────────────────────────

    def get_name_field_errors(self) -> list:
        errors = self.page.evaluate("""
            () => {
                const nameField = document.querySelector('#gift-card-recipient-name');
                if (!nameField) return [];
                const container = nameField.closest('div');
                return container
                    ? [...container.querySelectorAll('[class*="error"],[class*="invalid"],[class*="message"]')]
                        .map(e => e.innerText.trim()).filter(Boolean)
                    : [];
            }
        """)
        return errors

    def is_contact_field_invalid(self) -> bool:
        return self.page.evaluate("""
            () => {
                const el = document.querySelector('#gift-card-recipient-contact');
                return el ? !el.validity.valid : false;
            }
        """)
