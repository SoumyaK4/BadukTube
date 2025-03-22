import re
import requests
from datetime import datetime
import iso8601
import isodate

def extract_playlist_id(playlist_url):
    """Extract the playlist ID from a YouTube playlist URL."""
    playlist_id_regex = r'(?:youtube\.com/playlist\?list=|youtu\.be/playlist\?list=)([^&\s]+)'
    match = re.search(playlist_id_regex, playlist_url)
    if match:
        return match.group(1)
    return None

def extract_youtube_id(youtube_url):
    """Extract the video ID from a YouTube URL."""
    pattern = r'(?:youtube\.com/(?:watch\?v=|embed/|v/)|youtu\.be/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, youtube_url)
    if match:
        return match.group(1)
    return None

def fetch_playlist_videos(api_key, playlist_id):
    """Fetch all videos from a YouTube playlist."""
    videos = []
    next_page_token = None

    try:
        while True:
            # Build URL with pagination token if it exists
            url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet,contentDetails&maxResults=50&playlistId={playlist_id}&key={api_key}"
            if next_page_token:
                url += f"&pageToken={next_page_token}"

            # Make request to get playlist items
            response = requests.get(url)
            data = response.json()

            if 'error' in data:
                return [], data['error'].get('message', 'An error occurred')

            # Get video IDs for content details request
            video_ids = [item['contentDetails']['videoId'] for item in data['items']]

            # Get video details (including duration) in a single request
            video_details = get_video_details(api_key, video_ids)

            # Process each video in the playlist
            for item in data['items']:
                snippet = item['snippet']
                video_id = item['contentDetails']['videoId']

                # Get duration from video details
                duration_seconds = 0
                if video_id in video_details:
                    duration_str = video_details[video_id].get('duration', 'PT0S')
                    duration_seconds = int(isodate.parse_duration(duration_str).total_seconds())

                video = {
                    'title': snippet['title'],
                    'video_id': video_id,
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'published_at': datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00')),
                    'duration_seconds': duration_seconds
                }
                videos.append(video)

            # Check if there are more pages
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break

        return videos, None
    except Exception as e:
        return [], str(e)

def get_video_details(api_key, video_ids):
    """Get detailed information about videos including duration."""
    if not video_ids:
        return {}

    # Join video IDs for batch request (max 50 IDs)
    ids_str = ','.join(video_ids[:50])

    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={ids_str}&key={api_key}"
        response = requests.get(url)
        data = response.json()

        # Create mapping of video ID to duration
        result = {}
        if 'items' in data:
            for item in data['items']:
                video_id = item['id']
                content_details = item['contentDetails']
                result[video_id] = {
                    'duration': content_details.get('duration', 'PT0S')
                }

        return result
    except Exception as e:
        print(f"Error fetching video details: {e}")
        return {}

def get_youtube_video_info(youtube_url):
    """Extract info from a YouTube URL for a single video."""
    video_id = extract_youtube_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    # For now, we're not fetching additional info from the API for individual videos
    # We'll just return the basic info
    return {
        'youtube_id': video_id,
        'thumbnail_url': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        'publish_date': datetime.utcnow()  # Use current date as publish date
    }

def parse_duration(duration_iso):
    """
    Parse ISO 8601 duration format (PT#H#M#S) to seconds
    Example: PT1H30M15S = 1 hour, 30 minutes, 15 seconds = 5415 seconds
    """
    try:
        # Handle special case of zero duration
        if duration_iso == 'PT0S':
            return 0

        duration = duration_iso.replace('PT', '')
        hours = 0
        minutes = 0
        seconds = 0

        # Extract hours
        if 'H' in duration:
            hours_part = duration.split('H')[0]
            hours = int(hours_part)
            duration = duration.split('H')[1]

        # Extract minutes
        if 'M' in duration:
            minutes_part = duration.split('M')[0]
            minutes = int(minutes_part)
            duration = duration.split('M')[1]

        # Extract seconds
        if 'S' in duration:
            seconds_part = duration.split('S')[0]
            seconds = int(seconds_part)

        total_seconds = hours * 3600 + minutes * 60 + seconds
        return total_seconds
    except Exception as e:
        logging.error(f"Error parsing duration '{duration_iso}': {str(e)}")
        return 0


import logging
from utils import extract_youtube_video_id

logging.basicConfig(level=logging.INFO)