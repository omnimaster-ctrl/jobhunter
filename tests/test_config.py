import os
import pytest
import yaml
from config.loader import Config


@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / ".jobhunter"


@pytest.fixture
def user_config(config_dir):
    config_dir.mkdir(parents=True)
    config_path = config_dir / "config.yaml"
    config_path.write_text(yaml.dump({
        "autopilot": {"schedule": "daily"},
        "search": {"default_criteria": {"role": "ML Engineer"}},
    }))
    return config_path


class TestConfigDefaults:
    def test_loads_default_config(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("autopilot.schedule") == "off"
        assert config.get("rate_limits.applications_per_hour") == 3

    def test_default_search_criteria(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        criteria = config.get("search.default_criteria")
        assert criteria["role"] == "Senior Data Engineer"
        assert criteria["remote"] is True


class TestConfigUserOverrides:
    def test_user_config_overrides_defaults(self, user_config):
        config = Config(user_config_path=str(user_config))
        assert config.get("autopilot.schedule") == "daily"

    def test_user_config_deep_merge(self, user_config):
        config = Config(user_config_path=str(user_config))
        assert config.get("search.default_criteria.role") == "ML Engineer"
        assert config.get("search.default_criteria.remote") is True

    def test_non_overridden_values_remain(self, user_config):
        config = Config(user_config_path=str(user_config))
        assert config.get("rate_limits.applications_per_hour") == 3


class TestConfigCreation:
    def test_creates_default_user_config_if_missing(self, config_dir):
        config_path = config_dir / "config.yaml"
        config = Config(user_config_path=str(config_path))
        config.ensure_user_config()
        assert config_path.exists()

    def test_get_nested_value_with_dot_notation(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("dashboard.host") == "127.0.0.1"
        assert config.get("dashboard.port") == 3000

    def test_get_returns_none_for_missing_key(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("nonexistent.key") is None

    def test_get_returns_default_for_missing_key(self):
        config = Config(user_config_path="/nonexistent/path.yaml")
        assert config.get("nonexistent.key", "fallback") == "fallback"
