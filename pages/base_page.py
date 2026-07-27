"""
BasePage — inherited by all page objects.
Provides common utilities: navigation, waiting, channel switching.
"""

from playwright.sync_api import Page


class BasePage:
    """Base class for all page objects."""

    def __init__(self, page: Page):
        self.page = page

    # ── Navigation ─────────────────────────────────────────────────────────────

    def goto(self, url: str, wait_until: str = "domcontentloaded", timeout: int = 60000):
        """Navigate to a URL with retry."""
        for attempt in range(3):
            try:
                self.page.goto(url, wait_until=wait_until, timeout=timeout)
                return
            except Exception:
                self.page.wait_for_timeout(5000)

    def reload(self):
        self.page.reload(wait_until="domcontentloaded", timeout=60000)

    # ── Waiting ────────────────────────────────────────────────────────────────

    def wait(self, ms: int):
        self.page.wait_for_timeout(ms)

    def wait_for_text(self, text: str, timeout: int = 10000):
        self.page.wait_for_selector(f"text={text}", timeout=timeout)

    # ── Body text ──────────────────────────────────────────────────────────────

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def has_text(self, text: str) -> bool:
        return text in self.body_text()

    # ── Scroll ─────────────────────────────────────────────────────────────────

    def scroll_down(self, steps: int = 15, delay_ms: int = 200):
        """Scroll down to reveal lazy-loaded elements."""
        for _ in range(steps):
            self.page.mouse.wheel(0, 200)
            self.page.wait_for_timeout(delay_ms)
        self.page.wait_for_timeout(1000)

    # ── Channel switcher ───────────────────────────────────────────────────────

    def switch_channel(self, channel: str):
        """Switch storefront channel, e.g. 'INTL', 'UAE', 'KSA'."""
        self.page.evaluate(
            "() => [...document.querySelectorAll('button')]"
            ".find(b => b.innerText.includes('UAE') || b.innerText.includes('KSA')"
            " || b.innerText.includes('INTL'))?.click()"
        )
        self.page.wait_for_timeout(1500)
        self.page.evaluate(
            f"() => [...document.querySelectorAll('span,div,li')]"
            f".find(e => e.innerText.trim() === '{channel}' && e.offsetParent)?.click()"
        )
        self.page.wait_for_timeout(5000)
