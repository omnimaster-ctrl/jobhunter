# /profile — View or update candidate profile

Show or modify the candidate profile used for job matching and resume tailoring.

## Usage
- `/profile` — Show current profile
- `/profile update` — Interactive update

## Process

### View
Read `config/profile.yaml` and display:
```
👤 Candidate Profile

Name: Uriel David Tello Padilla
Title: Senior Data Engineer | Cloud Solutions Architect
Location: Morelia, Michoacán, Mexico
Experience: 9+ years

Top Skills: Azure Databricks, Fabric, AWS, Python, PySpark, SQL, Terraform, Docker, K8s, Airflow, dbt
Languages: English (90%), Spanish (Native)
Education: M.Sc. Physics & Math (IPN), B.Sc. Physics & Math (UMSNH)

Target: Remote contractor roles, US companies, LATAM-based
```

### Update
Ask user what to change, update `config/profile.yaml`, confirm changes.
