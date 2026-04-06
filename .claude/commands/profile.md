# /profile — View or update candidate profile

Show or modify the candidate profile used for job matching and resume tailoring.

## Usage
- `/profile` — Show current profile
- `/profile update` — Interactive update

## Telegram Channel Integration

**CRITICAL:** Your text output does NOT reach Telegram. Use the `reply` MCP tool for all responses.

## Process

### View
Read `config/profile.yaml` and send via `reply` tool:
```
reply(chat_id: "...", text: "👤 Candidate Profile\n\nName: Uriel David Tello Padilla\nTitle: Senior Data Engineer | Cloud Solutions Architect\nLocation: Morelia, Michoacán, Mexico\nExperience: 9+ years\n\nTop Skills: Azure Databricks, Fabric, AWS, Python, PySpark, SQL, Terraform, Docker, K8s, Airflow, dbt\nLanguages: English (90%), Spanish (Native)\nEducation: M.Sc. Physics & Math (IPN), B.Sc. (UMSNH)\n\nTarget: Remote contractor roles, US companies, LATAM-based")
```

### Update
Ask user what to change via `reply`, update `config/profile.yaml`, confirm changes via `reply`.
