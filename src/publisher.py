#!/usr/bin/env python3
"""Publica contenido en Facebook e Instagram."""
import os
import requests

FACEBOOK_PAGE_ID = os.environ.get("FACEBOOK_PAGE_ID", "122166413522685195")
FB_TOKEN = os.environ.get("FACEBOOK_PAGE_TOKEN")

def publish_all(content, video_path=None):
    results = {}

    # Facebook
    print("  Publicando en Facebook...")
    results["facebook"] = publish_facebook(content.get("facebook_post", ""))

    # Instagram (via Facebook Graph API)
    print("  Publicando en Instagram...")
    results["instagram"] = publish_instagram(content.get("instagram_caption", ""))

    return results

def publish_facebook(message):
    if not FB_TOKEN:
        return {"success": False, "error": "FACEBOOK_PAGE_TOKEN no configurado"}

    try:
        url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}/feed"
        response = requests.post(url, data={
            "message": message,
            "access_token": FB_TOKEN,
        })
        data = response.json()

        if "id" in data:
            print(f"    Facebook OK: post_id={data['id']}")
            return {"success": True, "post_id": data["id"]}
        else:
            error = data.get("error", {}).get("message", str(data))
            print(f"    Facebook ERROR: {error}")
            return {"success": False, "error": error}
    except Exception as e:
        print(f"    Facebook EXCEPCION: {e}")
        return {"success": False, "error": str(e)}

def publish_instagram(caption):
    if not FB_TOKEN:
        return {"success": False, "error": "FACEBOOK_PAGE_TOKEN no configurado"}

    try:
        # Get Instagram Business Account ID
        pages_url = f"https://graph.facebook.com/v18.0/{FACEBOOK_PAGE_ID}"
        pages_resp = requests.get(pages_url, params={
            "fields": "instagram_business_account",
            "access_token": FB_TOKEN,
        })
        pages_data = pages_resp.json()
        ig_id = pages_data.get("instagram_business_account", {}).get("id")

        if not ig_id:
            return {"success": False, "error": "No hay cuenta Instagram Business vinculada"}

        # Create text-only post (image upload requires hosted URL)
        # For now, post as a caption update
        create_url = f"https://graph.facebook.com/v18.0/{ig_id}/media"
        # Use a placeholder image URL for test
        PLACEHOLDER_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Blast_off_at_Maui.jpg/320px-Blast_off_at_Maui.jpg"

        create_resp = requests.post(create_url, data={
            "image_url": PLACEHOLDER_IMAGE,
            "caption": caption,
            "access_token": FB_TOKEN,
        })
        create_data = create_resp.json()

        if "id" not in create_data:
            error = create_data.get("error", {}).get("message", str(create_data))
            print(f"    Instagram ERROR: {error}")
            return {"success": False, "error": error}

        # Publish
        publish_url = f"https://graph.facebook.com/v18.0/{ig_id}/media_publish"
        publish_resp = requests.post(publish_url, data={
            "creation_id": create_data["id"],
            "access_token": FB_TOKEN,
        })
        publish_data = publish_resp.json()

        if "id" in publish_data:
            print(f"    Instagram OK: media_id={publish_data['id']}")
            return {"success": True, "media_id": publish_data["id"]}
        else:
            error = publish_data.get("error", {}).get("message", str(publish_data))
            print(f"    Instagram ERROR: {error}")
            return {"success": False, "error": error}
    except Exception as e:
        print(f"    Instagram EXCEPCION: {e}")
        return {"success": False, "error": str(e)}
