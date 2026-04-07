"""Tests for LinkedIn message reader utilities."""

from linkedin.linkedin_messages import (
    extract_job_urls,
    looks_like_job_offer,
    parse_conversation_preview,
    LINKEDIN_JOB_URL_RE,
    LINKEDIN_SHORT_URL_RE,
)


class TestExtractJobUrls:
    def test_extracts_standard_job_url(self):
        text = "Check this out https://www.linkedin.com/jobs/view/12345678 what do you think?"
        urls = extract_job_urls(text)
        assert len(urls) == 1
        assert "linkedin.com/jobs/view/12345678" in urls[0]

    def test_extracts_collections_url(self):
        text = "https://www.linkedin.com/jobs/collections/recommended/12345"
        urls = extract_job_urls(text)
        assert len(urls) == 1

    def test_extracts_comm_url(self):
        text = "Link: https://linkedin.com/comm/jobs/view/98765"
        urls = extract_job_urls(text)
        assert len(urls) == 1

    def test_extracts_shortened_url(self):
        text = "Great role: https://lnkd.in/abc123"
        urls = extract_job_urls(text)
        assert len(urls) == 1
        assert "lnkd.in/abc123" in urls[0]

    def test_extracts_multiple_urls(self):
        text = (
            "Two roles: https://www.linkedin.com/jobs/view/111 "
            "and https://www.linkedin.com/jobs/view/222"
        )
        urls = extract_job_urls(text)
        assert len(urls) == 2

    def test_deduplicates_urls(self):
        text = (
            "https://www.linkedin.com/jobs/view/111 "
            "again https://www.linkedin.com/jobs/view/111"
        )
        urls = extract_job_urls(text)
        assert len(urls) == 1

    def test_strips_query_params(self):
        text = "https://www.linkedin.com/jobs/view/111?refId=abc&trackingId=xyz"
        urls = extract_job_urls(text)
        assert len(urls) == 1
        assert "?" not in urls[0]

    def test_returns_empty_for_no_urls(self):
        text = "Hey, how are you doing? Let's catch up sometime."
        urls = extract_job_urls(text)
        assert urls == []

    def test_ignores_non_job_linkedin_urls(self):
        text = "Check my profile https://www.linkedin.com/in/someone"
        urls = extract_job_urls(text)
        assert urls == []


class TestLooksLikeJobOffer:
    def test_recognizes_job_offer_keywords(self):
        text = "Hi, I have a great remote data engineer opportunity for you"
        assert looks_like_job_offer(text) is True

    def test_recognizes_recruiter_message(self):
        text = "We are hiring for a senior engineer position at our company"
        assert looks_like_job_offer(text) is True

    def test_rejects_casual_message(self):
        text = "Hey, how are you? Want to grab coffee?"
        assert looks_like_job_offer(text) is False

    def test_rejects_single_keyword(self):
        # Only one keyword match — threshold is 2
        text = "I have an opportunity for lunch"
        assert looks_like_job_offer(text) is False

    def test_case_insensitive(self):
        text = "HIRING for a REMOTE ENGINEER ROLE"
        assert looks_like_job_offer(text) is True

    def test_contractor_freelance(self):
        text = "Looking for a freelance contractor for a remote role"
        assert looks_like_job_offer(text) is True


class TestParseConversationPreview:
    def test_parses_full_dict(self):
        raw = {
            "sender": "  John Doe  ",
            "snippet": "  I have a role for you  ",
            "timestamp": "2h ago",
            "url": "/messaging/thread/123",
            "unread": True,
        }
        result = parse_conversation_preview(raw)
        assert result["sender"] == "John Doe"
        assert result["snippet"] == "I have a role for you"
        assert result["timestamp"] == "2h ago"
        assert result["url"] == "/messaging/thread/123"
        assert result["unread"] is True

    def test_handles_missing_keys(self):
        raw = {}
        result = parse_conversation_preview(raw)
        assert result["sender"] == ""
        assert result["snippet"] == ""
        assert result["timestamp"] == ""
        assert result["url"] == ""
        assert result["unread"] is False

    def test_handles_partial_dict(self):
        raw = {"sender": "Jane", "unread": False}
        result = parse_conversation_preview(raw)
        assert result["sender"] == "Jane"
        assert result["unread"] is False


class TestRegexPatterns:
    def test_job_url_regex_matches_view(self):
        assert LINKEDIN_JOB_URL_RE.search("https://www.linkedin.com/jobs/view/12345678")

    def test_job_url_regex_matches_collections(self):
        assert LINKEDIN_JOB_URL_RE.search("https://linkedin.com/jobs/collections/recommended/123")

    def test_job_url_regex_matches_comm(self):
        assert LINKEDIN_JOB_URL_RE.search("https://linkedin.com/comm/jobs/view/456")

    def test_short_url_regex_matches(self):
        assert LINKEDIN_SHORT_URL_RE.search("https://lnkd.in/abcXYZ")

    def test_job_url_regex_no_match_profile(self):
        assert LINKEDIN_JOB_URL_RE.search("https://linkedin.com/in/someone") is None
