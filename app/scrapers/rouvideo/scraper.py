from __future__ import annotations
import base64
import json
import re
from typing import Any, Optional
from urllib.parse import urlparse, urljoin

from app.core.pool import fetch_html, fetch_json

def can_handle(host: str) -> bool:
    return "rou.video" in host.lower()

def _decrypt_ev(d: str, k: int) -> dict[str, Any]:
    """Decrypt the 'ev' field from rou.video Next.js data"""
    try:
        raw = base64.b64decode(d)
        decrypted_str = "".join([chr(b - k) for b in raw])
        return json.loads(decrypted_str)
    except Exception as e:
        print(f"Error decrypting rou.video ev data: {e}")
        return {}

def _extract_next_data(html: str) -> dict[str, Any]:
    """Extract __NEXT_DATA__ JSON from HTML"""
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except Exception as e:
            print(f"Error parsing __NEXT_DATA__: {e}")
    return {}

async def _get_build_id() -> str:
    """Fetch the homepage and extract the Next.js build ID"""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}
    for url in ["https://rou.video/home", "https://rou.video/", "https://rou.video/v"]:
        try:
            html = await fetch_html(url, headers=headers)
            data = _extract_next_data(html)
            bid = data.get("buildId")
            if bid:
                return bid
        except Exception:
            continue
    return "Rljy_YIzgVHS1mC9i8aEE" # Fallback to a known build ID

async def scrape(url: str) -> dict[str, Any]:
    parsed = urlparse(url)
    video_id = parsed.path.split("/")[-1]
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    # To get the buildId, we first fetch the page HTML
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://rou.video/"
    }
    
    html = await fetch_html(url, headers=headers)
    data = _extract_next_data(html)
    
    video_info = data.get("props", {}).get("pageProps", {}).get("video", {})
    if not video_info:
        # Try fetching the Next.js JSON directly if buildId is found
        build_id = data.get("buildId")
        if build_id:
            json_url = f"https://rou.video/_next/data/{build_id}/v/{video_id}.json"
            json_data = await fetch_json(json_url, headers=headers)
            video_info = json_data.get("pageProps", {}).get("video", {})
            ev_data = json_data.get("pageProps", {}).get("ev", {})
        else:
            raise ValueError(f"No video information found for ID: {video_id}")
    else:
        ev_data = data.get("props", {}).get("pageProps", {}).get("ev", {})

    # Metadata
    title = video_info.get("name") or video_info.get("nameZh")
    description = video_info.get("description")
    thumbnail = video_info.get("coverImageUrl")
    views = str(video_info.get("viewCount", "0"))
    upload_date = video_info.get("createdAt")
    duration = video_info.get("duration")
    
    tags = video_info.get("tags") or video_info.get("tagsZh") or []
    uploader = video_info.get("publisher", {}).get("name") if video_info.get("publisher") else "Unknown"

    # Streams
    streams = []
    default_url = None
    
    if ev_data:
        decrypted = _decrypt_ev(ev_data.get("d", ""), ev_data.get("k", 0))
        video_url = decrypted.get("videoUrl")
        if video_url:
            streams.append({
                "quality": "Auto",
                "url": video_url,
                "format": "hls",
                "server": "Primary"
            })
            default_url = video_url

    video_data = {
        "streams": streams,
        "default": default_url,
        "has_video": len(streams) > 0
    }

    # Related videos
    related_items = data.get("props", {}).get("pageProps", {}).get("relatedVideos", [])
    related_videos = []
    for item in related_items:
        r_id = item.get("id")
        if not r_id: continue
        related_videos.append({
            "url": f"https://rou.video/v/{r_id}",
            "title": item.get("name") or item.get("nameZh"),
            "thumbnail_url": item.get("coverImageUrl"),
            "duration": item.get("duration"),
            "views": str(item.get("viewCount", "0")),
            "upload_date": item.get("createdAt")
        })

    return {
        "url": url,
        "title": title,
        "description": description,
        "thumbnail_url": thumbnail,
        "duration": duration,
        "views": views,
        "upload_date": upload_date,
        "uploader_name": uploader,
        "category": None,
        "tags": tags,
        "video": video_data,
        "related_videos": related_videos
    }

async def list_videos(base_url: str, page: int = 1, limit: int = 100) -> list[dict[str, object]]:
    """List videos from rou.video using Next.js data API"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://rou.video/"
    }
    
    build_id = await _get_build_id()
    if not build_id:
        return []

    # Construct the Next.js data URL
    # Example: https://rou.video/_next/data/[buildId]/v.json?order=viewCount&page=1
    parsed_base = urlparse(base_url)
    path = parsed_base.path
    if not path or path == "/":
        path = "/v" # Default to all videos
    
    # Next.js data URLs for routes like /t/XXX or /v
    data_path = path if path.endswith(".json") else f"{path}.json"
    api_url = f"https://rou.video/_next/data/{build_id}{data_path}"
    
    # Merge existing query params and add page
    query_params = dict(p.split("=") for p in parsed_base.query.split("&") if "=" in p)
    query_params["page"] = str(page)
    
    # Build query string
    query_str = "&".join([f"{k}={v}" for k, v in query_params.items()])
    if query_str:
        api_url += f"?{query_str}"

    try:
        json_data = await fetch_json(api_url, headers=headers)
        prop_data = json_data.get("pageProps", {})
        videos = prop_data.get("videos")
        
        if not videos:
            # Check tag-based videos (category pages)
            videos = prop_data.get("tag", {}).get("videos")
            
        if not videos:
            # Check for home page specific lists
            # latestVideos is usually the most relevant for a general list
            home_keys = ["latestVideos", "dailyHotCNAV", "hotCNAV", "dailyHotSelfie", "hotSelfie", "dailyHot91", "hot91"]
            for key in home_keys:
                videos = prop_data.get(key)
                if videos:
                    break
        
        if not videos:
            videos = []
            
        items = []
        for v in videos:
            v_id = v.get("id")
            if not v_id: continue
            items.append({
                "url": f"https://rou.video/v/{v_id}",
                "title": v.get("name") or v.get("nameZh"),
                "thumbnail_url": v.get("coverImageUrl"),
                "duration": v.get("duration"),
                "views": str(v.get("viewCount", "0")),
                "upload_date": v.get("createdAt"),
                "uploader_name": v.get("publisher", {}).get("name") if v.get("publisher") else None
            })
        return items
    except Exception as e:
        print(f"Error listing rou.video videos: {e}")
        return []

def get_categories() -> list[dict[str, object]]:
    """Load categories from categories.json"""
    import os
    try:
        path = os.path.join(os.path.dirname(__file__), 'categories.json')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading rou.video categories: {e}")
    return []
