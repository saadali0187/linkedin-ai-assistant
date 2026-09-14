"""Posts the next item from content_pool.POSTS to LinkedIn using the official
LinkedIn API (UGC Posts endpoint, w_member_social scope).

Required environment variables:
    LINKEDIN_ACCESS_TOKEN  - OAuth access token with w_member_social scope
    LINKEDIN_PERSON_URN    - e.g. "urn:li:person:AbCdEfGhIj"

Optional:
    WITH_IMAGE  - "true" to attach an image from assets/images (rotates
                  through whatever files are in that folder). Any other
                  value (or an empty images folder) posts text-only.

State:
    state/post_index.txt   - index of the next text post to publish (rotates)
    state/image_index.txt  - index of the next image to attach (rotates)
"""

import glob
import os
import sys

import requests

from content_pool import POSTS

STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "state")
POST_STATE_FILE = os.path.join(STATE_DIR, "post_index.txt")
IMAGE_STATE_FILE = os.path.join(STATE_DIR, "image_index.txt")
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "images")

UGC_POSTS_URL = "https://api.linkedin.com/v2/ugcPosts"
REGISTER_UPLOAD_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"


def read_index(state_file: str) -> int:
    if not os.path.exists(state_file):
        return 0
    with open(state_file, "r") as f:
        content = f.read().strip()
        return int(content) if content else 0


def write_index(state_file: str, index: int) -> None:
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        f.write(str(index))


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def list_images() -> list[str]:
    if not os.path.isdir(IMAGES_DIR):
        return []
    return sorted(
        f
        for f in glob.glob(os.path.join(IMAGES_DIR, "*"))
        if os.path.isfile(f) and f.lower().endswith(IMAGE_EXTENSIONS)
    )


def upload_image(access_token: str, person_urn: str, image_path: str) -> str:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    register_payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": person_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    register_response = requests.post(
        REGISTER_UPLOAD_URL, json=register_payload, headers=headers, timeout=30
    )
    register_response.raise_for_status()
    register_data = register_response.json()["value"]

    upload_url = register_data["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = register_data["asset"]

    with open(image_path, "rb") as f:
        upload_response = requests.put(
            upload_url,
            data=f,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=60,
        )
    upload_response.raise_for_status()

    return asset_urn


def main() -> None:
    access_token = os.environ["LINKEDIN_ACCESS_TOKEN"]
    person_urn = os.environ["LINKEDIN_PERSON_URN"]
    want_image = os.environ.get("WITH_IMAGE", "false").lower() == "true"

    post_index = read_index(POST_STATE_FILE) % len(POSTS)
    text = POSTS[post_index]

    images = list_images() if want_image else []
    image_index = None
    asset_urn = None

    if want_image and images:
        image_index = read_index(IMAGE_STATE_FILE) % len(images)
        asset_urn = upload_image(access_token, person_urn, images[image_index])
    elif want_image:
        print("WITH_IMAGE=true but no files found in assets/images; posting text-only.")

    share_content = {
        "shareCommentary": {"text": text},
        "shareMediaCategory": "IMAGE" if asset_urn else "NONE",
    }
    if asset_urn:
        share_content["media"] = [{"status": "READY", "media": asset_urn}]

    payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {"com.linkedin.ugc.ShareContent": share_content},
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }

    response = requests.post(UGC_POSTS_URL, json=payload, headers=headers, timeout=30)

    if response.status_code not in (200, 201):
        print(f"LinkedIn post failed: {response.status_code} {response.text}", file=sys.stderr)
        sys.exit(1)

    print(f"Posted index {post_index} (image={asset_urn is not None}): {text[:60]}...")
    write_index(POST_STATE_FILE, post_index + 1)
    if image_index is not None:
        write_index(IMAGE_STATE_FILE, image_index + 1)


if __name__ == "__main__":
    main()
