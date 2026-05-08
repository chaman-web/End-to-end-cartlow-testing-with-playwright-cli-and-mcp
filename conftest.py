import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def base_url():
    return "https://stage.cartlow.com/uae/en"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "record_video_dir": "videos/",
        "record_video_size": {"width": 1280, "height": 800},
    }


@pytest.fixture(autouse=True)
def delete_video_on_pass(request, context):
    yield
    if request.node.rep_call.passed:
        page = context.pages[0] if context.pages else None
        if page and page.video:
            path = page.video.path()
            context.close()
            Path(path).unlink(missing_ok=True)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
