import pytest
from unittest.mock import AsyncMock
from linkedin.session_manager import SessionManager


class TestSessionCheck:
    @pytest.mark.asyncio
    async def test_session_valid_when_url_contains_feed(self):
        mock_page = AsyncMock()
        mock_page.url = "https://www.linkedin.com/feed/"
        mock_page.goto = AsyncMock()
        manager = SessionManager.__new__(SessionManager)
        manager.page = mock_page
        result = await manager.check_session()
        assert result is True

    @pytest.mark.asyncio
    async def test_session_invalid_when_url_is_login(self):
        mock_page = AsyncMock()
        mock_page.url = "https://www.linkedin.com/login"
        mock_page.goto = AsyncMock()
        manager = SessionManager.__new__(SessionManager)
        manager.page = mock_page
        result = await manager.check_session()
        assert result is False


class TestSessionStatus:
    def test_status_returns_dict(self):
        manager = SessionManager.__new__(SessionManager)
        manager._is_authenticated = True
        status = manager.status()
        assert status["authenticated"] is True
