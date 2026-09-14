# LinkedIn Auto-Post + Job Alert

Two independent automations, both using official APIs (no scraping, no bots
that violate LinkedIn's terms):

1. **`post_linkedin.yml`** — posts 2x/day to your LinkedIn feed via LinkedIn's
   official Share API, rotating through pre-written posts in
   `scripts/content_pool.py`.
2. **`job_alert.yml`** — once a day, emails you a digest of Frontend
   Developer / JavaScript / HTML / CSS jobs in Pakistan (via the Jooble API).
   No auto-apply — you review and apply yourself.

Both run on GitHub Actions, so your PC doesn't need to be on.

---

## Setup (one-time, ~20 minutes)

### 1. Push this folder to a new GitHub repo
```
git init
git add .
git commit -m "init"
gh repo create linkedin-ai-assistant --private --source=. --push
```
(or create the repo manually on github.com and push)

### 2. Create a LinkedIn app
1. Go to https://www.linkedin.com/developers/apps -> **Create app**.
2. Under **Products**, request:
   - **Sign In with LinkedIn using OpenID Connect**
   - **Share on LinkedIn**
   (Both are auto-approved instantly for personal use.)
3. Under **Auth**, add this redirect URL:
   `http://localhost:8080/callback`
4. Copy the **Client ID** and **Client Secret** from the Auth tab.

### 3. Get your access token (run locally, once)
```
cd scripts
pip install -r ../requirements.txt
set LINKEDIN_CLIENT_ID=your_client_id
set LINKEDIN_CLIENT_SECRET=your_client_secret
python get_linkedin_token.py
```
This opens your browser to log into LinkedIn and approve access, then prints
`LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_URN`. Copy both.

> The token expires after ~60 days — just re-run this script and update the
> GitHub secret when that happens.

### 4. Get a free Jooble API key
Sign up at https://jooble.org/api/about — takes a minute, gives you an API key
by email.

### 5. Create a Gmail App Password
1. Turn on 2-Step Verification on your Google account (if not already on).
2. Go to https://myaccount.google.com/apppasswords and create an app password.
3. Use that (not your normal Gmail password) for `GMAIL_APP_PASSWORD`.

### 6. Add GitHub repo secrets
In your repo: **Settings -> Secrets and variables -> Actions -> New repository secret**.
Add:
| Secret | Value |
|---|---|
| `LINKEDIN_ACCESS_TOKEN` | from step 3 |
| `LINKEDIN_PERSON_URN` | from step 3 |
| `JOOBLE_API_KEY` | from step 4 |
| `GMAIL_ADDRESS` | your Gmail address |
| `GMAIL_APP_PASSWORD` | from step 5 |

### 7. Enable the workflows
Go to the **Actions** tab of your repo and enable workflows if prompted.
You can also trigger each one manually via **Run workflow** to test before
waiting for the schedule.

---

## Customizing

- **Post content**: edit `scripts/content_pool.py` — add/remove/reorder posts
  any time, the rotation just keeps going.
- **Post times**: edit the `cron` lines in `.github/workflows/post_linkedin.yml`
  (times are in UTC; PKT = UTC+5).
- **Job search terms**: edit `JOB_KEYWORDS` / `JOB_LOCATION` in
  `.github/workflows/job_alert.yml`.

## Notes

- LinkedIn auto-apply bots are against LinkedIn's terms and risk account bans
  — that's why this only does job *alerts* (email), with applying left to you.
- The LinkedIn posting here uses LinkedIn's own official API with your
  consent (OAuth), so it does not violate their terms the way scraping/browser
  bots would.
