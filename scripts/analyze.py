import os
import requests
import pandas as pd
from datetime import datetime

USERNAME = os.getenv("USERNAME")

if not USERNAME:
    raise SystemExit("USERNAME environment variable not set")

headers = {}

repos = []
page = 1
per_page = 100
while True:
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page={per_page}&page={page}"
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    batch = r.json()
    if not batch:
        break
    repos.extend(batch)
    page += 1

data = []
now = datetime.utcnow()

for repo in repos:
    name = repo["name"]
    pushed_at = repo.get("pushed_at")
    if pushed_at:
        last_push_date = datetime.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
        days_old = (now - last_push_date).days
        last_updated = last_push_date.strftime("%Y-%m-%d")
    else:
        days_old = None
        last_updated = "Never"

    if days_old is None:
        status = "UNKNOWN"
    elif days_old < 30:
        status = "ACTIVE (<30d)"
    elif days_old < 90:
        status = "STALE (30-90d)"
    else:
        status = "OUTDATED (>90d)"

    data.append({
        "Repository": name,
        "Last Updated": last_updated,
        "Days Since Update": days_old if days_old else "",
        "Status": status,
        "URL": repo.get("html_url")
    })

df = pd.DataFrame(data).sort_values(by="Days Since Update", na_position="first")

df.to_csv("report.csv", index=False)

with open("report.md", "w", encoding="utf-8") as f:
    f.write("# Repository Activity Report\n")
    f.write(f"Generated on: {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n")
    f.write(df.to_markdown(index=False))
