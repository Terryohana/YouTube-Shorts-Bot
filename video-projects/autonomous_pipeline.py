import os
import sys
import json
import requests
import time
import asyncio
from bs4 import BeautifulSoup
import feedparser
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image
import io

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None

WORKSPACE = os.path.dirname(os.path.abspath(__file__))
VIDEO_PROJ = WORKSPACE
UPLOAD_SCRIPT = os.path.join(WORKSPACE, "..", ".agents", "skills", "youtube-uploader", "scripts", "upload.py")

def clean_text(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text(separator=' ').strip()

def get_top_topic():
    print("Fetching RSS from Android Police...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    res = requests.get("https://www.androidpolice.com/feed/", headers=headers, timeout=10)
    res.raise_for_status()
    feed = feedparser.parse(res.text)
    
    # Check if there is an unused topic file
    used_topics = []
    used_file = os.path.join(VIDEO_PROJ, "used_topics.json")
    if os.path.exists(used_file):
        with open(used_file, "r") as f:
            used_topics = json.load(f)
            
    for entry in feed.entries:
        if entry.link not in used_topics:
            return entry
            
    return feed.entries[0]

def get_article_data(url):
    print(f"Fetching full article: {url}")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    image_url = None
    desc = "Check out this amazing new update for Android!"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Try to get OG Image
        og_img = soup.find("meta", property="og:image")
        if og_img:
            image_url = og_img["content"]
            
        # Try to get meta description for a short script
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

def render_short(image_path, audio_path, output_path):
    print("Rendering video...")
    # Resize and blur background to fill vertical shorts format
    img = Image.open(image_path).convert("RGB")
    bg = img.resize((1080, 1920), Image.LANCZOS)
    
    # Create simple overlay
    temp_img = os.path.join(VIDEO_PROJ, "temp_autonomous_img.jpg")
    bg.save(temp_img, quality=95)
    
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration + 0.5
    
    image_clip = ImageClip(temp_img).set_duration(duration)
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
    if os.path.exists(temp_img):
        os.remove(temp_img)

async def generate_audio(text, output_path):
    print("Generating audio via Edge-TTS...")
    try:
        voice = "en-US-GuyNeural"
        communicate = edge_tts.Communicate(text, voice, rate="+10%")
        await communicate.save(output_path)
    except Exception as e:
        print(f"Edge-TTS failed ({e}), falling back to gTTS...")
        from gtts import gTTS
        tts = gTTS(text=text, lang='en', tld='us')
        tts.save(output_path)

def upload_video(video_path, title, description):
    print("Uploading to YouTube...")
    cmd = f'python "{UPLOAD_SCRIPT}" --file "{video_path}" --title "{title} #Shorts" --description "{description}" --privacy public'
    os.system(cmd)

def main():
    os.chdir(VIDEO_PROJ)
    print("Starting fully autonomous pipeline...")
    
    # 1. Get Topic
    entry = get_top_topic()
    title = clean_text(entry.title)
    url = entry.link
    
    # Create script from feed summary
    feed_summary = clean_text(entry.summary)
    
    # 2. Get high-res image
    image_url, article_desc = get_article_data(url)
    
    # Fallback to feed image if needed
    if not image_url and "media_content" in entry:
        image_url = entry.media_content[0]["url"]
        
    if not image_url:
        print("No image found! Using fallback generic image.")
        image_url = "https://images.unsplash.com/photo-1607252650355-f7fd0460ccdb?q=80&w=1080&auto=format&fit=crop"
        
    script_text = f"Did you know? {title}. {article_desc} {feed_summary[:150]}... Check the link for more! Don't forget to Subscribe!"
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    raw_img_path = "temp_raw_image.jpg"
    
    if gemini_key:
        print("GEMINI_API_KEY found! Generating AI script and background via REST API...")
        try:
            prompt = f"You are an expert YouTube Shorts scriptwriter. Write a 30-second punchy, high-retention script based on this news. DO NOT include any formatting, camera directions, or brackets. Only write the exact words that should be spoken out loud. Start with a strong hook.\nTitle: {title}\nSummary: {feed_summary}\nDescription: {article_desc}"
            
            # Text Generation (Gemini)
            text_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}"
            text_payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = requests.post(text_url, json=text_payload)
            res.raise_for_status()
            data = res.json()
            if "candidates" in data:
                script_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                print("Generated Script:", script_text)
            
            # Generate Background Image (Imagen)
            img_prompt = f"A highly engaging, high quality, colorful YouTube Shorts background related to this tech news, with NO text, abstract or literal: {title}"
            print("Generating custom AI background...")
            img_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={gemini_key}"
            img_payload = {
                "instances": [{"prompt": img_prompt}],
                "parameters": {"sampleCount": 1, "aspectRatio": "9:16", "outputOptions": {"mimeType": "image/jpeg"}}
            }
            res_img = requests.post(img_url, json=img_payload)
            res_img.raise_for_status()
            img_data = res_img.json()
            if "predictions" in img_data:
                import base64
                img_bytes = base64.b64decode(img_data["predictions"][0]["bytesBase64Encoded"])
                with open(raw_img_path, "wb") as f:
                    f.write(img_bytes)
            else:
                raise Exception("No predictions returned")
        except Exception as e:
            print(f"Gemini AI generation failed: {e}. Falling back to standard mode.")
            download_image(image_url, raw_img_path)
    else:
        print(f"Fallback Script: {script_text}")
        download_image(image_url, raw_img_path)
    
    # 4. Generate Audio
    audio_path = "temp_autonomous_audio.mp3"
    asyncio.run(generate_audio(script_text, audio_path))
    
    # 5. Render Video
    video_path = "autonomous_short.mp4"
    render_short(raw_img_path, audio_path, video_path)
    
    # 6. Upload
    desc = f"{article_desc}\n\nFull article: {url}\n\n#Android #TechNews #Shorts"
    # Ensure title is under 100 chars
    safe_title = title[:80]
    upload_video(video_path, safe_title, desc)
    
    # 7. Mark as used
    used_file = "used_topics.json"
    used_topics = []
    if os.path.exists(used_file):
        with open(used_file, "r") as f:
            used_topics = json.load(f)
    used_topics.append(url)
    with open(used_file, "w") as f:
        json.dump(used_topics, f)
        
    # Cleanup
    for f in [raw_img_path, audio_path]:
        if os.path.exists(f):
            os.remove(f)
            
    print("Pipeline complete!")

if __name__ == "__main__":
    main()
