#!/usr/bin/env python3
"""Busca imagenes y contenido historico en Wikipedia para enriquecer los videos."""
import urllib.request
import urllib.parse
import json

# User-Agent requerido por Wikipedia — sin esto devuelve 403 en servidores
HEADERS = {
    "User-Agent": "ViralTriForceBot/1.0 (https://github.com/Margi15/viral-tri-force-bot) python-urllib/3.10"
}

# Limite de pixeles para evitar decompression bomb en PIL (50 megapixeles)
MAX_PIXELS = 50_000_000


def search_wikipedia(topic, lang="es"):
    """
    Busca en Wikipedia el tema historico, retorna imagen y extracto.

    Returns dict con:
      - title: titulo del articulo encontrado
      - extract: resumen del articulo (primeros 600 chars)
      - image_url: URL de la imagen principal del articulo
      - page_url: URL de la pagina de Wikipedia
    """
    if not topic:
        return None

    # 1. Buscar el articulo mas relevante
    query = urllib.parse.quote(topic[:100])
    search_url = (
        f"https://{lang}.wikipedia.org/w/api.php"
        f"?action=query&list=search&srsearch={query}"
        f"&format=json&srlimit=3&srprop=snippet"
    )

    try:
        req = urllib.request.Request(search_url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        results = data.get("query", {}).get("search", [])
    except Exception as e:
        print(f"  Wikipedia busqueda fallida: {e}")
        return None

    if not results:
        # Intentar en ingles como fallback
        if lang == "es":
            return search_wikipedia(topic, lang="en")
        return None

    # 2. Obtener resumen + imagen del primer resultado
    for result in results:
        page_title = result["title"]
        encoded = urllib.parse.quote(page_title.replace(" ", "_"))
        summary_url = (
            f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded}"
        )

        try:
            req2 = urllib.request.Request(summary_url, headers=HEADERS)
            resp2 = urllib.request.urlopen(req2, timeout=10)
            summary = json.loads(resp2.read())

            # Preferir imagen original, pero solo si no es una bomba de pixeles
            image_url = None
            orig = summary.get("originalimage", {})
            if orig.get("source"):
                w = orig.get("width", 0)
                h = orig.get("height", 0)
                if w * h < MAX_PIXELS:
                    image_url = orig["source"]

            # Fallback a thumbnail si originalimage es demasiado grande
            if not image_url:
                image_url = summary.get("thumbnail", {}).get("source")

            extract = summary.get("extract", "")

            if not extract:
                continue

            print(f"  Wikipedia: '{page_title}' | imagen: {'si' if image_url else 'no'}")
            return {
                "title": summary.get("title", page_title),
                "extract": extract[:600],
                "image_url": image_url,
                "page_url": (
                    summary.get("content_urls", {})
                    .get("desktop", {})
                    .get("page", "")
                ),
                "lang": lang,
            }

        except Exception as e:
            print(f"  Wikipedia summary fallido para '{page_title}': {e}")
            continue

    # Fallback a ingles si no encontro nada en espanol
    if lang == "es":
        return search_wikipedia(topic, lang="en")

    return None


def fetch_wikipedia_image(image_url):
    """Descarga la imagen de Wikipedia y la retorna como PIL Image."""
    if not image_url:
        return None

    import io
    from PIL import Image

    try:
        req = urllib.request.Request(image_url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        img = Image.open(io.BytesIO(data))
        # Verificar tamano minimo y maximo
        if img.size[0] < 100 or img.size[1] < 100:
            return None
        if img.size[0] * img.size[1] >= MAX_PIXELS:
            print(f"  Imagen demasiado grande ({img.size[0]}x{img.size[1]}), omitiendo")
            return None
        print(f"  Imagen Wikipedia: {img.size[0]}x{img.size[1]} ({img.mode})")
        return img.convert("RGB")
    except Exception as e:
        print(f"  Imagen Wikipedia fallida: {e}")
        return None
