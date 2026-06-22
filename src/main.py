#!/usr/bin/env python3
"""Viral Tri-Force Bot - Main orchestrator."""
import sys
import os
import traceback
from scraper import get_viral_videos
from analyzer import analyze_video
from creator import create_content
from video_generator import generate_video
from publisher import publish_all

def main():
    print("\n" + "="*60)
    print("  VIRAL TRI-FORCE BOT")
    print("="*60)

    os.makedirs("output", exist_ok=True)

    # Step 1: Find viral videos
    print("\n[1/5] Buscando videos virales...")
    videos = get_viral_videos()
    if not videos:
        print("No se encontraron videos virales. Saliendo.")
        sys.exit(0)

    video = videos[0]
    print(f"  Video seleccionado: {video['title'][:60]}")

    # Step 2: Analyze
    print("\n[2/5] Analizando formula viral...")
    analysis = analyze_video(video)

    # Step 3: Create content
    print("\n[3/5] Creando contenido...")
    content = create_content(video, analysis)

    # Save content to output/
    with open("output/all_content.txt", "w", encoding="utf-8") as f:
        f.write(f"=== YOUTUBE SHORTS ===\n")
        f.write(f"Titulo: {content.get('title', '')}\n")
        f.write(content.get('script', '') + "\n\n")
        f.write(f"=== FACEBOOK POST ===\n")
        f.write(content.get('facebook_post', '') + "\n\n")
        f.write(f"=== INSTAGRAM CAPTION ===\n")
        f.write(content.get('instagram_caption', '') + "\n")

    # Step 4: Generate video
    print("\n[4/5] Generando video MP4...")
    video_path = generate_video(content)

    # Copy to output folder
    if video_path and os.path.exists(video_path):
        import shutil
        out_path = "output/final_video.mp4"
        shutil.copy(video_path, out_path)
        video_path = out_path

    # Step 5: Publish
    print("\n[5/5] Publicando...")
    results = publish_all(content, video_path)

    print("\n" + "="*60)
    print("  COMPLETADO!")
    for platform, result in results.items():
        status = "OK" if result.get("success") else "FALLO"
        print(f"  {platform}: {status}")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nERROR FATAL: {e}")
        traceback.print_exc()
        sys.exit(1)
