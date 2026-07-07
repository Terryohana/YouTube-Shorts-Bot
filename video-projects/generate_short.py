import sys
import os
import time
import asyncio
from moviepy.editor import ImageClip, AudioFileClip
from PIL import Image

async def generate_edge_tts(script_text, output_path):
    """Generate natural-sounding TTS using Microsoft Edge neural voices."""
    import edge_tts
    # en-US-GuyNeural = deep, natural male voice (great for tech content)
    voice = "en-US-GuyNeural"
    communicate = edge_tts.Communicate(script_text, voice, rate="+10%")
    await communicate.save(output_path)

def generate_pyttsx3_fallback(script_text, output_path):
    """Fallback to pyttsx3 if edge-tts fails."""
    import pyttsx3
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', int(rate * 1.1))
    engine.save_to_file(script_text, output_path)
    engine.runAndWait()
    time.sleep(0.5)

def create_short(image_path, script_text, output_path):
    """Create a YouTube Short (vertical 1080x1920) from an image and script."""
    
    # 1. Resize image to vertical Shorts format (1080x1920)
    print("  Preparing vertical image for Shorts...")
    img = Image.open(image_path)
    img_resized = img.resize((1080, 1920), Image.LANCZOS)
    temp_img = "temp_short_img.jpg"
    img_resized.save(temp_img, quality=95)
    
    # 2. Generate voiceover — try Edge TTS first, fallback to pyttsx3
    audio_file = "temp_short_audio.mp3"
    try:
        print("  Generating voiceover (Edge Neural TTS)...")
        asyncio.run(generate_edge_tts(script_text, audio_file))
        print("  Edge TTS success!")
    except Exception as e:
        print(f"  Edge TTS failed ({e}), falling back to pyttsx3...")
        audio_file = "temp_short_audio.wav"
        generate_pyttsx3_fallback(script_text, audio_file)
        print("  pyttsx3 fallback success!")
    
    # 3. Create the video
    print("  Rendering video...")
    audio_clip = AudioFileClip(audio_file)
    duration = audio_clip.duration + 0.5
    
    image_clip = ImageClip(temp_img).set_duration(duration)
    video_clip = image_clip.set_audio(audio_clip)
    
    video_clip.write_videofile(
        output_path, 
        fps=30, 
        codec="libx264", 
        audio_codec="aac"
    )
    
    # Cleanup
    audio_clip.close()
    video_clip.close()
    if os.path.exists(temp_img): os.remove(temp_img)
    if os.path.exists(audio_file): os.remove(audio_file)
    
    print(f"  Done! -> {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_short.py <image_path> <output_mp4> <script_text>")
        sys.exit(1)
    create_short(sys.argv[1], sys.argv[3], sys.argv[2])
