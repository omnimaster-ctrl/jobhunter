"""Autopilot scheduler — manages cron-based job scheduling for JobHunter."""

import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import yaml

from config.loader import Config

SCHEDULES: dict[str, str] = {
    "daily": "0 9 * * *",
    "2days": "0 9 */2 * *",
    "weekly": "0 9 * * 1",
}

CRON_COMMAND: str = (
    'claude --channels plugin:telegram@claude-plugins-official'
    ' --prompt "Run autopilot: search for jobs using saved criteria'
    ' and notify me of new matches"'
)

CRON_TAG: str = "# jobhunter-autopilot"


class AutopilotScheduler:
    """Manage the autopilot cron job and its configuration."""

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_current_schedule(self) -> str:
        """Return the name of the active schedule, or ``"off"``."""
        crontab = self._read_crontab()
        for line in crontab.splitlines():
            if CRON_TAG in line:
                cron_expr = line.split(CRON_TAG)[0].strip()
                # Extract just the cron timing (first 5 fields)
                parts = cron_expr.split()
                if len(parts) >= 5:
                    timing = " ".join(parts[:5])
                    for name, expr in SCHEDULES.items():
                        if timing == expr:
                            return name
        return "off"

    def set_schedule(self, schedule: str) -> dict:
        """Set or remove the autopilot cron entry.

        Returns a status dict with schedule info.
        """
        crontab = self._read_crontab()
        # Remove existing entry
        lines = [
            line
            for line in crontab.splitlines()
            if CRON_TAG not in line
        ]

        cron_expression = None
        if schedule != "off" and schedule in SCHEDULES:
            cron_expression = SCHEDULES[schedule]
            entry = f"{cron_expression} {CRON_COMMAND} {CRON_TAG}"
            lines.append(entry)

        new_crontab = "\n".join(lines)
        if new_crontab and not new_crontab.endswith("\n"):
            new_crontab += "\n"
        self._write_crontab(new_crontab)

        # Persist to config.yaml
        self._update_config_schedule(schedule)

        return {
            "schedule": schedule,
            "cron_expression": cron_expression,
            "next_run": self._calculate_next_run(schedule) if schedule != "off" else None,
            "search_criteria": self._config.get("search.default_criteria", {}),
        }

    def get_status(self) -> dict:
        """Return current autopilot status information."""
        schedule = self.get_current_schedule()
        cron_expression = SCHEDULES.get(schedule)
        return {
            "schedule": schedule,
            "cron_expression": cron_expression,
            "next_run": self._calculate_next_run(schedule) if schedule != "off" else None,
            "search_criteria": self._config.get("search.default_criteria", {}),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_crontab(self) -> str:
        """Read the current user crontab."""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                return ""
            return result.stdout
        except FileNotFoundError:
            return ""

    def _write_crontab(self, content: str) -> None:
        """Write *content* as the new user crontab."""
        subprocess.run(
            ["crontab", "-"],
            input=content,
            text=True,
            check=True,
        )

    def _calculate_next_run(self, schedule: str) -> str:
        """Return a human-readable string for the next scheduled run."""
        if schedule not in SCHEDULES:
            return "unknown"

        now = datetime.now()
        today_9am = now.replace(hour=9, minute=0, second=0, microsecond=0)

        if schedule == "daily":
            next_run = today_9am if now < today_9am else today_9am + timedelta(days=1)
        elif schedule == "2days":
            next_run = today_9am if now < today_9am else today_9am + timedelta(days=2)
        elif schedule == "weekly":
            # Next Monday at 9 AM
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0 and now >= today_9am:
                days_until_monday = 7
            next_run = today_9am + timedelta(days=days_until_monday)
        else:
            return "unknown"

        return next_run.strftime("%A, %B %d at %I:%M %p")

    def _update_config_schedule(self, schedule: str) -> None:
        """Persist the schedule value to the user config file."""
        config_path = Path(self._config._user_config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        if config_path.exists():
            with open(config_path, "r") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        data.setdefault("autopilot", {})["schedule"] = schedule

        with open(config_path, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
