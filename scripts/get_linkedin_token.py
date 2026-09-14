"""ONE-TIME local helper: runs the LinkedIn OAuth 2.0 flow and prints the
LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN values to save as GitHub secrets.

Run this on your own machine (not in GitHub Actions) after creating a
LinkedIn app with the "Sign In with LinkedIn using OpenID Connect" and
"Share on LinkedIn" products added. Redirect URL must be:
    http://localhost:8080/callback

Usage:
    set LINKEDIN_CLIENT_ID=xxxx        (PowerShell: $env:LINKEDIN_CLIENT_ID="xxxx")
    set LINKEDIN_CLIENT_SECRET=xxxx
    python get_linkedin_token.py
"""

import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

REDIRECT_URI = "http://localhost:8080/callback"
SCOPE = "openid profile w_member_social"

auth_code = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        auth_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"<html><body>Done, you can close this tab.</body></html>")

    def log_message(self, *args):
        pass  # keep the console quiet


def main() -> None:
    client_id = os.environ.get("LINKEDIN_CLIENT_ID")
    client_secret = os.environ.get("LINKEDIN_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("Set LINKEDIN_CLIENT_ID and LINKEDIN_CLIENT_SECRET first.", file=sys.stderr)
        sys.exit(1)

    auth_url = (
        "https://www.linkedin.com/oauth/v2/authorization?"
        + urllib.parse.urlencode(
            {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": REDIRECT_URI,
                "scope": SCOPE,
            }
        )
    )

    print("Opening browser for LinkedIn login/consent...")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", 8080), CallbackHandler)
    server.handle_request()  # blocks until the redirect hits us, once

    if not auth_code:
        print("Did not receive an authorization code.", file=sys.stderr)
        sys.exit(1)

    token_response = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    token_response.raise_for_status()
    access_token = token_response.json()["access_token"]

    userinfo_response = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=30,
    )
    userinfo_response.raise_for_status()
    person_id = userinfo_response.json()["sub"]

    print("\n--- Save these as GitHub repo secrets ---")
    print(f"LINKEDIN_ACCESS_TOKEN={access_token}")
    print(f"LINKEDIN_PERSON_URN=urn:li:person:{person_id}")
    print("\nNote: this token expires in ~60 days. Re-run this script to refresh it.")


if __name__ == "__main__":
    main()
