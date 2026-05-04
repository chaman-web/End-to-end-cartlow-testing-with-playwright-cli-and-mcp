from playwright.sync_api import Page


def test_page_title(page: Page, base_url):
    page.goto(base_url)
    assert page.title() != ""


def test_navigation(page: Page, base_url):
    page.goto(base_url)
    page.get_by_role("link", name="More information").click()
    page.wait_for_load_state("networkidle")
    assert "iana" in page.url
