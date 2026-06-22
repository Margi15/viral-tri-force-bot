#!/usr/bin/env python3
"""Busca videos virales de historia en espanol en YouTube."""
import os
from googleapiclient.discovery import build
from datetime import datetime, timedelta

def get_viral_videos(max_results=5):
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        raise ValueError("YOUTUBE_API_KEY no configurada")

    youtube = build("youtube", "v3", developerKey=api_key)

    # Fecha hace 30 dias
    published_after = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    queries = [
        "historia de mexico viral",
        "historia latinoamerica impactante",
        "dato historico sorprendente espanol",
        "historia antigua secretos revelados",
        "civilizaciones antiguas misterios",
    ]

    all_videos = []
    for query in queries[:2]:
        try:
            response = youtube.search().list(
                q=query,
                part="snippet",
                type="video",
                maxResults=10,
                order="viewCount",
                publishedAfter=published_after,
                videoDuration="medium",
                relevanceLanguage="es",
            ).execute()

            for item in response.get("items", []):
                video_id = item["id"]["videoId"]
                title = item["snippet"]["title"]
                desc = item["snippet"]["description"]

                # Get stats
                stats_resp = youtube.videos().list(
                    part="statistics,contentDetails",
                    id=video_id
                ).execute()

                if stats_resp["items"]:
                    stats = stats_resp["items"][0]["statistics"]
                    view_count = int(stats.get("viewCount", 0))
                    if view_count >= 50000:
                        all_videos.append({
                            "video_id": video_id,
                            "title": title,
                            "description": desc[:500],
                            "view_count": view_count,
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                        })
        except Exception as e:
            print(f"  Error en query '{query}': {e}")
            continue

    # Sort by views
    all_videos.sort(key=lambda x: x["view_count"], reverse=True)
    print(f"  Encontrados {len(all_videos)} videos virales")
    return all_videos[:max_results]
