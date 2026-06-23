#!/usr/bin/env python3
"""Genera video MP4 con voz Edge TTS e imagen historica real."""
import os
import asyncio
import tempfile
from datetime import datetime
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
    wiki_image_url = content.get("wiki_image_url")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Generate audio
        audio_path = str(tmpdir / "audio.mp3")
        print("Generando voz (Edge TTS)...")
        asyncio.run(_generate_audio(script, audio_path))

        # Create background image
        img_path = str(tmpdir / "bg.jpg")
        _create_background(title, img_path, video_source, wiki_image_url)

        # Create video
        output_path = "/tmp/viral_short.mp4"
        print("Ensamblando video...")
        _create_video(audio_path, img_path, output_path)

        print(f"Video generado: {output_path}")
        return output_path


def extract_keywords(text):
    """Extrae palabras clave del evento historico."""
    stop_words = {
        'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
        'de', 'del', 'al', 'en', 'con', 'por', 'para', 'sobre',
        'que', 'como', 'cuando', 'donde', 'quien', 'cual',
        'y', 'o', 'pero', 'si', 'no', 'tambien', 'ademas',
        'fue', 'es', 'son', 'era', 'fueron', 'ser', 'estar',
        'este', 'esta', 'estos', 'estas', 'ese', 'esa', 'esos', 'esas'
    }
    text = text.lower()
    text = ''.join(c for c in text if c.isalnum() or c.isspace())
    words = text.split()
    keywords = [w for w in words if len(w) > 4 and w not in stop_words]
    seen = set()
    unique_keywords = []
    for word in keywords:
        if word not in seen:
            seen.add(word)
            unique_keywords.append(word)
    return unique_keywords[:5]


def download_historical_images(event_description):
    """Descarga imagenes historicas REALES y relevantes."""
    import urllib.request
    import urllib.parse
    import json
    import io
    from PIL import Image

    os.makedirs('output/images', exist_ok=True)
    keywords = extract_keywords(event_description)
    downloaded_images = []

    # METODO 1: Wikimedia Commons (dominio publico)
    print("Buscando imagenes historicas en Wikimedia Commons...")
    for i, keyword in enumerate(keywords[:3]):
        try:
            query = urllib.parse.quote(keyword)
            search_url = (
                f"https://commons.wikimedia.org/w/api.php?action=query"
                f"&list=search&srsearch={query}&srnamespace=6"
                f"&srprop=size&srwhat=text&format=json&srlimit=5"
            )
            headers = {"User-Agent": "ViralTriForceBot/1.0"}
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            results = data.get('query', {}).get('search', [])
            if not results:
                continue

            image_title = results[0]['title'].replace('File:', '').replace(' ', '_')
            encoded_title = urllib.parse.quote(image_title)
            info_url = (
                f"https://commons.wikimedia.org/w/api.php?action=query"
                f"&titles=File:{encoded_title}&prop=imageinfo&iiprop=url&format=json"
            )
            req2 = urllib.request.Request(info_url, headers=headers)
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                info_data = json.loads(resp2.read())

            pages = info_data.get('query', {}).get('pages', {})
            for page in pages.values():
                if 'imageinfo' in page:
                    image_url = page['imageinfo'][0]['url']
                    req3 = urllib.request.Request(image_url, headers=headers)
                    with urllib.request.urlopen(req3, timeout=15) as resp3:
                        img_data = resp3.read()
                    img = Image.open(io.BytesIO(img_data))
                    if img.size[0] >= 100 and img.size[1] >= 100:
                        img_path = f'output/images/historical_{i}.jpg'
                        img.convert("RGB").save(img_path, "JPEG", quality=90)
                        downloaded_images.append(img_path)
                        print(f"  Imagen Wikimedia: {keyword}")
                    break

        except Exception as e:
            print(f"  Error Wikimedia con '{keyword}': {e}")
            continue

    # METODO 2: Pexels (si hay API key)
    if len(downloaded_images) < 2:
        pexels_api_key = os.environ.get('PEXELS_API_KEY', '')
        if pexels_api_key:
            print("Complementando con Pexels...")
            for keyword in keywords:
                if len(downloaded_images) >= 3:
                    break
                try:
                    query = urllib.parse.quote(keyword)
                    search_url = (
                        f"https://api.pexels.com/v1/search?query={query}"
                        f"&orientation=portrait&per_page=3"
                    )
                    req = urllib.request.Request(
                        search_url,
                        headers={"Authorization": pexels_api_key}
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = json.loads(resp.read())
                    photos = data.get('photos', [])
                    if photos:
                        photo_url = photos[0]['src']['large']
                        req2 = urllib.request.Request(photo_url)
                        with urllib.request.urlopen(req2, timeout=15) as resp2:
                            img_data = resp2.read()
                        img_path = f'output/images/historical_{len(downloaded_images)}.jpg'
                        with open(img_path, 'wb') as f:
                            f.write(img_data)
                        downloaded_images.append(img_path)
                        print(f"  Imagen Pexels: {keyword}")
                except Exception as e:
                    print(f"  Error Pexels: {e}")
                    continue

    # METODO 3: Placeholder elegante si todo falla
    while len(downloaded_images) < 1:
        from PIL import ImageDraw, ImageFont
        img = Image.new('RGB', (1080, 1920), color=(20, 20, 30))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(
                "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 80
            )
        except Exception:
            font = ImageFont.load_default()
        text = f"EVENTO\nHISTORICO\n{datetime.now().strftime('%d/%m/%Y')}"
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except Exception:
            tw, th = 400, 240
        draw.text(((1080 - tw) // 2, (1920 - th) // 2), text, fill=(200, 180, 140), font=font)
        draw.rectangle([50, 50, 1030, 1870], outline=(200, 180, 140), width=10)
        img_path = f'output/images/historical_{len(downloaded_images)}.jpg'
        img.save(img_path)
        downloaded_images.append(img_path)

    print(f"  Total imagenes: {len(downloaded_images)}")
    return downloaded_images


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
            if img.size[0] > 200:
                print(f"  Thumbnail YouTube: {quality} ({img.size[0]}x{img.size[1]})")
                return img
        except Exception as e:
            print(f"  {quality} fallido: {e}")
            continue
    return None


def _fetch_wiki_image(wiki_image_url):
    """Download Wikipedia image."""
    import urllib.request
    import io
    from PIL import Image

    if not wiki_image_url:
        return None
    try:
        req = urllib.request.Request(
            wiki_image_url,
            headers={"User-Agent": "ViralTriForceBot/1.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            img_data = resp.read()
        img = Image.open(io.BytesIO(img_data))
        if img.size[0] >= 100 and img.size[1] >= 100:
            print(f"  Imagen Wikipedia ({img.size[0]}x{img.size[1]})")
            return img
    except Exception as e:
        print(f"  Wikipedia imagen fallida: {e}")
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


def _create_background(title, output_path, video_source=None, wiki_image_url=None):
    from PIL import Image, ImageDraw, ImageFont
    import textwrap

    TARGET_W, TARGET_H = 1080, 1920

    # Prioridad: 1) Wikimedia Commons  2) Wikipedia  3) YouTube  4) Degradado
    bg_img = None

    # 1. Intentar Wikimedia Commons con palabras clave del titulo
    try:
        historical_imgs = download_historical_images(title)
        if historical_imgs:
            from PIL import Image as PILImage
            bg_img = PILImage.open(historical_imgs[0]).convert("RGB")
            print("  Usando imagen historica de Wikimedia Commons")
    except Exception as e:
        print(f"  Wikimedia fallido: {e}")

    # 2. Wikipedia image URL
    if bg_img is None and wiki_image_url:
        bg_img = _fetch_wiki_image(wiki_image_url)

    # 3. YouTube thumbnail
    if bg_img is None:
        video_id = video_source.get("video_id") if isinstance(video_source, dict) else None
        if video_id:
            bg_img = _fetch_youtube_thumbnail(video_id)

    # 4. Cinematic gradient fallback
    if bg_img is None:
        print("  Usando fondo degradado (sin imagen disponible)")
        bg_img = _create_cinematic_gradient(TARGET_W, TARGET_H)

    img = _resize_cover(bg_img, TARGET_W, TARGET_H)

    # Cinematic dark overlay
    img = img.convert("RGBA")
    overlay = Image.new("RGBA", (TARGET_W, TARGET_H), (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    for i in range(350):
        alpha = int(190 * (1 - i / 350))
        draw_ov.line([(0, i), (TARGET_W, i)], fill=(0, 0, 0, alpha))
    for i in range(950):
        y = TARGET_H - 1 - i
        alpha = int(230 * (1 - i / 950) ** 0.6)
        draw_ov.line([(0, y), (TARGET_W, y)], fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img, overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Fonts
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

    # Brand label at top
    brand = "BITACORA DEL TIEMPO"
    try:
        bb = draw.textbbox((0, 0), brand, font=font_brand)
        bw = bb[2] - bb[0]
    except Exception:
        bw = len(brand) * 22
    bx = (TARGET_W - bw) // 2
    draw.text((bx + 2, 72), brand, font=font_brand, fill=(0, 0, 0))
    draw.text((bx, 70), brand, font=font_brand, fill=(255, 215, 0))
    draw.rectangle([(bx, 123), (bx + bw, 127)], fill=(255, 215, 0))

    # Title at bottom
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
        for dx, dy in [(5, 5), (3, 3), (1, 1)]:
            draw.text((x + dx, y + dy), line, font=font_title, fill=(0, 0, 0))
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
