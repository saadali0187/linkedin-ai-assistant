"""Fetches jobs matching your skills from several sources and emails a daily
digest through Gmail SMTP. No LinkedIn scraping/auto-apply involved -- this
only finds and lists matching jobs; you review and apply yourself.

Sources:
    - Jooble              always on, free key required
    - JSearch (RapidAPI)   optional -- also surfaces LinkedIn/Indeed/Glassdoor,
                           but needs a RAPIDAPI_KEY (free signup required,
                           there is no key-less way to pull LinkedIn/Indeed
                           listings short of scraping, which this project
                           deliberately does not do)
    - RemoteOK             always on, free public API, no key needed
    - We Work Remotely     always on, free public RSS feed, no key needed

Searches two independent categories and lists each in its own section of the
digest: your primary skill set, and camera/CCTV monitoring roles (both in
Pakistan and worldwide remote).

Required environment variables:
    JOOBLE_API_KEY     - free key from https://jooble.org/api/about
    GMAIL_ADDRESS      - sender + recipient Gmail address
    GMAIL_APP_PASSWORD - Gmail App Password (not your normal password)

Optional:
    JOB_KEYWORDS            - default: "Frontend Developer JavaScript HTML CSS C# .NET MS SQL"
    JOB_LOCATIONS           - comma-separated, default: "Pakistan"
    FRONTEND_MATCH_KEYWORDS - comma-separated, used to filter RemoteOK/WWR
                              listings, default:
                              "frontend,javascript,html,css,react,c#,.net,asp.net,sql server,mssql"
    CAMERA_JOB_KEYWORDS     - default: "CCTV Monitoring Camera Operator Remote Surveillance Security Monitoring"
    CAMERA_JOB_LOCATIONS    - comma-separated, default: "Pakistan,Remote"
    CAMERA_MATCH_KEYWORDS   - comma-separated, used to filter RemoteOK/WWR
                              listings, default:
                              "cctv,surveillance camera,security camera,camera operator,video surveillance,camera monitoring"
    ALERT_TO       - recipient email, defaults to GMAIL_ADDRESS
    RAPIDAPI_KEY   - free key from https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
                     enables the JSearch source, which also surfaces LinkedIn
                     job postings alongside Indeed/Glassdoor/etc.
"""

import os
import re
import smtplib
import sys
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from html import unescape

import requests

JOOBLE_URL_TEMPLATE = "https://jooble.org/api/{key}"
JSEARCH_URL = "https://jsearch.p.rapidapi.com/search"
JSEARCH_HOST = "jsearch.p.rapidapi.com"
REMOTEOK_URL = "https://remoteok.com/api"
WWR_RSS_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"


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


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return unescape(re.sub(r"\s+", " ", text)).strip()


def _compile_keyword_patterns(keywords: list[str]) -> list[re.Pattern]:
    # Match whole keywords only (not substrings) so e.g. "react" doesn't hit
    # "interact"/"proactive" and ".net" doesn't hit stray domain names.
    return [
        re.compile(r"(?<![a-z0-9])" + re.escape(k) + r"(?![a-z0-9])", re.IGNORECASE)
        for k in keywords
    ]


def _relevant(title: str, description: str, patterns: list[re.Pattern]) -> bool:
    # A single keyword hit inside a long description is weak evidence -- many
    # unrelated roles mention a keyword once in passing. Trust a title match
    # on its own; otherwise require 2+ distinct keyword hits in the body.
    if any(p.search(title) for p in patterns):
        return True
    return sum(1 for p in patterns if p.search(description)) >= 2


def fetch_remoteok(match_keywords: list[str]) -> list[dict]:
    patterns = _compile_keyword_patterns(match_keywords)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; job-alert/1.0)"}
    response = requests.get(REMOTEOK_URL, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    jobs = []
    for item in data:
        if not isinstance(item, dict) or "position" not in item:
            continue  # first element is a metadata blob, not a listing
        title = item.get("position", "")
        description = _strip_html(item.get("description", ""))
        if not _relevant(title, description, patterns):
            continue
        jobs.append(
            {
                "title": title,
                "company": item.get("company", "Unknown company"),
                "location": "Remote",
                "link": item.get("url", ""),
            }
        )
    return jobs


def fetch_weworkremotely(match_keywords: list[str]) -> list[dict]:
    patterns = _compile_keyword_patterns(match_keywords)
    response = requests.get(WWR_RSS_URL, timeout=30)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    jobs = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = _strip_html(item.findtext("description") or "")
        if not _relevant(title, description, patterns):
            continue
        # WWR titles are formatted "Company: Job Title"
        company, sep, job_title = title.partition(":")
        jobs.append(
            {
                "title": job_title.strip() if sep else title,
                "company": company.strip() if sep else "Unknown company",
                "location": "Remote",
                "link": link,
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
    match_keywords: list[str],
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

    # RemoteOK and WWR are global remote-job boards, not location-scoped --
    # fetch each once per category instead of once per location.
    try:
        jobs.extend(fetch_remoteok(match_keywords))
    except requests.RequestException as exc:
        print(f"RemoteOK fetch failed for '{category}': {exc}", file=sys.stderr)
    try:
        jobs.extend(fetch_weworkremotely(match_keywords))
    except requests.RequestException as exc:
        print(f"We Work Remotely fetch failed for '{category}': {exc}", file=sys.stderr)

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
    frontend_match_keywords = [
        k.strip().lower()
        for k in os.environ.get(
            "FRONTEND_MATCH_KEYWORDS",
            "frontend,javascript,html,css,react,c#,.net,asp.net,sql server,mssql",
        ).split(",")
        if k.strip()
    ]

    camera_keywords = os.environ.get(
        "CAMERA_JOB_KEYWORDS",
        "CCTV Monitoring Camera Operator Remote Surveillance Security Monitoring",
    )
    camera_locations = os.environ.get("CAMERA_JOB_LOCATIONS", "Pakistan,Remote").split(",")
    camera_match_keywords = [
        k.strip().lower()
        for k in os.environ.get(
            "CAMERA_MATCH_KEYWORDS",
            "cctv,surveillance camera,security camera,camera operator,video surveillance,camera monitoring",
        ).split(",")
        if k.strip()
    ]

    categorized_jobs = [
        (
            "Frontend Developer",
            fetch_category("Frontend Developer", api_key, rapidapi_key, keywords, locations, frontend_match_keywords),
        ),
        (
            "Camera / CCTV Monitoring",
            fetch_category(
                "Camera / CCTV Monitoring",
                api_key,
                rapidapi_key,
                camera_keywords,
                camera_locations,
                camera_match_keywords,
            ),
        ),
    ]

    body = build_email_body(categorized_jobs)
    send_email(gmail_address, app_password, to_address, body)
    total = sum(len(jobs) for _, jobs in categorized_jobs)
    print(f"Sent job alert email with {total} job(s).")


if __name__ == "__main__":
    main()
