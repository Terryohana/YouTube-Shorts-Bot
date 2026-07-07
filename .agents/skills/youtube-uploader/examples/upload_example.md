# YouTube Uploader Skill – Example Usage

This document shows common usage patterns for the YouTube Uploader skill.

---

## Example 1 – Quick Public Upload (Default)

Upload a video publicly with an auto-generated thumbnail and SEO description:

```bash
python .agents/skills/youtube-uploader/scripts/upload.py \
  --file "C:/Videos/my_tutorial.mp4" \
  --title "Python Tutorial – Beginner to Advanced" \
  --description "In this video we cover... \n\n 0:00 Intro \n 1:20 Variables..." \
  --thumbnail "C:/Videos/generated_thumbnail.jpg"
```

**Output:**
```
✅ Upload complete!
   Video ID  : dQw4w9WgXcQ
   Video URL : https://www.youtube.com/watch?v=dQw4w9WgXcQ
   Privacy   : private
```

---

## Example 2 – Full Metadata Upload

```bash
python .agents/skills/youtube-uploader/scripts/upload.py \
  --file "C:/Videos/android_launcher_review.mp4" \
  --title "Best Android Launchers 2026 – Top 10 Picks" \
  --description "In this video I review the top 10 Android launchers of 2026, including Midnight Console Launcher, Nova, and more." \
  --tags "android,launcher,customization,apps,review,2026" \
  --category 28 \
  --privacy unlisted \
  --thumbnail "C:/Videos/thumbnail.jpg"
```

---

## Example 3 – Gaming Video Upload

```bash
python .agents/skills/youtube-uploader/scripts/upload.py \
  --file "C:/Recordings/gameplay.mp4" \
  --title "Epic Gameplay Highlights – June 2026" \
  --tags "gaming,highlights,gameplay" \
  --category 20 \
  --privacy private
```

---

## Example 4 – Music Upload

```bash
python .agents/skills/youtube-uploader/scripts/upload.py \
  --file "C:/Music/original_track.mp4" \
  --title "Original Track – Midnight Vibes" \
  --description "Original music produced by me. Enjoy!" \
  --category 10 \
  --privacy public
```

---

## Quota Reference

| Action | API Units |
|--------|-----------|
| Upload video | ~1,600 units |
| Set thumbnail | 50 units |
| Daily limit | 10,000 units |
| **Max uploads/day** | **~6 videos** |

> To increase quota, submit a [YouTube API quota increase request](https://support.google.com/youtube/contact/yt_api_form) to Google.

---

## Privacy Strategy

| Stage | Setting |
|-------|---------|
| Upload & review | `private` |
| Share with team | `unlisted` |
| Live to public | `public` |

You can change privacy via YouTube Studio after upload — no re-upload needed.
