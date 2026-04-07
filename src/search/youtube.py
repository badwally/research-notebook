"""YouTube Data API v3 client for the research pipeline."""


def normalize_video(search_item: dict, details: dict, captions_available: bool) -> dict:
    """Flatten YouTube API response into our standard video metadata format.

    Args:
        search_item: Item from YouTube search.list response.
        details: Item from YouTube videos.list response (contentDetails + statistics).
        captions_available: Whether captions exist for this video.

    Returns:
        Normalized video metadata dict matching the pipeline schema.
    """
    snippet = search_item["snippet"]
    video_id = search_item["id"]["videoId"]
    description = snippet["description"][:500]
    view_count = int(details.get("statistics", {}).get("viewCount", 0))

    return {
        "video_id": video_id,
        "url": f"https://youtube.com/watch?v={video_id}",
        "title": snippet["title"],
        "channel_name": snippet["channelTitle"],
        "channel_id": snippet["channelId"],
        "publish_date": snippet["publishedAt"],
        "duration": details["contentDetails"]["duration"],
        "view_count": view_count,
        "description": description,
        "has_captions": captions_available,
    }
