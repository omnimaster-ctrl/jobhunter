# Phase 2: LinkedIn Playwright Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Playwright-based LinkedIn automation engine that can authenticate, search for jobs, extract job data, and submit Easy Apply applications.

**Architecture:** Three Python modules — session manager (auth/health), job searcher (scrape/extract), and job applier (Easy Apply forms). All share a common browser utilities module for anti-detection, delays, and human-like behavior. Uses persistent Chrome profile for session reuse.

**Tech Stack:** Python 3.11+, Playwright for Python, SQLite (from Phase 1 db module), pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `playwright/__init__.py` | Package init |
| `playwright/browser.py` | Browser launch, anti-detection config, human-like utilities |
| `playwright/session_manager.py` | LinkedIn auth check, session health, re-auth notification |
| `playwright/linkedin_search.py` | Build search URLs, scrape job listings, extract job data |
| `playwright/linkedin_apply.py` | Easy Apply form automation, resume upload, form filling |
| `tests/test_browser.py` | Browser utility tests |
| `tests/test_session.py` | Session manager tests (mocked) |
| `tests/test_search.py` | Search URL building and parsing tests |
| `tests/test_apply.py` | Apply form handling tests (mocked) |

---

### Task 1: Browser Utilities Module

**Files:**
- Create: `playwright/__init__.py`
- Create: `playwright/browser.py`
- Create: `tests/test_browser.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_browser.py`:

```python
import pytest
from playwright.browser import (
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_browser.py -v`

- [ ] **Step 3: Implement browser utilities**

Create `playwright/__init__.py`:

```python
# Playwright automation package for JobHunter
```

Create `playwright/browser.py`:

```python
"""Browser launch configuration and human-like interaction utilities."""
import asyncio
import random
from pathlib import Path

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

LINKEDIN_BASE_URL = "https://www.linkedin.com"
USER_DATA_DIR = str(Path.home() / ".jobhunter" / "browser-profile")

# Realistic Chrome on macOS
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
VIEWPORT = {"width": 1920, "height": 1080}


def build_browser_args() -> list[str]:
    """Browser launch arguments for anti-detection."""
    return [
        "--disable-blink-features=AutomationControlled",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-infobars",
        f"--user-agent={USER_AGENT}",
    ]


async def launch_browser(headless: bool = False) -> tuple[Browser, BrowserContext]:
    """Launch Chromium with persistent profile for LinkedIn session reuse."""
    pw = await async_playwright().start()
    context = await pw.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=headless,
        args=build_browser_args(),
        viewport=VIEWPORT,
        user_agent=USER_AGENT,
        locale="en-US",
        timezone_id="America/Mexico_City",
    )
    return pw, context


async def random_delay(min_seconds: float = 2.0, max_seconds: float = 5.0) -> None:
    """Human-like random delay between actions."""
    delay = random.uniform(min_seconds, max_seconds)
    await asyncio.sleep(delay)


async def human_scroll(page: Page, distance: int = 300) -> None:
    """Simulate human-like scrolling."""
    await page.mouse.wheel(0, distance)
    await random_delay(0.5, 1.5)


async def safe_click(page: Page, selector: str, timeout: int = 10000) -> bool:
    """Click an element with delay, return False if not found."""
    try:
        element = page.locator(selector)
        await element.wait_for(state="visible", timeout=timeout)
        await random_delay(0.3, 0.8)
        await element.click()
        return True
    except Exception:
        return False
```

- [ ] **Step 4: Install pytest-asyncio**

Run: `pip3 install --break-system-packages pytest-asyncio`

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_browser.py -v`

- [ ] **Step 6: Commit**

```bash
git add playwright/ tests/test_browser.py
git commit -m "feat: add browser utilities with anti-detection config"
```

---

### Task 2: Session Manager

**Files:**
- Create: `playwright/session_manager.py`
- Create: `tests/test_session.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_session.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from playwright.session_manager import SessionManager


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_session.py -v`

- [ ] **Step 3: Implement SessionManager**

Create `playwright/session_manager.py`:

```python
"""LinkedIn session management — auth check, health monitoring, re-auth flow."""
from playwright.async_api import BrowserContext, Page

from playwright.browser import LINKEDIN_BASE_URL, random_delay


class SessionManager:
    def __init__(self, context: BrowserContext):
        self.context = context
        self.page: Page | None = None
        self._is_authenticated = False

    async def init(self) -> None:
        """Get or create the main page."""
        pages = self.context.pages
        self.page = pages[0] if pages else await self.context.new_page()

    async def check_session(self) -> bool:
        """Check if LinkedIn session is valid by visiting the homepage."""
        await self.page.goto(LINKEDIN_BASE_URL, wait_until="domcontentloaded")
        await random_delay(1.0, 2.0)
        url = self.page.url
        self._is_authenticated = "feed" in url
        return self._is_authenticated

    async def ensure_authenticated(self) -> bool:
        """Check session, return True if authenticated."""
        is_valid = await self.check_session()
        if not is_valid:
            self._is_authenticated = False
        return is_valid

    def status(self) -> dict:
        """Return current session status."""
        return {
            "authenticated": self._is_authenticated,
        }

    async def wait_for_manual_login(self, timeout_seconds: int = 300) -> bool:
        """Open LinkedIn login page and wait for user to log in manually.
        Returns True if login succeeds within timeout."""
        await self.page.goto(
            f"{LINKEDIN_BASE_URL}/login", wait_until="domcontentloaded"
        )
        try:
            await self.page.wait_for_url(
                "**/feed**", timeout=timeout_seconds * 1000
            )
            self._is_authenticated = True
            return True
        except Exception:
            return False
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_session.py -v`

- [ ] **Step 5: Commit**

```bash
git add playwright/session_manager.py tests/test_session.py
git commit -m "feat: add LinkedIn session manager with auth check"
```

---

### Task 3: LinkedIn Job Search

**Files:**
- Create: `playwright/linkedin_search.py`
- Create: `tests/test_search.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_search.py`:

```python
import pytest
from playwright.linkedin_search import build_search_url, parse_job_card


class TestBuildSearchUrl:
    def test_basic_search_url(self):
        url = build_search_url(keywords="Data Engineer")
        assert "linkedin.com/jobs/search" in url
        assert "keywords=Data+Engineer" in url or "keywords=Data%20Engineer" in url

    def test_remote_filter(self):
        url = build_search_url(keywords="Data Engineer", remote=True)
        assert "f_WT=2" in url

    def test_easy_apply_filter(self):
        url = build_search_url(keywords="Data Engineer", easy_apply=True)
        assert "f_EA=true" in url

    def test_experience_level_mid_senior(self):
        url = build_search_url(keywords="Data Engineer", experience_level="mid-senior")
        assert "f_E=4" in url

    def test_job_type_contract(self):
        url = build_search_url(keywords="Data Engineer", job_type="contract")
        assert "f_JT=C" in url

    def test_time_filter_24h(self):
        url = build_search_url(keywords="Data Engineer", posted_within="24h")
        assert "f_TPR=r86400" in url

    def test_time_filter_week(self):
        url = build_search_url(keywords="Data Engineer", posted_within="week")
        assert "f_TPR=r604800" in url

    def test_sort_by_recent(self):
        url = build_search_url(keywords="Data Engineer", sort_by="recent")
        assert "sortBy=DD" in url

    def test_location_filter(self):
        url = build_search_url(keywords="Data Engineer", location="Mexico")
        assert "location=Mexico" in url

    def test_combined_filters(self):
        url = build_search_url(
            keywords="Senior Data Engineer",
            remote=True,
            easy_apply=True,
            experience_level="mid-senior",
            job_type="contract",
            posted_within="week",
            sort_by="recent",
        )
        assert "f_WT=2" in url
        assert "f_EA=true" in url
        assert "f_E=4" in url
        assert "f_JT=C" in url
        assert "f_TPR=r604800" in url
        assert "sortBy=DD" in url


class TestParseJobCard:
    def test_parse_job_card_from_dict(self):
        raw = {
            "title": "Senior Data Engineer",
            "company": "Acme Corp",
            "url": "https://www.linkedin.com/jobs/view/123456",
            "location": "Remote - Mexico",
            "easy_apply": True,
        }
        job = parse_job_card(raw)
        assert job["title"] == "Senior Data Engineer"
        assert job["company"] == "Acme Corp"
        assert job["url"] == "https://www.linkedin.com/jobs/view/123456"
        assert job["easy_apply"] is True

    def test_parse_job_card_normalizes_url(self):
        raw = {
            "title": "Engineer",
            "company": "Co",
            "url": "https://www.linkedin.com/jobs/view/123456?refId=abc&trk=xyz",
        }
        job = parse_job_card(raw)
        assert job["url"] == "https://www.linkedin.com/jobs/view/123456"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_search.py -v`

- [ ] **Step 3: Implement LinkedIn search module**

Create `playwright/linkedin_search.py`:

```python
"""LinkedIn job search — URL construction, page scraping, data extraction."""
from urllib.parse import urlencode, urlparse, urlunparse

from playwright.async_api import Page

from playwright.browser import random_delay, human_scroll, safe_click, LINKEDIN_BASE_URL

EXPERIENCE_LEVELS = {
    "internship": "1",
    "entry": "2",
    "associate": "3",
    "mid-senior": "4",
    "director": "5",
    "executive": "6",
}

JOB_TYPES = {
    "full-time": "F",
    "part-time": "P",
    "contract": "C",
    "temporary": "T",
    "internship": "I",
}

TIME_FILTERS = {
    "24h": "r86400",
    "week": "r604800",
    "month": "r2592000",
}

SORT_OPTIONS = {
    "recent": "DD",
    "relevant": "R",
}


def build_search_url(
    keywords: str,
    location: str = None,
    remote: bool = False,
    easy_apply: bool = False,
    experience_level: str = None,
    job_type: str = None,
    posted_within: str = None,
    sort_by: str = None,
) -> str:
    """Build a LinkedIn job search URL with filters."""
    params = {"keywords": keywords}

    if location:
        params["location"] = location
    if remote:
        params["f_WT"] = "2"
    if easy_apply:
        params["f_EA"] = "true"
    if experience_level and experience_level in EXPERIENCE_LEVELS:
        params["f_E"] = EXPERIENCE_LEVELS[experience_level]
    if job_type and job_type in JOB_TYPES:
        params["f_JT"] = JOB_TYPES[job_type]
    if posted_within and posted_within in TIME_FILTERS:
        params["f_TPR"] = TIME_FILTERS[posted_within]
    if sort_by and sort_by in SORT_OPTIONS:
        params["sortBy"] = SORT_OPTIONS[sort_by]

    return f"{LINKEDIN_BASE_URL}/jobs/search/?{urlencode(params)}"


def parse_job_card(raw: dict) -> dict:
    """Normalize a raw job card dict — clean URL, ensure required fields."""
    url = raw.get("url", "")
    # Strip query params from LinkedIn job URLs
    parsed = urlparse(url)
    clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

    return {
        "title": raw.get("title", "").strip(),
        "company": raw.get("company", "").strip(),
        "url": clean_url,
        "location": raw.get("location", "").strip(),
        "easy_apply": raw.get("easy_apply", False),
        "description": raw.get("description", ""),
    }


async def scrape_job_listings(page: Page, search_url: str, max_jobs: int = 10) -> list[dict]:
    """Navigate to search URL and extract job cards from the results page."""
    await page.goto(search_url, wait_until="domcontentloaded")
    await random_delay(2.0, 4.0)
    await human_scroll(page)

    jobs = []
    # LinkedIn job cards are in a list — selectors may change, but the pattern is stable
    job_cards = page.locator(".job-card-container, .jobs-search-results__list-item")
    count = await job_cards.count()

    for i in range(min(count, max_jobs)):
        try:
            card = job_cards.nth(i)
            await card.scroll_into_view_if_needed()
            await random_delay(0.5, 1.5)

            title_el = card.locator(".job-card-list__title, .job-card-container__link")
            company_el = card.locator(".job-card-container__primary-description, .artdeco-entity-lockup__subtitle")
            location_el = card.locator(".job-card-container__metadata-item, .artdeco-entity-lockup__caption")

            title = await title_el.first.inner_text() if await title_el.count() > 0 else ""
            company = await company_el.first.inner_text() if await company_el.count() > 0 else ""
            location = await location_el.first.inner_text() if await location_el.count() > 0 else ""

            href = await title_el.first.get_attribute("href") if await title_el.count() > 0 else ""
            if href and not href.startswith("http"):
                href = f"{LINKEDIN_BASE_URL}{href}"

            # Check for Easy Apply badge
            easy_apply_badge = card.locator("[aria-label*='Easy Apply'], .job-card-container__apply-method")
            has_easy_apply = await easy_apply_badge.count() > 0

            raw = {
                "title": title,
                "company": company,
                "url": href,
                "location": location,
                "easy_apply": has_easy_apply,
            }
            jobs.append(parse_job_card(raw))
        except Exception:
            continue

    return jobs


async def get_job_description(page: Page, job_url: str) -> str:
    """Navigate to a job posting and extract the full description."""
    await page.goto(job_url, wait_until="domcontentloaded")
    await random_delay(2.0, 4.0)

    desc_locator = page.locator(".jobs-description__content, .jobs-box__html-content")
    if await desc_locator.count() > 0:
        return await desc_locator.first.inner_text()
    return ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_search.py -v`

- [ ] **Step 5: Commit**

```bash
git add playwright/linkedin_search.py tests/test_search.py
git commit -m "feat: add LinkedIn job search with URL builder and page scraper"
```

---

### Task 4: LinkedIn Easy Apply

**Files:**
- Create: `playwright/linkedin_apply.py`
- Create: `tests/test_apply.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_apply.py`:

```python
import pytest
from playwright.linkedin_apply import (
    SUPPORTED_FIELD_TYPES,
    is_easy_apply_supported,
    ApplicationResult,
)


class TestFieldSupport:
    def test_supported_field_types_defined(self):
        assert "text" in SUPPORTED_FIELD_TYPES
        assert "select" in SUPPORTED_FIELD_TYPES
        assert "radio" in SUPPORTED_FIELD_TYPES
        assert "file" in SUPPORTED_FIELD_TYPES

    def test_is_easy_apply_supported_with_basic_form(self):
        fields = [
            {"type": "text", "label": "First name"},
            {"type": "text", "label": "Last name"},
            {"type": "file", "label": "Resume"},
        ]
        assert is_easy_apply_supported(fields) is True

    def test_is_easy_apply_not_supported_with_unknown_fields(self):
        fields = [
            {"type": "unknown_widget", "label": "Custom question"},
        ]
        assert is_easy_apply_supported(fields) is False


class TestApplicationResult:
    def test_success_result(self):
        result = ApplicationResult(
            success=True,
            job_url="https://linkedin.com/jobs/view/123",
            screenshot_path="/tmp/screenshot.png",
        )
        assert result.success is True
        assert result.error is None

    def test_failure_result(self):
        result = ApplicationResult(
            success=False,
            job_url="https://linkedin.com/jobs/view/123",
            error="Unsupported form field type: custom_widget",
        )
        assert result.success is False
        assert "Unsupported" in result.error
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_apply.py -v`

- [ ] **Step 3: Implement Easy Apply module**

Create `playwright/linkedin_apply.py`:

```python
"""LinkedIn Easy Apply automation — form filling, resume upload, submission."""
import os
from dataclasses import dataclass, field
from typing import Optional

from playwright.async_api import Page

from playwright.browser import random_delay, safe_click


SUPPORTED_FIELD_TYPES = {"text", "select", "radio", "checkbox", "file", "textarea"}


@dataclass
class ApplicationResult:
    success: bool
    job_url: str
    screenshot_path: Optional[str] = None
    error: Optional[str] = None
    fields_filled: list[str] = field(default_factory=list)


def is_easy_apply_supported(fields: list[dict]) -> bool:
    """Check if all form fields are in our supported set."""
    return all(f.get("type") in SUPPORTED_FIELD_TYPES for f in fields)


async def detect_form_fields(page: Page) -> list[dict]:
    """Detect form fields in the current Easy Apply modal step."""
    fields = []

    # Text inputs
    text_inputs = page.locator(".jobs-easy-apply-modal input[type='text']")
    for i in range(await text_inputs.count()):
        el = text_inputs.nth(i)
        label = await el.get_attribute("aria-label") or await el.get_attribute("placeholder") or ""
        fields.append({"type": "text", "label": label, "element": el})

    # Textareas
    textareas = page.locator(".jobs-easy-apply-modal textarea")
    for i in range(await textareas.count()):
        el = textareas.nth(i)
        label = await el.get_attribute("aria-label") or ""
        fields.append({"type": "textarea", "label": label, "element": el})

    # Select dropdowns
    selects = page.locator(".jobs-easy-apply-modal select")
    for i in range(await selects.count()):
        el = selects.nth(i)
        label = await el.get_attribute("aria-label") or ""
        fields.append({"type": "select", "label": label, "element": el})

    # Radio buttons
    radios = page.locator(".jobs-easy-apply-modal input[type='radio']")
    if await radios.count() > 0:
        fields.append({"type": "radio", "label": "radio_group", "element": radios.first})

    # File upload
    file_inputs = page.locator(".jobs-easy-apply-modal input[type='file']")
    for i in range(await file_inputs.count()):
        el = file_inputs.nth(i)
        fields.append({"type": "file", "label": "resume", "element": el})

    return fields


async def fill_field(page: Page, field_info: dict, value: str) -> bool:
    """Fill a single form field with the given value."""
    try:
        el = field_info["element"]
        field_type = field_info["type"]

        if field_type in ("text", "textarea"):
            await el.click()
            await random_delay(0.2, 0.5)
            await el.fill(value)
            return True
        elif field_type == "select":
            await el.select_option(label=value)
            return True
        elif field_type == "radio":
            option = page.locator(f"input[type='radio'][value='{value}']")
            if await option.count() > 0:
                await option.first.click()
                return True
            return False
        elif field_type == "file":
            await el.set_input_files(value)
            return True
        return False
    except Exception:
        return False


async def submit_easy_apply(
    page: Page,
    job_url: str,
    resume_path: str,
    answers: dict[str, str] = None,
    screenshot_dir: str = None,
) -> ApplicationResult:
    """Complete the LinkedIn Easy Apply flow for a job.

    Args:
        page: Playwright page with active LinkedIn session
        job_url: URL of the job posting
        resume_path: Path to the PDF resume to upload
        answers: Dict mapping field labels to values for screening questions
        screenshot_dir: Directory to save submission screenshot
    """
    answers = answers or {}
    fields_filled = []

    try:
        # Navigate to job
        await page.goto(job_url, wait_until="domcontentloaded")
        await random_delay(2.0, 4.0)

        # Click Easy Apply button
        easy_apply_btn = page.locator(
            "button[aria-label*='Easy Apply'], "
            ".jobs-apply-button, "
            "button:has-text('Easy Apply')"
        )
        if not await safe_click(page, "button[aria-label*='Easy Apply']"):
            return ApplicationResult(
                success=False,
                job_url=job_url,
                error="Easy Apply button not found",
            )

        await random_delay(1.0, 2.0)

        # Process multi-step form
        max_steps = 10
        for step in range(max_steps):
            await random_delay(1.0, 2.0)

            # Detect fields on current step
            fields = await detect_form_fields(page)

            # Check if all fields are supported
            field_types_only = [{"type": f["type"], "label": f["label"]} for f in fields]
            if not is_easy_apply_supported(field_types_only):
                unsupported = [f["type"] for f in field_types_only if f["type"] not in SUPPORTED_FIELD_TYPES]
                return ApplicationResult(
                    success=False,
                    job_url=job_url,
                    error=f"Unsupported form field type: {', '.join(unsupported)}",
                    fields_filled=fields_filled,
                )

            # Fill fields
            for f in fields:
                if f["type"] == "file":
                    if os.path.exists(resume_path):
                        await fill_field(page, f, resume_path)
                        fields_filled.append("resume_upload")
                elif f["label"] in answers:
                    await fill_field(page, f, answers[f["label"]])
                    fields_filled.append(f["label"])

            # Check for Submit button (final step)
            submit_btn = page.locator(
                "button[aria-label*='Submit application'], "
                "button:has-text('Submit application')"
            )
            if await submit_btn.count() > 0:
                await random_delay(0.5, 1.0)
                await submit_btn.first.click()
                await random_delay(2.0, 3.0)

                # Take screenshot as proof
                screenshot_path = None
                if screenshot_dir:
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = os.path.join(screenshot_dir, "submission.png")
                    await page.screenshot(path=screenshot_path)

                return ApplicationResult(
                    success=True,
                    job_url=job_url,
                    screenshot_path=screenshot_path,
                    fields_filled=fields_filled,
                )

            # Click Next for multi-step forms
            next_btn = page.locator(
                "button[aria-label='Continue to next step'], "
                "button[aria-label*='Next'], "
                "button:has-text('Next')"
            )
            if await next_btn.count() > 0:
                await next_btn.first.click()
            else:
                break

        return ApplicationResult(
            success=False,
            job_url=job_url,
            error="Could not find Submit button after all steps",
            fields_filled=fields_filled,
        )

    except Exception as e:
        return ApplicationResult(
            success=False,
            job_url=job_url,
            error=str(e),
            fields_filled=fields_filled,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd ~/jobhunter && python3 -m pytest tests/test_apply.py -v`

- [ ] **Step 5: Commit**

```bash
git add playwright/linkedin_apply.py tests/test_apply.py
git commit -m "feat: add LinkedIn Easy Apply automation with form detection"
```

---

### Task 5: Integration Test — Full Search Flow

**Files:**
- Create: `tests/test_integration_search.py`

This test runs against the real LinkedIn (requires logged-in session). Mark as manual/skip by default.

- [ ] **Step 1: Write the integration test**

Create `tests/test_integration_search.py`:

```python
"""Integration test for LinkedIn search — requires real session.
Run manually: python3 -m pytest tests/test_integration_search.py -v --run-integration
"""
import pytest
from playwright.browser import launch_browser
from playwright.session_manager import SessionManager
from playwright.linkedin_search import build_search_url, scrape_job_listings


def pytest_addoption(parser):
    parser.addoption("--run-integration", action="store_true", default=False)


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
```

- [ ] **Step 2: Commit**

```bash
git add tests/test_integration_search.py
git commit -m "feat: add LinkedIn search integration test (manual)"
```

---

### Task 6: Run Full Test Suite and Push

- [ ] **Step 1: Run all unit tests**

Run: `cd ~/jobhunter && python3 -m pytest tests/ -v --ignore=tests/test_integration_search.py`
Expected: All tests pass

- [ ] **Step 2: Commit any remaining changes and push**

```bash
git add -A
git commit -m "feat: complete Phase 2 — LinkedIn Playwright engine"
git push origin main
```
