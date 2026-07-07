---
name: youtube-uploader
description: Uploads videos to YouTube using the official YouTube Data API v3 with OAuth 2.0 authentication. Supports full metadata control (title, description, tags, category, privacy), custom thumbnails, and resumable chunked uploads for large files.
---

# YouTube Uploader Skill

This skill enables automated, programmatic video uploads to YouTube using the **official YouTube Data API v3** with secure OAuth 2.0 authentication. It avoids fragile browser automation and instead uses Google's supported Python client library.

---

## Prerequisites

Before using this skill, ensure the following are installed and configured:

### 1. Python Dependencies
Run the setup script once:
```bash
pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```
Or use the helper script:
```bash
python .agents/skills/youtube-uploader/scripts/setup.py
```

### 2. Google Cloud Project & OAuth Credentials
Follow these one-time steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **YouTube Data API v3** from the API Library
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Desktop App**
6. Download the JSON file and save it as:
   ```
   .agents/skills/youtube-uploader/credentials/client_secrets.json
   ```
7. Add your Google account email to **OAuth consent screen → Test users** (required while app is in "Testing" mode)

### 3. First-Time Auth (Generate Token)
Run this once to complete the OAuth flow and cache your token:
```bash
python .agents/skills/youtube-uploader/scripts/authenticate.py
```
This opens a browser window for you to authorize the app. The token is saved to:
```
.agents/skills/youtube-uploader/credentials/token.pickle
```
Subsequent uploads will use this cached token silently.

---

## Usage Instructions

When the user asks you to upload a video to YouTube, follow these steps:

### Step 1 – Verify Prerequisites
1. Check that `client_secrets.json` exists in the credentials folder.
2. Check that `token.pickle` exists (run `authenticate.py` if not).
3. Check that Python packages are installed.

### Step 2 – Gather Upload Metadata & Assets
1. **File details**: Infer or ask the user for the absolute path to the video.
2. **SEO Description & Timestamps**: Automatically generate an SEO-optimized description that includes topic timestamps for the video based on its content or the user's description. Include relevant keywords and hashtags.
3. **Thumbnail Generation**: Automatically use your `generate_image` tool to create a high-quality, eye-catching thumbnail. Save it to a local path (e.g., `thumbnail.jpg` in your scratch directory).
4. Ask the user (or infer) for:
   - `title` — Video title
   - `category_id` — YouTube category ID (default: `"22"`)

### Step 3 – Run the Upload Script
```bash
python .agents/skills/youtube-uploader/scripts/upload.py \
  --file "C:/path/to/your/video.mp4" \
  --title "My Awesome Video" \
  --description "Your auto-generated SEO description here... \n\n 0:00 Intro..." \
  --tags "seo,tags,here" \
  --category 22 \
  --privacy public \
  --thumbnail "C:/path/to/generated_thumbnail.jpg"
```

### Step 4 – Verify Upload
The script outputs the YouTube video URL and Video ID on success. Share this with the user.

---

## Key Technical Notes

- **Quota**: YouTube Data API allows ~10,000 units/day. One upload ≈ 1,600 units → ~6 uploads/day on unverified projects.
- **Chunked Uploads**: The script uses 1MB resumable chunks for large file reliability.
- **Privacy Default**: Always uploads as `private` by default — safe for review before publishing.
- **Category IDs**: Common ones:
  - `1` = Film & Animation
  - `2` = Autos & Vehicles
  - `10` = Music
  - `20` = Gaming
  - `22` = People & Blogs
  - `24` = Entertainment
  - `26` = How-to & Style
  - `28` = Science & Technology

---

## Files in This Skill

| File | Purpose |
|------|---------|
| `scripts/setup.py` | Installs required Python packages |
| `scripts/authenticate.py` | Runs OAuth flow and saves token |
| `scripts/upload.py` | Main upload script (CLI) |
| `credentials/` | Stores `client_secrets.json` and `token.pickle` (gitignored) |
| `examples/upload_example.md` | Example usage patterns |

---

## Security Notes

> **IMPORTANT**: Never commit `client_secrets.json` or `token.pickle` to version control.
> These files contain sensitive OAuth credentials tied to your Google account.
> A `.gitignore` entry is included automatically in the `credentials/` folder.
