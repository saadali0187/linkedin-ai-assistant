"""Finds freelance/remote frontend-dev leads matching your skills (via free,
public job boards) and emails a digest with a ready-to-send outreach message
draft for each one.

This does NOT message anyone automatically -- there is no LinkedIn API (or
any legitimate API) that lets an app search strangers' profiles and send
them unsolicited messages, and doing that via scraping/bots would violate
LinkedIn's terms and risk an account ban. Instead this finds leads and drafts
the message for you; you review and send it yourself.

Sources (both free, no API key required):
    - RemoteOK              https://remoteok.com/api
    - We Work Remotely      (Programming RSS feed)

Required environment variables:
    GMAIL_ADDRESS      - sender + recipient Gmail address
    GMAIL_APP_PASSWORD - Gmail App Password (not your normal password)

Optional:
    LEAD_KEYWORDS  - comma-separated, default:
                     "frontend,javascript,html,css,react,c#,.net,asp.net,sql server,mssql"
    ALERT_TO       - recipient email, defaults to GMAIL_ADDRESS
"""

import os
import re
import smtplib
import sys
import xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from html import unescape

import requests

REMOTEOK_URL = "https://remoteok.com/api"
WWR_RSS_URL = "https://weworkremotely.com/categories/remote-programming-jobs.rss"

SKILLS_BLURB = "JavaScript/HTML/CSS, C#/.NET, and SQL Server"

MESSAGE_TEMPLATES = [
    "Hi, I came across the {title} opening at {company} and wanted to reach out "
    "directly. I'm a developer with experience in " + SKILLS_BLURB + " and this "
    "looks like a great fit for my skills. Happy to share examples of my work "
    "if you're still looking -- would love to chat.",
    "Hello, I noticed {company} is looking for help with {title}. I work with "
    + SKILLS_BLURB + " and would love to help out. Let me know if you'd like "
    "to see my portfolio or discuss the role.",
    "Hi there -- saw the {title} listing from {company} and it lines up well "
    "with what I do (" + SKILLS_BLURB + "). If the role's still open, I'd love "
    "to connect and share some recent work.",
]


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
    # unrelated roles mention e.g. "React" once in a broad tech-stack list.
    # Trust a title match on its own; otherwise require 2+ distinct keyword
    # hits in the description.
    if any(p.search(title) for p in patterns):
        return True
    return sum(1 for p in patterns if p.search(description)) >= 2


def fetch_remoteok(keywords: list[str]) -> list[dict]:
    patterns = _compile_keyword_patterns(keywords)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; lead-finder/1.0)"}
    response = requests.get(REMOTEOK_URL, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()

    leads = []
    for item in data:
        if not isinstance(item, dict) or "position" not in item:
            continue  # first element is a metadata blob, not a listing
        title = item.get("position", "")
        description = _strip_html(item.get("description", ""))
        # `tags` is unreliable on RemoteOK -- many unrelated listings share
        # the same generic tag list, so match on title/description only.
        if not _relevant(title, description, patterns):
            continue
        leads.append(
            {
                "title": title,
                "company": item.get("company", "Unknown"),
                "link": item.get("url", ""),
            }
        )
    return leads


def fetch_weworkremotely(keywords: list[str]) -> list[dict]:
    patterns = _compile_keyword_patterns(keywords)
    response = requests.get(WWR_RSS_URL, timeout=30)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    leads = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = _strip_html(item.findtext("description") or "")
        if not _relevant(title, description, patterns):
            continue
        # WWR titles are formatted "Company: Job Title"
        company, sep, job_title = title.partition(":")
        leads.append(
            {
                "title": job_title.strip() if sep else title,
                "company": company.strip() if sep else "Unknown",
                "link": link,
            }
        )
    return leads


def dedupe_leads(leads: list[dict]) -> list[dict]:
    seen_links = set()
    unique = []
    for lead in leads:
        link = lead.get("link")
        if not link or link in seen_links:
            continue
        seen_links.add(link)
        unique.append(lead)
    return unique


def draft_message(lead: dict, index: int) -> str:
    template = MESSAGE_TEMPLATES[index % len(MESSAGE_TEMPLATES)]
    return template.format(
        title=lead.get("title") or "this role",
        company=lead.get("company") or "your team",
    )


def build_email_body(leads: list[dict]) -> str:
    if not leads:
        return "No new matching client leads found today."

    lines = [f"Found {len(leads)} potential lead(s) matching your skills:\n"]
    for i, lead in enumerate(leads[:25]):
        lines.append(f"- {lead['title']} @ {lead['company']}\n  {lead['link']}")
        lines.append(f'  Suggested message:\n  "{draft_message(lead, i)}"\n')
    lines.append(
        "\nThese are drafts for YOU to send manually (via the listing's apply "
        "link, or the client's own contact/LinkedIn page). Nothing here is "
        "sent automatically."
    )
    return "\n".join(lines)


def send_email(gmail_address: str, app_password: str, to_address: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = "Your daily client leads"
    msg["From"] = gmail_address
    msg["To"] = to_address

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.sendmail(gmail_address, [to_address], msg.as_string())


def main() -> None:
    gmail_address = os.environ["GMAIL_ADDRESS"]
    app_password = os.environ["GMAIL_APP_PASSWORD"]
    to_address = os.environ.get("ALERT_TO", gmail_address)
    keywords = [
        k.strip().lower()
        for k in os.environ.get(
            "LEAD_KEYWORDS",
            "frontend,javascript,html,css,react,c#,.net,asp.net,sql server,mssql",
        ).split(",")
        if k.strip()
    ]

    leads: list[dict] = []
    try:
        leads.extend(fetch_remoteok(keywords))
    except requests.RequestException as exc:
        print(f"RemoteOK fetch failed: {exc}", file=sys.stderr)
    try:
        leads.extend(fetch_weworkremotely(keywords))
    except requests.RequestException as exc:
        print(f"We Work Remotely fetch failed: {exc}", file=sys.stderr)

    leads = dedupe_leads(leads)
    body = build_email_body(leads)
    send_email(gmail_address, app_password, to_address, body)
    print(f"Sent client leads email with {len(leads)} lead(s).")


if __name__ == "__main__":
    main()
