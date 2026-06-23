#!/usr/bin/env python3
"""Genera video MP4 con voz Edge TTS e imagen de fondo real del video original."""
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
    video_source = content.get("video_source", {})

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Generate audio
        audio_path = str(tmpdir / "audio.mp3")
        print("Generando voz (Edge TTS)...")
        asyncio.run(_generate_audio(script, audio_path))

        # Create background image using real YouTube thumbnail
        img_path = str(tmpdir / "bg.jpg")
        _create_background(title, img_path, video_source)

        # Create video
        output_path = "/tmp/viral_short.mp4"
        print("Ensamblando video...")
        _create_video(audio_path, img_path, output_path)

        print(f"Video generado: {output_path}")
        return output_path


def _fetch_youtube_thumbnail(video_id):
    """Download the original YouTube video thumbnail as background."""
    import urllib.request
    import io
    from PIL import Image

    if not video_id:
        return None

    for quality in ["maxresdefault", "hqdefault", "sddefault"]:
        url = f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
        try:
            req = urllib.request.urlopen(url, timeout=10)
            img_data = req.read()
            img = Image.open(io.BytesIO(img_data))
            # YouTube returns a 120x90 gray placeholder when maxres doesn't exist
            if img.size[0] > 200:
                print(f"  Thumbnail obtenido: {quality} ({img.size[0]}x{img.size[1]})")
                return img
        except Exception as e:
            print(f"  {quality} fallido: {e}")
            continue

    return None


def _resize_cover(img, target_w, target_h):
    """Resize and center-crop image to exactly target_w x target_h."""
    from PIL import Image

    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)

    left = (new_w - target_w) // 2
    top = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def _create_cinematic_gradient(w, h):
    """Cinematic dark blue-black gradient as fallback background."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (w, h), (10, 10, 30))
    draw = ImageDraw.Draw(img)
    for i in range(h):
        t = i / h
        r = int(10 + 40 * (1 - t))
        g = int(10 + 20 * (1 - t))
        b = int(30 + 80 * (1 - t))
        draw.line([(0, i), (w, i)], fill=(r, g, b))
    return img


def _create_background(title, output_path, video_source=None):
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    TARGET_W, TARGET_H = 1080, 1920

    # 1. Try to get the real YouTube thumbnail
    video_id = video_source.get("video_id") if isinstance(video_source, dict) else None
    bg_img = _fetch_youtube_thumbnail(video_id) if video_id else None

    if bg_img:
        img = _resize_cover(bg_img, TARGET_W, TARGET_H)
        print("  Usando thumbnail real del video original")
    else:
        print("  Usando fondo degradado (sin thumbnail disponible)")
        img = _create_cinematic_gradient(TARGET_W, TARGET_H)

    # 2. Apply cinematic dark overlay
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)

    # Top vignette (darker at top for brand label)
    for i in range(350):
        alpha = int(190 * (1 - i / 350))
        draw_ov.line([(0, i), (TARGET_W, i)], fill=(0, 0, 0, alpha))

    # Bottom heavy gradient for title text
    for i in range(950):
        y = TARGET_H - 1 - i
        alpha = int(230 * (1 - i / 950) ** 0.6)
        draw_ov.line([(0, y), (TARGET_W, y)], fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # 3. Load fonts
    try:
        font_title = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 82
        )
        font_brand = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 44
        )
    except Exception:
        font_title = ImageFont.load_default()
        font_brand = font_title

    # 4. Brand label at top center
    brand = "BITACORA DEL TIEMPO"
    try:
        bb = draw.textbbox((0, 0), brand, font=font_brand)
        bw = bb[2] - bb[0]
    except Exception:
        bw = len(brand) * 22
    bx = (TARGET_W - bw) // 2
    # Shadow then gold text
    draw.text((bx + 2, 72), brand, font=font_brand, fill=(0, 0, 0))
    draw.text((bx, 70), brand, font=font_brand, fill=(255, 215, 0))
    # Gold underline
    draw.rectangle([(bx, 123), (bx + bw, 127)], fill=(255, 215, 0))

    # 5. Title text at bottom third -- white with multi-layer shadow
    wrapped = textwrap.fill(title.upper(), width=17)
    lines = wrapped.split("\n")
    line_h = 108
    total_h = len(lines) * line_h
    y = TARGET_H - total_h - 130

    for line in lines:
        try:
            bb = draw.textbbox((0, 0), line, font=font_title)
            tw = bb[2] - bb[0]
        except Exception:
            tw = len(line) * 42
        x = (TARGET_W - tw) // 2
        # Multi-layer shadow for punch
        for dx, dy in [(5, 5), (3, 3), (1, 1)]:
            draw.text((x + dx, y + dy), line, font=font_title, fill=(0, 0, 0))
        # White text
        draw.text((x, y), line, font=font_title, fill=(255, 255, 255))
        y += line_h

    img.save(output_path, "JPEG", quality=95)


def _create_video(audio_path, img_path, output_path):
    try:
        from moviepy.editor import ImageClip, AudioFileClip

        audio = AudioFileClip(audio_path)
        duration = min(audio.duration, 58)
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
        print(f"Advertencia moviepy: {e}")
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
                output_path,
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
        except Exception as e2:
            print(f"ffmpeg fallback: {e2}")
