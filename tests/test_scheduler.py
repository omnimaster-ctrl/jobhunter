"""Tests for autopilot.scheduler — all subprocess/file I/O is mocked."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from autopilot.scheduler import (
    CRON_COMMAND,
    CRON_TAG,
    SCHEDULES,
    AutopilotScheduler,
)
from config.loader import Config


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def config_dir(tmp_path):
    d = tmp_path / ".jobhunter"
    d.mkdir()
    return d


@pytest.fixture
def user_config(config_dir):
    config_path = config_dir / "config.yaml"
    config_path.write_text(yaml.dump({
        "autopilot": {"schedule": "off"},
        "search": {"default_criteria": {"role": "Data Engineer", "remote": True}},
    }))
    return config_path


@pytest.fixture
def scheduler(user_config):
    cfg = Config(user_config_path=str(user_config))
    return AutopilotScheduler(config=cfg)


# ── Constants ─────────────────────────────────────────────────────────


class TestConstants:
    def test_schedules_contains_expected_keys(self):
        assert set(SCHEDULES) == {"daily", "2days", "weekly"}

    def test_daily_cron_expression(self):
        assert SCHEDULES["daily"] == "0 9 * * *"

    def test_2days_cron_expression(self):
        assert SCHEDULES["2days"] == "0 9 */2 * *"

    def test_weekly_cron_expression(self):
        assert SCHEDULES["weekly"] == "0 9 * * 1"

    def test_cron_command_contains_claude(self):
        assert "claude" in CRON_COMMAND

    def test_cron_command_contains_telegram_channel(self):
        assert "plugin:telegram@claude-plugins-official" in CRON_COMMAND

    def test_cron_tag_value(self):
        assert CRON_TAG == "# jobhunter-autopilot"


# ── _read_crontab / _write_crontab ───────────────────────────────────


class TestCrontabIO:
    @patch("autopilot.scheduler.subprocess.run")
    def test_read_crontab_returns_stdout(self, mock_run, scheduler):
        mock_run.return_value = MagicMock(returncode=0, stdout="existing cron\n")
        assert scheduler._read_crontab() == "existing cron\n"

    @patch("autopilot.scheduler.subprocess.run")
    def test_read_crontab_returns_empty_on_error(self, mock_run, scheduler):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="no crontab")
        assert scheduler._read_crontab() == ""

    @patch("autopilot.scheduler.subprocess.run")
    def test_read_crontab_returns_empty_when_not_found(self, mock_run, scheduler):
        mock_run.side_effect = FileNotFoundError
        assert scheduler._read_crontab() == ""

    @patch("autopilot.scheduler.subprocess.run")
    def test_write_crontab_passes_content_via_stdin(self, mock_run, scheduler):
        mock_run.return_value = MagicMock(returncode=0)
        scheduler._write_crontab("0 9 * * * echo hi\n")
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs["input"] == "0 9 * * * echo hi\n"


# ── get_current_schedule ──────────────────────────────────────────────


class TestGetCurrentSchedule:
    @patch("autopilot.scheduler.subprocess.run")
    def test_returns_off_when_no_crontab(self, mock_run, scheduler):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        assert scheduler.get_current_schedule() == "off"

    @patch("autopilot.scheduler.subprocess.run")
    def test_returns_off_when_no_tagged_entry(self, mock_run, scheduler):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="0 * * * * some-other-job\n",
        )
        assert scheduler.get_current_schedule() == "off"

    @patch("autopilot.scheduler.subprocess.run")
    def test_detects_daily_schedule(self, mock_run, scheduler):
        entry = f"0 9 * * * {CRON_COMMAND} {CRON_TAG}\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=entry)
        assert scheduler.get_current_schedule() == "daily"

    @patch("autopilot.scheduler.subprocess.run")
    def test_detects_weekly_schedule(self, mock_run, scheduler):
        entry = f"0 9 * * 1 {CRON_COMMAND} {CRON_TAG}\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=entry)
        assert scheduler.get_current_schedule() == "weekly"

    @patch("autopilot.scheduler.subprocess.run")
    def test_detects_2days_schedule(self, mock_run, scheduler):
        entry = f"0 9 */2 * * {CRON_COMMAND} {CRON_TAG}\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=entry)
        assert scheduler.get_current_schedule() == "2days"


# ── set_schedule ──────────────────────────────────────────────────────


class TestSetSchedule:
    @patch("autopilot.scheduler.subprocess.run")
    def test_set_daily_returns_correct_dict(self, mock_run, scheduler):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        result = scheduler.set_schedule("daily")
        assert result["schedule"] == "daily"
        assert result["cron_expression"] == "0 9 * * *"
        assert result["next_run"] is not None
        assert "role" in result["search_criteria"]

    @patch("autopilot.scheduler.subprocess.run")
    def test_set_off_removes_entry(self, mock_run, scheduler):
        existing = f"0 9 * * * {CRON_COMMAND} {CRON_TAG}\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=existing)
        result = scheduler.set_schedule("off")
        assert result["schedule"] == "off"
        assert result["cron_expression"] is None
        assert result["next_run"] is None

    @patch("autopilot.scheduler.subprocess.run")
    def test_set_schedule_preserves_other_cron_entries(self, mock_run, scheduler):
        existing = f"0 * * * * other-job\n0 9 * * * {CRON_COMMAND} {CRON_TAG}\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=existing)
        scheduler.set_schedule("weekly")
        # The write call is the second subprocess.run invocation
        write_call = mock_run.call_args_list[-1]
        written = write_call.kwargs.get("input", write_call[1].get("input", ""))
        assert "other-job" in written
        assert CRON_TAG in written

    @patch("autopilot.scheduler.subprocess.run")
    def test_set_schedule_updates_config_yaml(self, mock_run, scheduler, user_config):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        scheduler.set_schedule("weekly")
        with open(user_config) as f:
            data = yaml.safe_load(f)
        assert data["autopilot"]["schedule"] == "weekly"

    @patch("autopilot.scheduler.subprocess.run")
    def test_set_off_updates_config_yaml(self, mock_run, scheduler, user_config):
        mock_run.return_value = MagicMock(returncode=0, stdout="")
        scheduler.set_schedule("off")
        with open(user_config) as f:
            data = yaml.safe_load(f)
        assert data["autopilot"]["schedule"] == "off"


# ── get_status ────────────────────────────────────────────────────────


class TestGetStatus:
    @patch("autopilot.scheduler.subprocess.run")
    def test_status_when_off(self, mock_run, scheduler):
        mock_run.return_value = MagicMock(returncode=1, stdout="")
        status = scheduler.get_status()
        assert status["schedule"] == "off"
        assert status["cron_expression"] is None
        assert status["next_run"] is None

    @patch("autopilot.scheduler.subprocess.run")
    def test_status_when_daily(self, mock_run, scheduler):
        entry = f"0 9 * * * {CRON_COMMAND} {CRON_TAG}\n"
        mock_run.return_value = MagicMock(returncode=0, stdout=entry)
        status = scheduler.get_status()
        assert status["schedule"] == "daily"
        assert status["cron_expression"] == "0 9 * * *"
        assert status["next_run"] is not None
        assert "search_criteria" in status


# ── _calculate_next_run ───────────────────────────────────────────────


class TestCalculateNextRun:
    def test_daily_before_9am(self, scheduler):
        with patch("autopilot.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = datetime(2026, 4, 5, 8, 0)
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = scheduler._calculate_next_run("daily")
            assert "9:00 AM" in result

    def test_daily_after_9am(self, scheduler):
        with patch("autopilot.scheduler.datetime") as mock_dt:
            now = datetime(2026, 4, 5, 10, 0)
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = scheduler._calculate_next_run("daily")
            # Should be next day
            assert "April 06" in result

    def test_unknown_schedule_returns_unknown(self, scheduler):
        assert scheduler._calculate_next_run("nonexistent") == "unknown"

    def test_weekly_returns_monday(self, scheduler):
        with patch("autopilot.scheduler.datetime") as mock_dt:
            # Wednesday April 8 2026 at 10am
            now = datetime(2026, 4, 8, 10, 0)
            mock_dt.now.return_value = now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            result = scheduler._calculate_next_run("weekly")
            assert "Monday" in result
