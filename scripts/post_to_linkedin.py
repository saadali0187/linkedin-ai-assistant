"""Posts the next item from content_pool.POSTS to LinkedIn using the official
LinkedIn API (UGC Posts endpoint, w_member_social scope).

Required environment variables:
    LINKEDIN_ACCESS_TOKEN  - OAuth access token with w_member_social scope
    LINKEDIN_PERSON_URN    - e.g. "urn:li:person:AbCdEfGhIj"

State:
    state/post_index.txt   - index of the next post to publish (rotates)
"""

import os
import sys
import requests

from content_pool import POSTS

STATE_FILE = os.path.join(os.path.dirname(__file__), "..", "state", "post_index.txt")
API_URL = "https://api.linkedin.com/v2/ugcPosts"


def read_index() -> int:
    if not os.path.exists(STATE_FILE):
        return 0
    with open(STATE_FILE, "r") as f:
        content = f.read().strip()
        return int(content) if content else 0


def write_index(index: int) -> None:
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(str(index))


def main() -> None:
    access_token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    person_urn = os.environ["LINKEDIN_PERSON_URN"]

    index = read_index() % len(POSTS)
    text = POSTS[index]

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    response = requests.post(API_URL, json=payload, headers=headers, timeout=30)

    if response.status_code not in (200, 201):
        print(f"LinkedIn post failed: {response.status_code} {response.text}", file=sys.stderr)
        sys.exit(1)

    print(f"Posted index {index}: {text[:60]}...")
    write_index(index + 1)


if __name__ == "__main__":
    main()
