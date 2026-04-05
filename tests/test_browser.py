import pytest
from linkedin.browser import (
    build_browser_args,
    random_delay,
    LINKEDIN_BASE_URL,
    USER_DATA_DIR,
)


class TestBrowserConfig:
    def test_build_browser_args_returns_list(self):
        args = build_browser_args()
        assert isinstance(args, list)
        assert "--disable-blink-features=AutomationControlled" in args

    def test_user_data_dir_is_jobhunter_path(self):
        assert ".jobhunter/browser-profile" in USER_DATA_DIR

    def test_linkedin_base_url(self):
        assert LINKEDIN_BASE_URL == "https://www.linkedin.com"


class TestRandomDelay:
    @pytest.mark.asyncio
    async def test_random_delay_within_range(self):
        import time

        start = time.time()
        await random_delay(0.1, 0.2)
        elapsed = time.time() - start
        assert 0.09 <= elapsed <= 0.3
