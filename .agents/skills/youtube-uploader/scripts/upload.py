"""
upload.py - YouTube Video Uploader
Full-featured YouTube upload script with resumable chunking, metadata support,
thumbnail upload, and exponential backoff retry logic.

Usage:
    python upload.py --file "video.mp4" --title "My Video" --description "..." \
                     --tags "tag1,tag2" --category 22 --privacy private \
                     --thumbnail "thumb.jpg"

Requirements:
    Run authenticate.py first to generate credentials/token.pickle
"""

import argparse
import http.client
import httplib2
import os
import pickle
import random
import sys
import time
from pathlib import Path

# Google API imports
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request
except ImportError:
    print("❌ Missing dependencies. Please run: python scripts/setup.py")
    raise SystemExit(1)

# ──────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────
SKILL_DIR = Path(__file__).parent.parent
CREDENTIALS_DIR = SKILL_DIR / "credentials"
TOKEN_FILE = CREDENTIALS_DIR / "token.pickle"

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
CHUNK_SIZE = 1024 * 1024  # 1 MB chunks for resumable uploads

# Retry config
MAX_RETRIES = 10
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    IOError,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
)

# YouTube category IDs reference
CATEGORIES = {
    1: "Film & Animation",
    2: "Autos & Vehicles",
    10: "Music",
    15: "Pets & Animals",
    17: "Sports",
    20: "Gaming",
    22: "People & Blogs",
    23: "Comedy",
    24: "Entertainment",
    25: "News & Politics",
    26: "How-to & Style",
    27: "Education",
    28: "Science & Technology",
    29: "Nonprofits & Activism",
}


# ──────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────
def get_authenticated_service():
    """Load cached credentials and build YouTube API client."""
    if not TOKEN_FILE.exists():
        print("❌ No token found. Please run: python scripts/authenticate.py")
        raise SystemExit(1)

    with open(TOKEN_FILE, "rb") as token:
        creds = pickle.load(token)

    # Refresh if expired
    if creds and creds.expired and creds.refresh_token:
        print("🔄 Refreshing access token...")
        creds.refresh(Request())
        with open(TOKEN_FILE, "wb") as token:
            pickle.dump(creds, token)

    return build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        credentials=creds,
        cache_discovery=False,
    )


# ──────────────────────────────────────────────
# Upload with Exponential Backoff
# ──────────────────────────────────────────────
def resumable_upload(request, file_size_mb: float):
    """Execute a resumable upload with exponential backoff retry logic."""
    response = None
    error = None
    retry = 0

    print(f"\n🚀 Starting upload ({file_size_mb:.1f} MB) with 1MB chunks...\n")

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                uploaded_mb = file_size_mb * status.progress()
                bar = "█" * (progress // 5) + "░" * (20 - progress // 5)
                print(
                    f"  [{bar}] {progress:3d}%  ({uploaded_mb:.1f}/{file_size_mb:.1f} MB)",
                    end="\r",
                    flush=True,
                )
            if response is not None:
                print()  # newline after progress bar
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"HTTP {e.resp.status}: {e.content}"
            else:
                raise
        except RETRIABLE_EXCEPTIONS as e:
            error = f"Retriable error: {e}"

        if error is not None:
            retry += 1
            if retry > MAX_RETRIES:
                print(f"\n❌ Upload failed after {MAX_RETRIES} retries.")
                raise Exception(f"Max retries exceeded. Last error: {error}")

            sleep_time = random.uniform(0, 2**retry)
            print(f"\n  ⚠️  {error}")
            print(f"  ↻  Retry {retry}/{MAX_RETRIES} in {sleep_time:.1f}s...")
            time.sleep(sleep_time)
            error = None

    return response


# ──────────────────────────────────────────────
# Main Upload Function
# ──────────────────────────────────────────────
def upload_video(youtube, args):
    """Build the upload request and execute it."""
    file_path = Path(args.file)

    if not file_path.exists():
        print(f"❌ Video file not found: {file_path}")
        raise SystemExit(1)

    file_size = file_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    category_name = CATEGORIES.get(args.category, "Unknown")

    print("=" * 55)
    print("  📹 YouTube Video Upload")
    print("=" * 55)
    print(f"  File      : {file_path.name}")
    print(f"  Size      : {file_size_mb:.1f} MB")
    print(f"  Title     : {args.title}")
    print(f"  Privacy   : {args.privacy}")
    print(f"  Category  : {args.category} ({category_name})")
    if tags:
        print(f"  Tags      : {', '.join(tags[:5])}{'...' if len(tags) > 5 else ''}")
    print("=" * 55)

    body = {
        "snippet": {
            "title": args.title,
            "description": args.description,
            "tags": tags,
            "categoryId": str(args.category),
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": args.privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        str(file_path),
        chunksize=CHUNK_SIZE,
        resumable=True,
    )

    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media,
    )

    response = resumable_upload(insert_request, file_size_mb)

    video_id = response.get("id")
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    print(f"\n✅ Upload complete!")
    print(f"   Video ID  : {video_id}")
    print(f"   Video URL : {video_url}")
    print(f"   Privacy   : {args.privacy}")

    # Upload thumbnail if provided
    if args.thumbnail:
        thumbnail_path = Path(args.thumbnail)
        if thumbnail_path.exists():
            print(f"\n🖼️  Uploading thumbnail: {thumbnail_path.name}...")
            try:
                youtube.thumbnails().set(
                    videoId=video_id,
                    media_body=MediaFileUpload(str(thumbnail_path)),
                ).execute()
                print("   ✅ Thumbnail uploaded successfully!")
            except HttpError as e:
                print(f"   ⚠️  Thumbnail upload failed: {e}")
                print("   (Custom thumbnails require a verified YouTube account)")
        else:
            print(f"   ⚠️  Thumbnail file not found: {thumbnail_path}")

    return video_id, video_url


# ──────────────────────────────────────────────
# CLI Entry Point
# ──────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser(
        description="Upload a video to YouTube via the Data API v3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Public upload (default):
  python upload.py --file video.mp4 --title "My Video"

  # Full metadata upload:
  python upload.py --file video.mp4 --title "Tutorial" \\
    --description "Full tutorial" --tags "python,tutorial,coding" \\
    --category 28 --privacy unlisted --thumbnail thumb.jpg

Category IDs:
  1=Film  10=Music  20=Gaming  22=People&Blogs
  24=Entertainment  26=HowTo  28=Science&Tech
        """,
    )
    parser.add_argument("--file", required=True, help="Path to the video file")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument(
        "--description", default="", help="Video description (default: empty)"
    )
    parser.add_argument(
        "--tags", default="", help="Comma-separated tags (default: none)"
    )
    parser.add_argument(
        "--category",
        type=int,
        default=22,
        help="YouTube category ID (default: 22 = People & Blogs)",
    )
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default="public",
        help="Privacy setting (default: public)",
    )
    parser.add_argument(
        "--thumbnail", default=None, help="Path to thumbnail image (JPEG/PNG, optional)"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        youtube = get_authenticated_service()
        video_id, video_url = upload_video(youtube, args)
        # Output machine-readable result for agent parsing
        print(f"\n--- RESULT ---")
        print(f"VIDEO_ID={video_id}")
        print(f"VIDEO_URL={video_url}")
        print(f"PRIVACY={args.privacy}")
    except HttpError as e:
        print(f"\n❌ YouTube API error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
