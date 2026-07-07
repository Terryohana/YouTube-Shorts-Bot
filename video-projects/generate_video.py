import sys
import os
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, vfx
from PIL import Image, ImageDraw, ImageFont

def create_video(image_path, script_text, output_path):
    # 1. Add "Subscribe" text to the image using Pillow
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    width, height = img.size
    
    # Try to load a generic font, or use default
    try:
        font = ImageFont.truetype("arial.ttf", size=int(height/15))
    except IOError:
        font = ImageFont.load_default()
        
    text = "Don't forget to Subscribe!"
    # Basic text positioning at the bottom center
    try:
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
    except AttributeError:
        # Fallback for older Pillow versions
        text_width, text_height = draw.textsize(text, font=font)

    x = (width - text_width) / 2
    y = height - text_height - 50
    
    # Draw black outline
    outline_range = 2
    for offset_x in range(-outline_range, outline_range+1):
        for offset_y in range(-outline_range, outline_range+1):
            draw.text((x+offset_x, y+offset_y), text, font=font, fill="black")
    # Draw white text
    draw.text((x, y), text, font=font, fill="white")
    
    temp_img_path = "temp_slide.jpg"
    img.save(temp_img_path)

    # 2. Generate Audio using gTTS
    temp_audio_path = "temp_audio.mp3"
    tts = gTTS(text=script_text, lang='en', slow=False)
    tts.save(temp_audio_path)

    # 3. Create Video using MoviePy
    audio_clip = AudioFileClip(temp_audio_path).fx(vfx.speedx, 1.35)
    # Give it an extra 1 second of buffer
    duration = audio_clip.duration + 1.0
    
    image_clip = ImageClip(temp_img_path).set_duration(duration)
    video_clip = image_clip.set_audio(audio_clip)
    
    video_clip.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

    # Cleanup temp files
    audio_clip.close()
    video_clip.close()
    if os.path.exists(temp_img_path): os.remove(temp_img_path)
    if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
    
if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python generate_video.py <image_path> <output_mp4> <script_text>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    output_mp4 = sys.argv[2]
    script_text = sys.argv[3]
    
    create_video(image_path, script_text, output_mp4)
