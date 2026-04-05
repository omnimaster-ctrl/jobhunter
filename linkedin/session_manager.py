"""LinkedIn session management — authentication checks and login helpers."""

import asyncio

from linkedin.browser import LINKEDIN_BASE_URL, random_delay


class SessionManager:
    """Manages a LinkedIn browser session within a given BrowserContext."""

    def __init__(self, context) -> None:
        self.context = context
        self.page = None
        self._is_authenticated: bool = False

    async def init(self) -> None:
        """Get the first open page or create one."""
        pages = self.context.pages
        if pages:
            self.page = pages[0]
        else:
            self.page = await self.context.new_page()

    async def check_session(self) -> bool:
        """Navigate to LinkedIn home and return True if the user is logged in."""
        await self.page.goto(LINKEDIN_BASE_URL, wait_until="domcontentloaded")
        await random_delay(1.0, 2.0)
        self._is_authenticated = "feed" in self.page.url
        return self._is_authenticated

    async def ensure_authenticated(self) -> bool:
        """Return True if the current session is authenticated."""
        return await self.check_session()

    def status(self) -> dict:
        """Return a dict describing the current authentication state."""
        return {"authenticated": self._is_authenticated}

    async def wait_for_manual_login(self, timeout_seconds: int = 300) -> bool:
        """
        Navigate to the LinkedIn login page and wait for the user to log in manually.

        Returns True once the feed URL is detected, False on timeout.
        """
        login_url = f"{LINKEDIN_BASE_URL}/login"
        await self.page.goto(login_url, wait_until="domcontentloaded")

        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while asyncio.get_event_loop().time() < deadline:
            if "feed" in self.page.url:
                self._is_authenticated = True
                return True
            await asyncio.sleep(2)

        self._is_authenticated = False
        return False
