"""LinkedIn messaging inbox reader: scrape recent messages for job offers."""

import re
from urllib.parse import urlparse, urlunparse

from linkedin.browser import random_delay, human_scroll

MESSAGING_URL = "https://www.linkedin.com/messaging/"

# Patterns that indicate a job-related message
JOB_KEYWORDS = [
    "opportunity", "position", "role", "opening", "hiring",
    "job", "candidate", "apply", "interested", "data engineer",
    "engineer", "developer", "architect", "contractor", "remote",
    "freelance", "offer", "recruit",
]

# Regex to find LinkedIn job URLs in message text
LINKEDIN_JOB_URL_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/(?:jobs/view|jobs/collections|comm/jobs/view)/[\w-]+/?",
    re.IGNORECASE,
)

# Also match shortened LinkedIn URLs
LINKEDIN_SHORT_URL_RE = re.compile(
    r"https?://lnkd\.in/[\w-]+",
    re.IGNORECASE,
)


def extract_job_urls(text: str) -> list[str]:
    """Extract LinkedIn job URLs from message text."""
    urls = LINKEDIN_JOB_URL_RE.findall(text)
    urls += LINKEDIN_SHORT_URL_RE.findall(text)
    # Normalize: strip query params
    cleaned = []
    for url in urls:
        parsed = urlparse(url)
        clean = parsed._replace(query="", fragment="")
        cleaned.append(urlunparse(clean))
    return list(dict.fromkeys(cleaned))  # deduplicate preserving order


def looks_like_job_offer(text: str) -> bool:
    """Check if message text likely contains a job offer based on keywords."""
    lower = text.lower()
    matches = sum(1 for kw in JOB_KEYWORDS if kw in lower)
    return matches >= 2


def parse_conversation_preview(raw: dict) -> dict:
    """Normalize a raw conversation preview dict.

    Expected keys from scraping:
      - sender: str (name of the sender)
      - snippet: str (message preview text)
      - timestamp: str (relative time like "2h ago")
      - url: str (conversation URL)
      - unread: bool
    """
    return {
        "sender": raw.get("sender", "").strip(),
        "snippet": raw.get("snippet", "").strip(),
        "timestamp": raw.get("timestamp", "").strip(),
        "url": raw.get("url", ""),
        "unread": raw.get("unread", False),
    }


async def scrape_conversations(page, max_conversations: int = 15) -> list[dict]:
    """Navigate to LinkedIn messaging and extract recent conversation previews."""
    await page.goto(MESSAGING_URL, wait_until="domcontentloaded")
    await random_delay(2.0, 4.0)

    conversations = []
    seen = set()

    # LinkedIn messaging list selectors
    list_selectors = [
        ".msg-conversations-container__conversations-list li",
        ".msg-conversation-listitem",
        "[data-control-name='overlay.messaging_conversation']",
        ".msg-conversation-card",
    ]

    items = []
    for sel in list_selectors:
        items = await page.query_selector_all(sel)
        if items:
            break

    if not items:
        return []

    for item in items[:max_conversations]:
        try:
            # Sender name
            name_el = await item.query_selector(
                ".msg-conversation-card__participant-names, "
                ".msg-conversation-listitem__participant-names, "
                "[class*='participant-name']"
            )
            sender = (await name_el.inner_text()).strip() if name_el else ""

            # Message snippet
            snippet_el = await item.query_selector(
                ".msg-conversation-card__message-snippet, "
                ".msg-conversation-listitem__message-snippet, "
                "[class*='message-snippet']"
            )
            snippet = (await snippet_el.inner_text()).strip() if snippet_el else ""

            # Timestamp
            time_el = await item.query_selector(
                ".msg-conversation-card__time-stamp, "
                ".msg-conversation-listitem__time-stamp, "
                "time"
            )
            timestamp = (await time_el.inner_text()).strip() if time_el else ""

            # Conversation link
            link_el = await item.query_selector("a[href*='/messaging/thread/']")
            url = await link_el.get_attribute("href") if link_el else ""

            # Unread indicator
            unread_el = await item.query_selector(
                ".msg-conversation-card__unread-count, "
                "[class*='unread']"
            )
            unread = unread_el is not None

            if sender and sender not in seen:
                seen.add(sender)
                conversations.append(parse_conversation_preview({
                    "sender": sender,
                    "snippet": snippet,
                    "timestamp": timestamp,
                    "url": url,
                    "unread": unread,
                }))
        except Exception:
            continue

    return conversations


async def read_conversation(page, conversation_url: str, max_messages: int = 20) -> list[dict]:
    """Open a conversation and extract recent messages."""
    await page.goto(
        f"https://www.linkedin.com{conversation_url}" if conversation_url.startswith("/") else conversation_url,
        wait_until="domcontentloaded",
    )
    await random_delay(2.0, 4.0)

    messages = []

    # Scroll up to load more messages
    msg_container = await page.query_selector(
        ".msg-s-message-list, [class*='message-list']"
    )
    if msg_container:
        await human_scroll(page, -500)
        await random_delay(1.0, 2.0)

    # Message selectors
    msg_selectors = [
        ".msg-s-message-list__event",
        ".msg-s-event-listitem",
        "[class*='msg-s-event']",
    ]

    items = []
    for sel in msg_selectors:
        items = await page.query_selector_all(sel)
        if items:
            break

    for item in items[-max_messages:]:
        try:
            # Sender
            sender_el = await item.query_selector(
                ".msg-s-message-group__name, "
                "[class*='message-group__name'], "
                "[class*='sender']"
            )
            sender = (await sender_el.inner_text()).strip() if sender_el else ""

            # Message body
            body_el = await item.query_selector(
                ".msg-s-event-listitem__body, "
                "[class*='event-listitem__body'], "
                "[class*='message-body']"
            )
            body = (await body_el.inner_text()).strip() if body_el else ""

            # Timestamp
            time_el = await item.query_selector("time")
            timestamp = (await time_el.get_attribute("datetime")) if time_el else ""

            if body:
                messages.append({
                    "sender": sender,
                    "body": body,
                    "timestamp": timestamp,
                    "job_urls": extract_job_urls(body),
                    "is_job_offer": looks_like_job_offer(body),
                })
        except Exception:
            continue

    return messages


async def find_job_offers_in_inbox(page, max_conversations: int = 15) -> list[dict]:
    """Scan recent conversations and return those containing job offers.

    Returns a list of dicts with:
      - sender: who sent it
      - snippet: preview text
      - conversation_url: link to open the conversation
      - job_urls: list of LinkedIn job URLs found
      - messages: list of relevant message dicts from the conversation
    """
    conversations = await scrape_conversations(page, max_conversations)
    results = []

    for conv in conversations:
        # Check snippet first for quick filtering
        snippet_has_job = looks_like_job_offer(conv["snippet"])
        snippet_has_url = bool(extract_job_urls(conv["snippet"]))

        if not snippet_has_job and not snippet_has_url and not conv["unread"]:
            continue

        # Open conversation and read messages
        if conv["url"]:
            messages = await read_conversation(page, conv["url"])

            job_messages = [m for m in messages if m["is_job_offer"] or m["job_urls"]]
            all_job_urls = []
            for m in messages:
                all_job_urls.extend(m["job_urls"])
            all_job_urls = list(dict.fromkeys(all_job_urls))

            if job_messages or all_job_urls:
                results.append({
                    "sender": conv["sender"],
                    "snippet": conv["snippet"],
                    "timestamp": conv["timestamp"],
                    "conversation_url": conv["url"],
                    "job_urls": all_job_urls,
                    "messages": job_messages,
                })

            await random_delay(2.0, 5.0)  # Anti-detection between conversations

    return results
