"""Fetches jobs matching your skills (via the Jooble API and, optionally, the
JSearch API which aggregates LinkedIn/Indeed/Glassdoor/etc.) and emails a
daily digest through Gmail SMTP. No LinkedIn scraping/auto-apply involved --
this only finds and lists matching jobs; you review and apply yourself.

Searches two independent categories and lists each in its own section of the
digest: your primary skill set, and camera/CCTV monitoring roles (both in
Pakistan and worldwide remote).

Required environment variables:
    JOOBLE_API_KEY     - free key from https://jooble.org/api/about
    GMAIL_ADDRESS      - sender + recipient Gmail address
    GMAIL_APP_PASSWORD - Gmail App Password (not your normal password)

Optional:
    JOB_KEYWORDS          - default: "Frontend Developer JavaScript HTML CSS C# .NET MS SQL"
    JOB_LOCATIONS         - comma-separated, default: "Pakistan"
    CAMERA_JOB_KEYWORDS   - default: "CCTV Monitoring Camera Operator Remote Surveillance Security Monitoring"
    CAMERA_JOB_LOCATIONS  - comma-separated, default: "Pakistan,Remote"
    ALERT_TO       - recipient email, defaults to GMAIL_ADDRESS
    RAPIDAPI_KEY   - free key from https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
                     enables the JSearch source, which also surfaces LinkedIn
                     job postings alongside Indeed/Glassdoor/etc.
"""

import os
import smtplib
import sys
from email.mime.text import MIMEText

import requests

JOOBLE_URL_TEMPLATE = "https://jooble.org/api/{key}"
JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
JSEARCH_HOST = "jsearch.p.rapidapi.com"


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


def fetch_jobs_jsearch(api_key: str, keywords: str, location: str) -> list[dict]:
    query = f"{keywords} in {location}" if location else keywords
    response = requests.get(
        JSEARCH_URL,
        headers={"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": JSEARCH_HOST},
        params={"query": query, "page": "1", "num_pages": "1"},
        timeout=30,
    )
    response.raise_for_status()
    jobs = []
    for item in response.json().get("data", []):
        jobs.append(
            {
                "title": item.get("job_title", "Untitled"),
                "company": item.get("employer_name", "Unknown company"),
                "location": ", ".join(
                    part for part in (item.get("job_city"), item.get("job_country")) if part
                ),
                "link": item.get("job_apply_link") or item.get("job_google_link", ""),
            }
        )
    return jobs


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


def fetch_category(
    category: str,
    jooble_key: str,
    rapidapi_key: str,
    keywords: str,
    locations: list[str],
) -> list[dict]:
    """Searches one job category (e.g. primary skills, camera monitoring)
    across all configured locations and tags each result with its category
    so the digest email can group them into sections."""
    jobs: list[dict] = []
    for location in locations:
        location = location.strip()
        if location.lower() == "remote":
            # "Remote" isn't a real place Jooble understands as a location -
            # leave location blank to search worldwide and push "remote"
            # into the keywords so results are filtered to remote roles.
            search_location = ""
            search_keywords = f"{keywords} remote"
        else:
            search_location = location
            search_keywords = keywords
        try:
            jobs.extend(fetch_jobs(jooble_key, search_keywords, search_location))
        except requests.RequestException as exc:
            print(f"Jooble fetch failed for '{category}' in '{location}': {exc}", file=sys.stderr)

        if rapidapi_key:
            try:
                jobs.extend(fetch_jobs_jsearch(rapidapi_key, search_keywords, search_location))
            except requests.RequestException as exc:
                print(f"JSearch fetch failed for '{category}' in '{location}': {exc}", file=sys.stderr)

    for job in jobs:
        job["category"] = category
    return dedupe_jobs(jobs)


def build_email_body(categorized_jobs: list[tuple[str, list[dict]]]) -> str:
    total = sum(len(jobs) for _, jobs in categorized_jobs)
    if total == 0:
        return "No new matching jobs found today."

    sections = [f"Found {total} job(s) matching your searches today:\n"]
    for category, jobs in categorized_jobs:
        if not jobs:
            continue
        sections.append(f"=== {category} ({len(jobs)}) ===")
        for job in jobs[:40]:
            title = job.get("title", "Untitled")
            company = job.get("company", "Unknown company")
            location = job.get("location", "")
            link = job.get("link", "")
            sections.append(f"- {title} @ {company} ({location})\n  {link}\n")
    return "\n".join(sections)


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
    rapidapi_key = os.environ.get("RAPIDAPI_KEY", "")

    keywords = os.environ.get(
        "JOB_KEYWORDS", "Frontend Developer JavaScript HTML CSS C# .NET MS SQL"
    )
    locations = os.environ.get("JOB_LOCATIONS", "Pakistan").split(",")

    camera_keywords = os.environ.get(
        "CAMERA_JOB_KEYWORDS",
        "CCTV Monitoring Camera Operator Remote Surveillance Security Monitoring",
    )
    camera_locations = os.environ.get("CAMERA_JOB_LOCATIONS", "Pakistan,Remote").split(",")

    categorized_jobs = [
        ("Frontend Developer", fetch_category("Frontend Developer", api_key, rapidapi_key, keywords, locations)),
        (
            "Camera / CCTV Monitoring",
            fetch_category("Camera / CCTV Monitoring", api_key, rapidapi_key, camera_keywords, camera_locations),
        ),
    ]

    body = build_email_body(categorized_jobs)
    send_email(gmail_address, app_password, to_address, body)
    total = sum(len(jobs) for _, jobs in categorized_jobs)
    print(f"Sent job alert email with {total} job(s).")


if __name__ == "__main__":
    main()
