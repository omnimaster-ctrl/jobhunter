import pytest
from linkedin.linkedin_search import build_search_url, parse_job_card

class TestBuildSearchUrl:
    def test_basic_search_url(self):
        url = build_search_url(keywords="Data Engineer")
        assert "linkedin.com/jobs/search" in url
        assert "keywords=Data" in url

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
            remote=True, easy_apply=True,
            experience_level="mid-senior", job_type="contract",
            posted_within="week", sort_by="recent",
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
        assert job["easy_apply"] is True

    def test_parse_job_card_normalizes_url(self):
        raw = {
            "title": "Engineer", "company": "Co",
            "url": "https://www.linkedin.com/jobs/view/123456?refId=abc&trk=xyz",
        }
        job = parse_job_card(raw)
        assert job["url"] == "https://www.linkedin.com/jobs/view/123456"
