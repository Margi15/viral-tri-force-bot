#!/usr/bin/env python3
"""Analiza videos con Claude para extraer la formula viral."""
import os
import anthropic

def analyze_video(video):
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""Analiza este video viral de historia y extrae su formula de exito.

Titulo: {video['title']}
Descripcion: {video['description']}
Vistas: {video['view_count']:,}
URL: {video['url']}

Responde en JSON con exactamente estos campos:
{{
  "tema_principal": "el tema historico central en 10 palabras max",
  "gancho_viral": "que hace que este tema sea irresistible",
  "elemento_sorpresa": "el dato o revelacion que mas impacto genera",
  "emocion_dominante": "una palabra: curiosidad/asombro/indignacion/orgullo",
  "publico_objetivo": "descripcion del publico ideal",
  "angulo_unico": "el angulo que lo diferencia de otros videos similares"
}}

Solo responde con el JSON, sin texto adicional."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )

    import json
    try:
        analysis = json.loads(message.content[0].text)
    except:
        analysis = {
            "tema_principal": video['title'][:50],
            "gancho_viral": "Historia fascinante",
            "elemento_sorpresa": "Datos historicos reveladores",
            "emocion_dominante": "curiosidad",
            "publico_objetivo": "Amantes de la historia",
            "angulo_unico": "Perspectiva unica",
        }

    print(f"  Tema: {analysis.get('tema_principal', 'N/A')}")
    print(f"  Emocion: {analysis.get('emocion_dominante', 'N/A')}")
    return analysis
