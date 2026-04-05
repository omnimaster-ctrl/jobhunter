"""Browser configuration and utilities for LinkedIn automation."""

import asyncio
import random
from pathlib import Path

from playwright.async_api import async_playwright

LINKEDIN_BASE_URL = "https://www.linkedin.com"

USER_DATA_DIR = str(Path.home() / ".jobhunter" / "browser-profile")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

VIEWPORT = {"width": 1920, "height": 1080}


def build_browser_args() -> list[str]:
    """Return Chromium launch arguments that reduce automation detection."""
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-infobars",
        "--disable-extensions",
        f"--window-size={VIEWPORT['width']},{VIEWPORT['height']}",
    ]


async def launch_browser(headless: bool = False):
    """Launch Chromium with a persistent profile and return (playwright, context)."""
    pw = await async_playwright().start()
    Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
    context = await pw.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=headless,
        args=build_browser_args(),
        user_agent=USER_AGENT,
        viewport=VIEWPORT,
        locale="en-US",
    )
    return pw, context


async def random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """Sleep for a random duration between min_seconds and max_seconds."""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def human_scroll(page, distance: int = 300) -> None:
    """Scroll the page by distance pixels then wait a random delay."""
    await page.mouse.wheel(0, distance)
    await random_delay(0.5, 1.5)


async def safe_click(page, selector: str, timeout: int = 10000) -> bool:
    """Click an element by selector; return False if not found within timeout."""
    try:
        await page.click(selector, timeout=timeout)
        await random_delay(0.5, 1.5)
        return True
    except Exception:
        return False
