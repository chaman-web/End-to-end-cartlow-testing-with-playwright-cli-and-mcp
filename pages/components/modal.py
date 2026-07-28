"""
ModalComponent — Generic modal/dialog interactions.

Handles confirmation popups (Agree/Disagree), login modals,
and any overlay dialogs site-wide.
"""

from playwright.sync_api import Page


class ModalComponent:
    """Represents modal dialogs and confirmation popups."""

    MODAL_CONTAINER  = "[class*='modal'], [class*='dialog'], [role='dialog']"
    CONFIRM_AGREE    = "button:has-text('Agree'), button:has-text('Yes'), button:has-text('Confirm')"
    CONFIRM_DISAGREE = "button:has-text('Disagree'), button:has-text('No'), button:has-text('Cancel')"
    CLOSE_BTN        = "[class*='modal'] button[class*='close'], [role='dialog'] button[class*='close']"

    def __init__(self, page: Page):
        self.page = page

    def is_visible(self) -> bool:
        """Return True if any modal is currently visible."""
        return self.page.locator(self.MODAL_CONTAINER).first.is_visible()

    def wait_for_modal(self, timeout: int = 5000) -> bool:
        """Wait for a modal to appear. Returns True if it appeared."""
        try:
            self.page.locator(self.MODAL_CONTAINER).first.wait_for(
                state="visible", timeout=timeout
            )
            return True
        except Exception:
            return False

    def get_text(self) -> str:
        """Get the text content of the currently visible modal."""
        modal = self.page.locator(self.MODAL_CONTAINER).first
        if modal.is_visible():
            return modal.inner_text().strip()
        return ""

    def agree(self):
        """Click the Agree / Yes / Confirm button."""
        btn = self.page.locator(self.CONFIRM_AGREE).first
        btn.wait_for(state="visible", timeout=5000)
        btn.click()
        self.page.wait_for_timeout(1500)

    def disagree(self):
        """Click the Disagree / No / Cancel button."""
        btn = self.page.locator(self.CONFIRM_DISAGREE).first
        btn.wait_for(state="visible", timeout=5000)
        btn.click()
        self.page.wait_for_timeout(1500)

    def close(self):
        """Click the X close button on the modal."""
        btn = self.page.locator(self.CLOSE_BTN).first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
            self.page.wait_for_timeout(1000)

    def agree_if_present(self, timeout: int = 3000) -> bool:
        """Click Agree if a modal appears within timeout. Returns True if clicked."""
        try:
            btn = self.page.locator(self.CONFIRM_AGREE).first
            btn.wait_for(state="visible", timeout=timeout)
            btn.click()
            self.page.wait_for_timeout(1500)
            return True
        except Exception:
            return False
