import sys
import os
import subprocess
import time
import pyttsx3
from playwright.sync_api import sync_playwright
from moviepy.editor import VideoFileClip, AudioFileClip

def generate_voiceover():
    print("Step 1: Generating voiceover...")
    with open("daily_script.txt", "r", encoding="utf-8") as f:
        script = f.read()
        
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    new_rate = int(rate * 1.08)
    engine.setProperty('rate', new_rate)
    print(f"  Speech rate: {rate} -> {new_rate} WPM")
    
    engine.save_to_file(script, 'temp_audio.wav')
    engine.runAndWait()
    time.sleep(1)
    
    audio_clip = AudioFileClip("temp_audio.wav")
    print(f"  Audio duration: {audio_clip.duration:.1f}s ({audio_clip.duration/60:.1f} min)")
    return audio_clip

def generate_synced_html(total_duration):
    print(f"Step 2: Generating synced HTML (total duration: {total_duration:.1f}s)...")
    subprocess.run(
        [sys.executable, "generate_hyperframe.py", str(total_duration)],
        check=True
    )

def record_html(duration):
    print(f"Step 3: Recording via Playwright for {duration:.0f}s...")
    os.makedirs("videos", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
            record_video_dir="videos/",
            record_video_size={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        file_url = f"file:///{os.path.abspath('index.html').replace(chr(92), '/')}"
        page.goto(file_url)
        page.wait_for_timeout(int(duration * 1000) + 2000)
        video_path = page.video.path()
        context.close()
        browser.close()
        return video_path

def main():
    audio_clip = generate_voiceover()
    generate_synced_html(audio_clip.duration)
    raw_video_path = record_html(audio_clip.duration)
    
    print("Step 4: Muxing video and audio...")
    video_clip = VideoFileClip(raw_video_path)
    video_clip = video_clip.subclip(0, audio_clip.duration)
    final_video = video_clip.set_audio(audio_clip)
    
    output_filename = "hyperframes_synced_final.mp4"
    final_video.write_videofile(output_filename, fps=30, codec="libx264", audio_codec="aac")
    print(f"\nDone! {output_filename}")

if __name__ == "__main__":
    main()
