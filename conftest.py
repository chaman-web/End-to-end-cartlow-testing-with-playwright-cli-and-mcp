import pytest


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
