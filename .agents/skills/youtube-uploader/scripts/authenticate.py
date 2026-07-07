"""
authenticate.py - YouTube Uploader OAuth2 Authentication
Performs the one-time OAuth 2.0 flow and caches the token for future uploads.
Run this script once before using the upload.py script.
"""

import os
import pickle
from pathlib import Path

# Google API imports
try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("❌ Missing dependencies. Please run: python scripts/setup.py")
    raise SystemExit(1)

# Scopes required for YouTube uploads
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Resolve paths relative to this script's location
SKILL_DIR = Path(__file__).parent.parent
CREDENTIALS_DIR = SKILL_DIR / "credentials"
CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.pickle"


def authenticate():
    """Run OAuth 2.0 flow and cache credentials."""

    if not CLIENT_SECRETS_FILE.exists():
        print(f"❌ client_secrets.json not found at:\n   {CLIENT_SECRETS_FILE}")
        print("\n📋 How to get it:")
        print("   1. Go to https://console.cloud.google.com/")
        print("   2. Enable YouTube Data API v3")
        print("   3. Create OAuth 2.0 Desktop credentials")
        print(f"   4. Download and save as: {CLIENT_SECRETS_FILE}")
        raise SystemExit(1)

    creds = None

    # Load existing token if available
    if TOKEN_FILE.exists():
        with open(TOKEN_FILE, "rb") as token:
            creds = pickle.load(token)

    # Refresh or re-authenticate
    if creds and creds.valid:
        print("✅ Existing credentials are still valid. No re-authentication needed.")
        return creds

    if creds and creds.expired and creds.refresh_token:
        print("🔄 Refreshing expired credentials...")
        try:
            creds.refresh(Request())
            print("✅ Credentials refreshed successfully.")
        except Exception as e:
            print(f"⚠️ Failed to refresh ({e}). Forcing re-authentication...")
            creds = None
            
    if not creds or not creds.valid:
        print("🌐 Opening browser for YouTube authorization...")
        print("   Please log in and grant upload permissions.\n")
        flow = InstalledAppFlow.from_client_secrets_file(
            str(CLIENT_SECRETS_FILE), SCOPES
        )
        creds = flow.run_local_server(port=0, open_browser=False)
        print("✅ Authorization successful!")

    # Save the credentials for future use
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOKEN_FILE, "wb") as token:
        pickle.dump(creds, token)

    print(f"💾 Token saved to: {TOKEN_FILE}")
    print("\n🎉 You're ready to upload! Run: python scripts/upload.py --help")
    return creds


if __name__ == "__main__":
    authenticate()
