#!/usr/bin/env python3
"""Genera video MP4 con voz Edge TTS y imagen de fondo."""
import os
import asyncio
import tempfile
from pathlib import Path

async def _generate_audio(script, output_path):
    import edge_tts
    voice = "es-MX-DaliaNeural"
    communicate = edge_tts.Communicate(script, voice)
    await communicate.save(output_path)

def generate_video(content):
    script = content.get("script", "Historia fascinante.")
    title = content.get("title", "Historia")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Generate audio
        audio_path = str(tmpdir / "audio.mp3")
        print("  Generando voz (Edge TTS)...")
        asyncio.run(_generate_audio(script, audio_path))

        # Create background image
        img_path = str(tmpdir / "bg.jpg")
        _create_background(title, img_path)

        # Create video
        output_path = "/tmp/viral_short.mp4"
        print("  Ensamblando video...")
        _create_video(audio_path, img_path, output_path)

        print(f"  Video generado: {output_path}")
        return output_path

def _create_background(title, output_path):
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    # Create dark background with gradient
    img = Image.new("RGB", (1080, 1920), color=(20, 20, 40))
    draw = ImageDraw.Draw(img)

    # Add gradient effect
    for i in range(1920):
        alpha = int(255 * (1 - i/1920) * 0.3)
        draw.line([(0, i), (1080, i)], fill=(60, 20, 100))

    # Add title text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 50)
    except:
        font = ImageFont.load_default()
        small_font = font

    # Wrap text
    wrapped = textwrap.fill(title.upper(), width=20)
    lines = wrapped.split("\n")

    y = 800
    for line in lines:
        try:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
        except:
            text_width = len(line) * 40
        x = (1080 - text_width) // 2

        # Shadow
        draw.text((x+4, y+4), line, font=font, fill=(0, 0, 0))
        # Text
        draw.text((x, y), line, font=font, fill=(255, 220, 100))
        y += 100

    # Add decorative line
    draw.rectangle([(100, 780), (980, 790)], fill=(255, 220, 100))
    draw.rectangle([(100, y+20), (980, y+30)], fill=(255, 220, 100))

    img.save(output_path, "JPEG", quality=95)

def _create_video(audio_path, img_path, output_path):
    try:
        from moviepy.editor import ImageClip, AudioFileClip, CompositeVideoClip

        audio = AudioFileClip(audio_path)
        duration = min(audio.duration, 58)  # Max 58s for Shorts

        img_clip = ImageClip(img_path, duration=duration)
        img_clip = img_clip.set_audio(audio.subclip(0, duration))

        img_clip.write_videofile(
            output_path,
            fps=24,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            verbose=False,
            logger=None,
        )
    except Exception as e:
        print(f"  Advertencia moviepy: {e}")
        # Fallback: just copy audio as placeholder
        import shutil
        shutil.copy(audio_path, output_path.replace(".mp4", "_audio.mp3"))
        # Create minimal video with ffmpeg if available
        try:
            import subprocess
            cmd = [
                "ffmpeg", "-y", "-loop", "1",
                "-i", img_path,
                "-i", audio_path,
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "128k",
                "-pix_fmt", "yuv420p",
                "-shortest",
                output_path
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
        except Exception as e2:
            print(f"  ffmpeg fallback: {e2}")
