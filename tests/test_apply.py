import pytest
from linkedin.linkedin_apply import (
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
