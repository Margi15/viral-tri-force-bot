#!/usr/bin/env python3
"""Crea contenido para YouTube Shorts, Facebook e Instagram."""
import os
import anthropic

def create_content(video, analysis):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    tema = analysis.get("tema_principal", video["title"])
    gancho = analysis.get("gancho_viral", "")
    sorpresa = analysis.get("elemento_sorpresa", "")
    emocion = analysis.get("emocion_dominante", "curiosidad")

    prompt = f"""Crea contenido viral de historia en espanol para redes sociales.

Tema: {tema}
Gancho viral: {gancho}
Dato sorpresa: {sorpresa}
Emocion: {emocion}

Genera:
1. SCRIPT_SHORTS: Guion para YouTube Short de 45 segundos (maximo 120 palabras).
   Comienza con una pregunta o dato impactante. Termina con "Sigueme para mas historia".

2. FACEBOOK_POST: Post de Facebook de 150-200 palabras con emojis, el dato sorpresa
   y llamada a la accion "Comenta SI si quieres saber mas".

3. INSTAGRAM_CAPTION: Caption de Instagram de 80-100 palabras con hashtags relevantes
   al final (#historia #historiaviral #cultura).

Responde EXACTAMENTE en este formato:
---SCRIPT_SHORTS---
[guion aqui]
---FACEBOOK_POST---
[post aqui]
---INSTAGRAM_CAPTION---
[caption aqui]"""

    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    text = message.content[0].text
    parts = {}

    sections = text.split("---")
    for i, section in enumerate(sections):
        section = section.strip()
        if section == "SCRIPT_SHORTS" and i+1 < len(sections):
            parts["script"] = sections[i+1].strip()
        elif section == "FACEBOOK_POST" and i+1 < len(sections):
            parts["facebook_post"] = sections[i+1].strip()
        elif section == "INSTAGRAM_CAPTION" and i+1 < len(sections):
            parts["instagram_caption"] = sections[i+1].strip()

    # Fallbacks
    if not parts.get("script"):
        parts["script"] = f"Sabias que {tema}? {sorpresa}. Sigueme para mas historia."
    if not parts.get("facebook_post"):
        parts["facebook_post"] = f"{tema}\n\n{sorpresa}\n\nComenta SI si quieres saber mas!"
    if not parts.get("instagram_caption"):
        parts["instagram_caption"] = f"{tema} {sorpresa} #historia #historiaviral #cultura"

    parts["title"] = tema
    parts["video_source"] = video

    print(f"  Script: {len(parts['script'].split())} palabras")
    return parts
