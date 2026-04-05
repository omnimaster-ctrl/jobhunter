"""Initialize the ~/.jobhunter data directory and database."""
import os
import stat
from pathlib import Path

from config.loader import Config
from db.database import Database


def setup():
    home = Path.home() / ".jobhunter"

    # Create directories with restrictive permissions
    dirs = [
        home,
        home / "browser-profile",
        home / "resumes",
        home / "db",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        os.chmod(d, stat.S_IRWXU)  # 700

    # Initialize config
    config = Config()
    config.ensure_user_config()

    # Initialize database
    db_path = str(home / "db" / "jobhunter.db")
    db = Database(db_path)
    db.init()
    db.close()
    os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)  # 600

    print("JobHunter environment initialized:")
    print(f"  Config:   {home / 'config.yaml'}")
    print(f"  Database: {db_path}")
    print(f"  Browser:  {home / 'browser-profile'}")
    print(f"  Resumes:  {home / 'resumes'}")


if __name__ == "__main__":
    setup()
