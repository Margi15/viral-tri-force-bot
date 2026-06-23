#!/usr/bin/env python3
"""Busca imagenes y contenido historico en Wikipedia para enriquecer los videos."""
import urllib.request
import urllib.parse
import json


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
        req = urllib.request.urlopen(search_url, timeout=10)
        data = json.loads(req.read())
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
            req2 = urllib.request.urlopen(summary_url, timeout=10)
            summary = json.loads(req2.read())

            # Preferir imagen original de alta resolucion
            image_url = (
                summary.get("originalimage", {}).get("source")
                or summary.get("thumbnail", {}).get("source")
            )
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
        # Wikipedia requiere User-Agent
        req = urllib.request.Request(
            image_url,
            headers={"User-Agent": "BitacoraDelTiempoBot/1.0 (educational)"},
        )
        resp = urllib.request.urlopen(req, timeout=15)
        data = resp.read()
        img = Image.open(io.BytesIO(data))
        # Asegurarse de que es una imagen real (no un SVG o placeholder)
        if img.size[0] < 100 or img.size[1] < 100:
            return None
        print(f"  Imagen Wikipedia: {img.size[0]}x{img.size[1]} ({img.mode})")
        return img.convert("RGB")
    except Exception as e:
        print(f"  Imagen Wikipedia fallida: {e}")
        return None
