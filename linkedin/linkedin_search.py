"""LinkedIn job search utilities: URL builder, job card parser, and async scrapers."""

from urllib.parse import urlencode, urlparse, urlunparse

EXPERIENCE_LEVELS = {
    "internship": 1,
    "entry": 2,
    "associate": 3,
    "mid-senior": 4,
    "director": 5,
    "executive": 6,
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
    """Build a LinkedIn job search URL with the given filters."""
    params = {"keywords": keywords}

    if location:
        params["location"] = location

    if remote:
        params["f_WT"] = "2"

    if easy_apply:
        params["f_EA"] = "true"

    if experience_level and experience_level in EXPERIENCE_LEVELS:
        params["f_E"] = str(EXPERIENCE_LEVELS[experience_level])

    if job_type and job_type in JOB_TYPES:
        params["f_JT"] = JOB_TYPES[job_type]

    if posted_within and posted_within in TIME_FILTERS:
        params["f_TPR"] = TIME_FILTERS[posted_within]

    if sort_by and sort_by in SORT_OPTIONS:
        params["sortBy"] = SORT_OPTIONS[sort_by]

    return f"https://www.linkedin.com/jobs/search?{urlencode(params)}"


def parse_job_card(raw: dict) -> dict:
    """Normalize a raw job card dict, stripping query params from the URL."""
    job = dict(raw)

    if "url" in job and job["url"]:
        parsed = urlparse(job["url"])
        clean = parsed._replace(query="", fragment="")
        job["url"] = urlunparse(clean)

    return job


async def scrape_job_listings(page, search_url: str, max_jobs: int = 10) -> list:
    """Navigate to a LinkedIn search URL and extract job cards."""
    await page.goto(search_url, wait_until="domcontentloaded")

    jobs = []
    seen_ids = set()

    # Scroll to load more jobs up to max_jobs
    while len(jobs) < max_jobs:
        cards = await page.query_selector_all(".job-search-card, .jobs-search-results__list-item")
        if not cards:
            break

        for card in cards:
            if len(jobs) >= max_jobs:
                break

            try:
                title_el = await card.query_selector(".job-search-card__title, .job-card-list__title")
                company_el = await card.query_selector(".job-search-card__company-name, .job-card-container__company-name")
                location_el = await card.query_selector(".job-search-card__location, .job-card-container__metadata-item")
                link_el = await card.query_selector("a[href*='/jobs/view/']")
                easy_apply_el = await card.query_selector(".job-search-card__easy-apply-label, .job-card-container__apply-method")

                title = (await title_el.inner_text()).strip() if title_el else ""
                company = (await company_el.inner_text()).strip() if company_el else ""
                location = (await location_el.inner_text()).strip() if location_el else ""
                url = await link_el.get_attribute("href") if link_el else ""
                easy_apply = easy_apply_el is not None

                if not url:
                    continue

                raw = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "easy_apply": easy_apply,
                }
                job = parse_job_card(raw)

                if job["url"] not in seen_ids:
                    seen_ids.add(job["url"])
                    jobs.append(job)
            except Exception:
                continue

        if len(cards) < max_jobs:
            break

        # Scroll down to load more
        await page.evaluate("window.scrollBy(0, 800)")
        await page.wait_for_timeout(1000)

    return jobs[:max_jobs]


async def get_job_description(page, job_url: str) -> str:
    """Navigate to a job posting and extract the full description text."""
    await page.goto(job_url, wait_until="domcontentloaded")

    selectors = [
        ".jobs-description__content",
        ".jobs-box__html-content",
        ".description__text",
        "[class*='description']",
    ]

    for selector in selectors:
        el = await page.query_selector(selector)
        if el:
            return (await el.inner_text()).strip()

    return ""
