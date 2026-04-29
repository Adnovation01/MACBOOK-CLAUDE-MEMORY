# How to Add Social Media Cookies

Social plugins (Facebook, Instagram, LinkedIn, Twitter) require a valid browser session cookie to scrape. You log in once in your real browser, export the cookies, and paste the JSON file into the right folder. The scraper then reuses that session.

---

## Step 1 — Install a Cookie Exporter Extension

Install one of these in Chrome or Firefox:

| Extension | Chrome | Firefox |
|---|---|---|
| **Cookie-Editor** (recommended) | [Chrome Web Store](https://chrome.google.com/webstore/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm) | [Firefox Add-ons](https://addons.mozilla.org/en-US/firefox/addon/cookie-editor/) |
| EditThisCookie | [Chrome Web Store](https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg) | — |

---

## Step 2 — Log In to the Platform

In your **real browser** (not incognito), log in to the platform you want to enable:

- Facebook → `https://www.facebook.com`
- Instagram → `https://www.instagram.com`
- LinkedIn → `https://www.linkedin.com`
- Twitter/X → `https://www.twitter.com`

Make sure you are fully logged in and can see your feed/home page.

---

## Step 3 — Export Cookies as JSON

1. While on the platform's homepage, click the Cookie-Editor extension icon in your toolbar.
2. Click **Export** → **Export as JSON**.
3. The JSON is copied to your clipboard.

The exported JSON looks like this (abbreviated):

```json
[
  {
    "name": "c_user",
    "value": "100012345678",
    "domain": ".facebook.com",
    "path": "/",
    "expires": 1780000000,
    "httpOnly": false,
    "secure": true,
    "sameSite": "None"
  },
  {
    "name": "xs",
    "value": "12%3AaBcDeFgHiJ...",
    "domain": ".facebook.com",
    ...
  }
]
```

---

## Step 4 — Save the File

Paste the JSON into a new file. Save it to the `config/sessions/` folder inside the project:

| Platform | File path |
|---|---|
| Facebook | `config/sessions/facebook.json` |
| Instagram | `config/sessions/instagram.json` |
| LinkedIn | `config/sessions/linkedin.json` |
| Twitter/X | `config/sessions/twitter.json` |

Example using a text editor:

```
ai_consulting_business/
└── config/
    └── sessions/
        ├── facebook.json    ← paste exported JSON here
        ├── instagram.json
        ├── linkedin.json
        └── twitter.json
```

> **Security note:** These files contain live session tokens. Do not commit them to git, share them, or put them anywhere public. The `.gitignore` already excludes `config/sessions/`.

---

## Step 5 — Verify It Works

1. Go to `http://localhost:5001/settings`.
2. The plugin status indicators next to each social platform should show **✓ Set** in green.
3. Go to `http://localhost:5001/plugins` and click **Run Full Diagnostics** — the health dot for that plugin should turn green.

If the dot stays grey/red, the cookie file is in the wrong location or the JSON is malformed.

---

## Cookie Expiry

Browser session cookies typically last **30–90 days**. When they expire:

1. Log back in to the platform in your browser.
2. Re-export cookies with Cookie-Editor.
3. Overwrite the existing file in `config/sessions/`.

The health check will automatically pick up the new cookies on the next diagnostic run.

---

## Tips for Better Results

- **Export from Chrome on a desktop**, not mobile — cookies from mobile browsers are often scoped differently.
- **Don't log out** of the platform after exporting. Logging out invalidates the session token.
- **Use a dedicated account** for scraping, not your main personal account. If the scraper triggers a rate limit or unusual-activity warning, only the dedicated account gets flagged.
- **LinkedIn** is the most aggressive — if scraping LinkedIn, keep `rate_limit_seconds` at 10+ seconds between requests and limit to 20–30 searches per day.
