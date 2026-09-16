"""Fetches jobs matching your skills (via the Jooble API) and emails a daily
digest through Gmail SMTP. No LinkedIn scraping/auto-apply involved.

Required environment variables:
    JOOBLE_API_KEY     - free key from https://jooble.org/api/about
    GMAIL_ADDRESS      - sender + recipient Gmail address
    GMAIL_APP_PASSWORD - Gmail App Password (not your normal password)

Optional:
    JOB_KEYWORDS   - default: "Frontend Developer JavaScript HTML CSS C# .NET MS SQL"
    JOB_LOCATIONS  - comma-separated, default: "Pakistan,Remote"
    ALERT_TO       - recipient email, defaults to GMAIL_ADDRESS
"""

import os
import smtplib
import sys
from email.mime.text import MIMEText

import requests

JOOBLE_URL_TEMPLATE = "https://jooble.org/api/{key}"


def fetch_jobs(api_key: str, keywords: str, location: str) -> list[dict]:
    url = JOOBLE_URL_TEMPLATE.format(key=api_key)
    response = requests.post(
        url,
        json={"keywords": keywords, "location": location},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get("jobs", [])


def dedupe_jobs(jobs: list[dict]) -> list[dict]:
    seen_links = set()
    unique = []
    for job in jobs:
        link = job.get("link")
        if link in seen_links:
            continue
        seen_links.add(link)
        unique.append(job)
    return unique


def build_email_body(jobs: list[dict]) -> str:
    if not jobs:
        return "No new matching jobs found today."

    lines = [f"Found {len(jobs)} job(s) matching your skills:\n"]
    for job in jobs[:40]:
        title = job.get("title", "Untitled")
        company = job.get("company", "Unknown company")
        location = job.get("location", "")
        link = job.get("link", "")
        lines.append(f"- {title} @ {company} ({location})\n  {link}\n")
    return "\n".join(lines)


def send_email(gmail_address: str, app_password: str, to_address: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = "Your daily job matches"
    msg["From"] = gmail_address
    msg["To"] = to_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, [to_address], msg.as_string())


def main() -> None:
    api_key = os.environ["JOOBLE_API_KEY"]
    gmail_address = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_address = os.environ.get("ALERT_TO", gmail_address)

    keywords = os.environ.get(
        "JOB_KEYWORDS", "Frontend Developer JavaScript HTML CSS C# .NET MS SQL"
    )
    locations = os.environ.get("JOB_LOCATIONS", "Pakistan,Remote").split(",")

    all_jobs: list[dict] = []
    for location in locations:
        location = location.strip()
        if location.lower() == "remote":
            # "Remote" isn't a real place Jooble understands as a location -
            # leave location blank to search worldwide (Pakistan included)
            # and push "remote" into the keywords so results are filtered
            # to remote roles instead.
            search_location = ""
            search_keywords = f"{keywords} remote"
        else:
            search_location = location
            search_keywords = keywords
        try:
            all_jobs.extend(fetch_jobs(api_key, search_keywords, search_location))
        except requests.RequestException as exc:
            print(f"Job fetch failed for location '{location}': {exc}", file=sys.stderr)

    jobs = dedupe_jobs(all_jobs)
    body = build_email_body(jobs)
    send_email(gmail_address, app_password, to_address, body)
    print(f"Sent job alert email with {len(jobs)} job(s).")


if __name__ == "__main__":
    main()
