import os
import sys
import json
import requests
import time
import base64
import struct
import wave
import textwrap
from bs4 import BeautifulSoup
import feedparser
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts
import asyncio

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
VIDEO_PROJ = WORKSPACE
UPLOAD_SCRIPT = os.path.join(WORKSPACE, "..", ".agents", "skills", "youtube-uploader", "scripts", "upload.py")
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

def clean_text(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=' ').strip()

def get_top_topic():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5"
    }
    feeds = [
        "https://www.androidpolice.com/feed/",
        "https://9to5google.com/feed/",
        "https://www.theverge.com/android/rss/index.xml",
        "https://techcrunch.com/category/mobile/feed/"
    ]
    
    used_topics = []
    used_file = os.path.join(VIDEO_PROJ, "used_topics.json")
    if os.path.exists(used_file):
        with open(used_file, "r") as f:
            used_topics = json.load(f)

    for feed_url in feeds:
        print(f"Fetching RSS from {feed_url}...")
        try:
            res = requests.get(feed_url, headers=headers, timeout=15)
            res.raise_for_status()
            feed = feedparser.parse(res.text)
            
            if not feed.entries:
                continue
                
            for entry in feed.entries:
                if entry.link not in used_topics:
                    print(f"Found new topic: {entry.title}")
                    return entry
            
            return feed.entries[0] # Fallback if all used
        except Exception as e:
            print(f"Failed to fetch {feed_url}: {e}")
            continue
            
    raise Exception("All RSS feeds failed to load. Check network connection.")

def get_article_data(url):
    print(f"Fetching full article: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    image_url = None
    desc = "Check out this amazing new update for Android!"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        og_img = soup.find("meta", property="og:image")
        if og_img:
            image_url = og_img["content"]
            
        og_desc = soup.find("meta", property="og:description")
        if og_desc:
            desc = og_desc["content"]
    except Exception as e:
        print(f"Error fetching article data, falling back to RSS defaults: {e}")
        
    return image_url, desc

def download_image(url, output_path):
    print(f"Downloading image from {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    with open(output_path, "wb") as f:
        f.write(res.content)

# ──────────────────────────────────────────────
# GEMINI API HELPERS
# ──────────────────────────────────────────────

def gemini_generate_script(api_key, title, feed_summary, article_desc):
    """Use Gemini 2.5 Flash to write a punchy script AND a short headline."""
    print("Generating AI script via Gemini 2.5 Flash...")
    prompt = (
        "You are an expert YouTube Shorts scriptwriter for a tech news channel.\n"
        "Based on the following news article, generate TWO things:\n"
        "1. HEADLINE: A short, punchy, clickbait-style headline (3-6 words, ALL CAPS) for the thumbnail.\n"
        "2. SCRIPT: A 30-second high-retention voiceover script. Start with a strong hook. "
        "DO NOT include formatting, camera directions, brackets, or asterisks. "
        "Only write the exact words to be spoken.\n\n"
        "Respond in this exact format:\n"
        "HEADLINE: <your headline>\n"
        "SCRIPT: <your script>\n\n"
        f"Title: {title}\nSummary: {feed_summary}\nDescription: {article_desc}"
    )
    url = f"{GEMINI_API_BASE}/gemini-2.5-flash:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, json=payload, timeout=60)
    res.raise_for_status()
    data = res.json()
    
    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    
    headline = title.upper()[:40]
    script = text
    
    # Parse HEADLINE: and SCRIPT: format
    if "HEADLINE:" in text and "SCRIPT:" in text:
        parts = text.split("SCRIPT:")
        headline_part = parts[0]
        script = parts[1].strip()
        headline = headline_part.replace("HEADLINE:", "").strip().strip('"').upper()
    
    print(f"Headline: {headline}")
    print(f"Script: {script[:200]}...")
    return headline, script


def gemini_generate_image(api_key, title, output_path):
    """Use Gemini 2.5 Flash Image model to generate a cyberpunk background."""
    print("Generating AI background via Gemini Image model...")
    img_prompt = (
        f"Generate a dramatic, hyper-realistic, cyberpunk-style vertical background image "
        f"for a YouTube Short about: {title}. "
        f"Dark tones with glowing neon accents (blue, green, red). "
        f"Cinematic lighting, high contrast, tech-themed elements. "
        f"Do NOT include any text or words in the image. "
        f"Aspect ratio 9:16, portrait orientation."
    )
    url = f"{GEMINI_API_BASE}/gemini-2.5-flash-image:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": img_prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
    }
    res = requests.post(url, json=payload, timeout=120)
    res.raise_for_status()
    data = res.json()
    
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            img_bytes = base64.b64decode(part["inlineData"]["data"])
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            print(f"AI background saved ({len(img_bytes)} bytes)")
            return True
    
    raise Exception("No image data in response")


def gemini_generate_tts(api_key, script_text, output_path):
    """Use Gemini 2.5 Flash TTS to generate high-quality voiceover."""
    print("Generating AI voiceover via Gemini TTS...")
    url = f"{GEMINI_API_BASE}/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": script_text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": "Kore"
                    }
                }
            }
        }
    }
    res = requests.post(url, json=payload, timeout=120)
    res.raise_for_status()
    data = res.json()
    
    for part in data.get("candidates", [{}])[0].get("content", {}).get("parts", []):
        if "inlineData" in part:
            audio_bytes = base64.b64decode(part["inlineData"]["data"])
            # Convert raw PCM (16-bit, 24kHz, mono) to WAV
            wav_path = output_path.replace(".mp3", ".wav")
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(24000)
                wf.writeframes(audio_bytes)
            print(f"AI voiceover saved ({len(audio_bytes)} bytes)")
            return wav_path
    
    raise Exception("No audio data in response")


# ──────────────────────────────────────────────
# IMAGE COMPOSITING (text overlay like mq2.jpg)
# ──────────────────────────────────────────────

def overlay_headline_on_image(image_path, headline, output_path):
    """Drastically improved cyberpunk thumbnail overlay."""
    print(f"Overlaying headline: {headline}")
    img = Image.open(image_path).convert("RGBA")
    
    # 1. Resize to exact 9:16
    img = img.resize((1080, 1920), Image.LANCZOS)
    
    # 2. Darken the background significantly (60% black) so the neon text pops
    dark_overlay = Image.new("RGBA", img.size, (0, 0, 0, 150))
    img = Image.alpha_composite(img, dark_overlay)
    
    # 3. Setup massive, bold font base
    font_size = 140
    def get_font(size):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
        except (OSError, IOError):
            try:
                return ImageFont.truetype("arialbd.ttf", size)
            except (OSError, IOError):
                return ImageFont.load_default()
                
    font = get_font(font_size)
    
    # 4. Wrap text very tightly (approx 2-3 words per line) for maximum impact
    draw = ImageDraw.Draw(img)
    wrapped = textwrap.wrap(headline, width=12)
    
    # 5. Dynamically shrink the font if any line is wider than the image bounds (with padding)
    max_allowed_width = 980 # 50px padding on each side (out of 1080)
    while font_size > 40:
        too_wide = False
        for line in wrapped:
            bbox = draw.textbbox((0, 0), line, font=font)
            if (bbox[2] - bbox[0]) > max_allowed_width:
                too_wide = True
                break
        if not too_wide:
            break
        font_size -= 5
        font = get_font(font_size)
    
    line_height = font_size + 30
    total_height = len(wrapped) * line_height
    y_start = (1920 - total_height) // 2 - 50 # Slightly above exact center
    
    # Cyberpunk Yellow
    text_color = (255, 230, 0, 255)
    shadow_color = (0, 0, 0, 255)
    
    for i, line in enumerate(wrapped):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (1080 - text_width) // 2
        y = y_start + i * line_height
        
        # Draw thick black outline (stroke)
        thickness = 8
        for ox in range(-thickness, thickness + 1, 2):
            for oy in range(-thickness, thickness + 1, 2):
                draw.text((x + ox, y + oy), line, font=font, fill=shadow_color)
                
        # Draw heavy drop shadow down and right
        draw.text((x + 12, y + 15), line, font=font, fill=shadow_color)
        draw.text((x + 15, y + 18), line, font=font, fill=shadow_color)
        draw.text((x + 20, y + 25), line, font=font, fill=shadow_color)
        
        # Draw main bright yellow text
        draw.text((x, y), line, font=font, fill=text_color)
    
    # Save as RGB
    img_rgb = img.convert("RGB")
    
    # Boost contrast of final image slightly for that premium punchy look
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(img_rgb)
    img_rgb = enhancer.enhance(1.2)
    
    img_rgb.save(output_path, quality=95)
    print("Headline overlay complete")


# ──────────────────────────────────────────────
# VIDEO RENDERING
# ──────────────────────────────────────────────

async def fallback_generate_audio(text, output_path):
    print("Generating audio via Edge-TTS (fallback)...")
    try:
        voice = "en-US-ChristopherNeural"
        communicate = edge_tts.Communicate(text, voice, rate="+15%", pitch="+5Hz")
        await communicate.save(output_path)
    except Exception as e:
        print(f"Edge-TTS failed ({e}), falling back to gTTS...")
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', tld='us')
        tts.save(output_path)


def render_short(image_path, audio_path, output_path):
    print("Rendering video...")
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration + 0.5
    
    image_clip = ImageClip(image_path).set_duration(duration)
    video_clip = image_clip.set_audio(audio_clip)
    
    video_clip.write_videofile(
        output_path, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        logger=None
    )
    
    audio_clip.close()
    video_clip.close()


def upload_video(video_path, title, description):
    print("Uploading to YouTube...")
    cmd = f'python "{UPLOAD_SCRIPT}" --file "{video_path}" --title "{title} #Shorts" --description "{description}" --privacy public'
    os.system(cmd)


# ──────────────────────────────────────────────
# MAIN PIPELINE
# ──────────────────────────────────────────────

def main():
    os.chdir(VIDEO_PROJ)
    print("Starting fully autonomous pipeline...")
    
    # 1. Get Topic
    entry = get_top_topic()
    title = clean_text(entry.title)
    url = entry.link
    feed_summary = clean_text(entry.summary)
    
    # 2. Get article data (image + description)
    image_url, article_desc = get_article_data(url)
    if not image_url and "media_content" in entry:
        image_url = entry.media_content[0]["url"]
    if not image_url:
        image_url = "https://images.unsplash.com/photo-1607252650355-f7fd0460ccdb?q=80&w=1080&auto=format&fit=crop"
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    raw_img_path = "temp_raw_image.jpg"
    final_img_path = "temp_final_image.jpg"
    audio_path = "temp_autonomous_audio.wav"
    headline = title.upper()[:40]
    script_text = f"Did you know? {title}. {article_desc} {feed_summary[:150]}... Check the link for more! Don't forget to Subscribe!"
    
    if gemini_key:
        print("=" * 50)
        print("GEMINI API KEY FOUND - Using AI generation")
        print("=" * 50)
        
        # Step A: Generate Script + Headline
        try:
            headline, script_text = gemini_generate_script(gemini_key, title, feed_summary, article_desc)
        except Exception as e:
            print(f"Script generation failed: {e}")
        
        # Step B: Generate Background Image
        try:
            gemini_generate_image(gemini_key, title, raw_img_path)
        except Exception as e:
            print(f"Image generation failed: {e}. Using article image.")
            download_image(image_url, raw_img_path)
        
        # Step C: Overlay headline text on the image
        try:
            overlay_headline_on_image(raw_img_path, headline, final_img_path)
        except Exception as e:
            print(f"Headline overlay failed: {e}. Using raw image.")
            img = Image.open(raw_img_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
            img.save(final_img_path, quality=95)
        
        # Step D: Generate AI Voice
        try:
            audio_path = gemini_generate_tts(gemini_key, script_text, audio_path)
        except Exception as e:
            print(f"Gemini TTS failed: {e}. Falling back to old TTS implementation.")
            audio_path = "temp_autonomous_audio.mp3"
            asyncio.run(fallback_generate_audio(script_text, audio_path))
    else:
        print("No GEMINI_API_KEY - using basic mode")
        download_image(image_url, raw_img_path)
        img = Image.open(raw_img_path).convert("RGB").resize((1080, 1920), Image.LANCZOS)
        img.save(final_img_path, quality=95)
        audio_path = "temp_autonomous_audio.mp3"
        asyncio.run(fallback_generate_audio(script_text, audio_path))
    
    # 3. Render Video
    video_path = "autonomous_short.mp4"
    render_short(final_img_path, audio_path, video_path)
    
    # 4. Upload
    desc = f"{article_desc}\n\nFull article: {url}\n\n#Android #TechNews #Shorts"
    safe_title = title[:80]
    upload_video(video_path, safe_title, desc)
    
    # 5. Mark as used
    used_file = "used_topics.json"
    used_topics = []
    if os.path.exists(used_file):
        with open(used_file, "r") as f:
            used_topics = json.load(f)
    used_topics.append(url)
    with open(used_file, "w") as f:
        json.dump(used_topics, f)
        
    # Cleanup
    for fpath in [raw_img_path, final_img_path, audio_path]:
        if os.path.exists(fpath):
            os.remove(fpath)
            
    print("Pipeline complete!")

if __name__ == "__main__":
    main()
