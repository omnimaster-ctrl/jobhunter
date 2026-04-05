"""Integration test for LinkedIn search — requires real session.
Run manually: python3 -m pytest tests/test_integration_search.py -v --run-integration
"""
import pytest
from linkedin.browser import launch_browser
from linkedin.session_manager import SessionManager
from linkedin.linkedin_search import build_search_url, scrape_job_listings


@pytest.fixture
def run_integration(request):
    if not request.config.getoption("--run-integration"):
        pytest.skip("Integration tests require --run-integration flag")


@pytest.mark.asyncio
async def test_search_returns_jobs(run_integration):
    pw, context = await launch_browser(headless=False)
    try:
        session = SessionManager(context)
        await session.init()

        is_auth = await session.check_session()
        if not is_auth:
            print("Not logged in — waiting for manual login...")
            await session.wait_for_manual_login(timeout_seconds=120)

        url = build_search_url(
            keywords="Data Engineer",
            remote=True,
            easy_apply=True,
            location="Mexico",
        )

        page = session.page
        jobs = await scrape_job_listings(page, url, max_jobs=5)

        assert len(jobs) > 0
        for job in jobs:
            assert job["title"]
            assert job["url"]
            print(f"  Found: {job['title']} at {job['company']}")
    finally:
        await context.close()
        await pw.stop()
