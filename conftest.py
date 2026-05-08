import pytest


@pytest.fixture(scope="session")
def base_url():
    return "https://stage.cartlow.com/uae/en"


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
