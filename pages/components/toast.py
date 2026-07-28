"""
ToastComponent — Toast / snackbar notification interactions.

Used to verify success/error messages after actions like Add to Cart,
login, order placement, etc.
"""

from playwright.sync_api import Page


class ToastComponent:
    """Represents transient toast/snackbar notifications."""

    TOAST_SELECTORS = [
        "[class*='toast']",
        "[class*='snackbar']",
        "[class*='notification']",
        "[class*='alert']:not([role='dialog'])",
        "[class*='message']:not(p):not(span)",
    ]

    def __init__(self, page: Page):
        self.page = page

    def _selector(self) -> str:
        return ", ".join(self.TOAST_SELECTORS)

    def wait_for_toast(self, timeout: int = 8000) -> str:
        """Wait for a toast to appear and return its text."""
        try:
            toast = self.page.locator(self._selector()).first
            toast.wait_for(state="visible", timeout=timeout)
            return toast.inner_text().strip()
        except Exception:
            return ""

    def get_text(self) -> str:
        """Get visible toast text without waiting."""
        toast = self.page.locator(self._selector()).first
        if toast.count() > 0 and toast.is_visible():
            return toast.inner_text().strip()
        return ""

    def is_success(self) -> bool:
        """Check if a success toast is visible."""
        text = self.get_text().lower()
        return any(kw in text for kw in ["success", "added", "done", "complete", "placed"])

    def is_error(self) -> bool:
        """Check if an error toast is visible."""
        text = self.get_text().lower()
        return any(kw in text for kw in ["error", "failed", "invalid", "wrong", "unable"])

    def wait_for_success(self, timeout: int = 8000) -> bool:
        """Wait up to timeout ms for a success toast."""
        text = self.wait_for_toast(timeout).lower()
        return any(kw in text for kw in ["success", "added", "done", "complete", "placed"])

    def wait_for_error(self, timeout: int = 8000) -> bool:
        """Wait up to timeout ms for an error toast."""
        text = self.wait_for_toast(timeout).lower()
        return any(kw in text for kw in ["error", "failed", "invalid", "wrong", "unable"])

    def dismiss(self):
        """Click close button on toast if present."""
        close = self.page.locator(
            f"{self._selector()} button, {self._selector()} [class*='close']"
        ).first
        if close.count() > 0 and close.is_visible():
            close.click()
            self.page.wait_for_timeout(500)
