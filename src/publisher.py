#!/usr/bin/env python3
"""Publica en YouTube Shorts y Facebook con video."""
import os
import json
import requests
from datetime import datetime

def get_youtube_service():
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GRequest

    token_json = os.environ.get('YOUTUBE_CLIENT_SECRET')
    if not token_json:
        print("  YOUTUBE_CLIENT_SECRET no configurado - saltando YouTube")
        return None

    try:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        if creds.expired and creds.refresh_token:
            creds.refresh(GRequest())
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"  Error autenticando YouTube: {e}")
        return None

def upload_to_youtube_shorts(video_path, title, description, tags=None):
    from googleapiclient.http import MediaFileUpload

    print("  Subiendo a YouTube Shorts...")
    youtube = get_youtube_service()
    if not youtube:
        return {"success": False, "error": "No YouTube credentials"}

    if not os.path.exists(video_path):
        return {"success": False, "error": f"Video no encontrado: {video_path}"}

    try:
        body = {
            'snippet': {
                'title': title[:100],
                'description': description,
                'tags': tags or ['historia', 'viral', 'shorts'],
                'categoryId': '27'
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
                'embeddable': True,
                'publicStatsViewable': True,
            }
        }

        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
        req = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

        response = None
        while response is None:
            status, response = req.next_chunk()
            if status:
                print(f"    Subiendo: {int(status.progress() * 100)}%")

        video_id = response['id']
        url = f"https://www.youtube.com/shorts/{video_id}"
        print(f"    YouTube OK: {url}")
        return {"success": True, "video_id": video_id, "url": url}

    except Exception as e:
        print(f"    YouTube ERROR: {e}")
        return {"success": False, "error": str(e)}

def publish_to_facebook(video_path, caption):
    print("  Publicando en Facebook...")
    page_token = os.environ.get('FACEBOOK_PAGE_TOKEN')
    page_id = os.environ.get('FACEBOOK_PAGE_ID', '122166413522685195')

    if not page_token:
        return {"success": False, "error": "FACEBOOK_PAGE_TOKEN no configurado"}

    # If video exists, upload as video post
    if video_path and os.path.exists(video_path):
        try:
            url = f"https://graph.facebook.com/v18.0/{page_id}/videos"
            with open(video_path, 'rb') as vf:
                resp = requests.post(url, files={'source': vf}, data={
                    'description': caption,
                    'published': 'true',
                    'access_token': page_token,
                })
            data = resp.json()
            if 'id' in data:
                print(f"    Facebook video OK: {data['id']}")
                return {"success": True, "post_id": data['id']}
            else:
                error = data.get('error', {}).get('message', str(data))
                print(f"    Facebook video ERROR: {error} - cayendo a post de texto")
        except Exception as e:
            print(f"    Facebook video excepcion: {e} - cayendo a post de texto")

    # Fallback: text post
    try:
        url = f"https://graph.facebook.com/v18.0/{page_id}/feed"
        resp = requests.post(url, data={'message': caption, 'access_token': page_token})
        data = resp.json()
        if 'id' in data:
            print(f"    Facebook texto OK: {data['id']}")
            return {"success": True, "post_id": data['id']}
        else:
            error = data.get('error', {}).get('message', str(data))
            print(f"    Facebook ERROR: {error}")
            return {"success": False, "error": error}
    except Exception as e:
        return {"success": False, "error": str(e)}

def publish_instagram(caption):
    print("  Publicando en Instagram...")
    page_token = os.environ.get('FACEBOOK_PAGE_TOKEN')
    page_id = os.environ.get('FACEBOOK_PAGE_ID', '122166413522685195')
    if not page_token:
        return {"success": False, "error": "No token"}

    try:
        r = requests.get(f"https://graph.facebook.com/v18.0/{page_id}", params={
            "fields": "instagram_business_account", "access_token": page_token
        })
        ig_id = r.json().get("instagram_business_account", {}).get("id")
        if not ig_id:
            return {"success": False, "error": "No Instagram Business Account vinculado"}

        PLACEHOLDER = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Blast_off_at_Maui.jpg/320px-Blast_off_at_Maui.jpg"
        r2 = requests.post(f"https://graph.facebook.com/v18.0/{ig_id}/media", data={
            "image_url": PLACEHOLDER, "caption": caption, "access_token": page_token
        })
        if "id" not in r2.json():
            return {"success": False, "error": r2.json().get("error", {}).get("message", str(r2.json()))}

        r3 = requests.post(f"https://graph.facebook.com/v18.0/{ig_id}/media_publish", data={
            "creation_id": r2.json()["id"], "access_token": page_token
        })
        data = r3.json()
        if "id" in data:
            print(f"    Instagram OK: {data['id']}")
            return {"success": True, "media_id": data["id"]}
        else:
            error = data.get("error", {}).get("message", str(data))
            print(f"    Instagram ERROR: {error}")
            return {"success": False, "error": error}
    except Exception as e:
        return {"success": False, "error": str(e)}

def publish_all(content, video_path=None):
    title = content.get("title", "Historia Viral")
    fb_post = content.get("facebook_post", "")
    ig_caption = content.get("instagram_caption", "")

    yt_title = f"🤯 {title[:80]}"
    yt_desc = f"{title}\n\n#Historia #Curiosidades #Shorts #Viral"

    results = {}

    # YouTube Shorts (if video exists and credentials set)
    if video_path and os.path.exists(video_path):
        results["youtube"] = upload_to_youtube_shorts(video_path, yt_title, yt_desc)
    else:
        results["youtube"] = {"success": False, "error": "Sin video MP4"}

    # Facebook (with video if available)
    results["facebook"] = publish_to_facebook(video_path, fb_post)

    # Instagram
    results["instagram"] = publish_instagram(ig_caption)

    # Save output
    os.makedirs("output", exist_ok=True)
    with open("output/publish_log.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "results": results,
            "content": {k: v for k, v in content.items() if k != "video_source"}
        }, f, indent=2, ensure_ascii=False)

    return results

if __name__ == "__main__":
    publish_all({}, None)
