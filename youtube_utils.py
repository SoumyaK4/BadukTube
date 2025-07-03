import re
import requests
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

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

                # Get duration and upload date from video details
                duration_seconds = 0
                upload_date = None
                
                if video_id in video_details:
                    duration_str = video_details[video_id].get('duration', 'PT0S')
                    duration_seconds = parse_duration(duration_str)
                    
                    # Use actual upload date instead of playlist addition date if available
                    if upload_date_str := video_details[video_id].get('upload_date'):
                        upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00'))
                
                # If no upload date was found in video details, fall back to playlist date
                if not upload_date:
                    upload_date = datetime.fromisoformat(snippet['publishedAt'].replace('Z', '+00:00'))
                    
                video = {
                    'title': snippet['title'],
                    'video_id': video_id,
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'published_at': upload_date,
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
    """Get detailed information about videos including duration and upload date."""
    if not video_ids:
        return {}

    # Join video IDs for batch request (max 50 IDs)
    ids_str = ','.join(video_ids[:50])

    try:
        # Include snippet part to get upload date, along with contentDetails for duration
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails,snippet&id={ids_str}&key={api_key}"
        response = requests.get(url)
        data = response.json()

        # Create mapping of video ID to details
        result = {}
        if 'items' in data:
            for item in data['items']:
                video_id = item['id']
                content_details = item['contentDetails']
                snippet = item.get('snippet', {})
                
                result[video_id] = {
                    'duration': content_details.get('duration', 'PT0S'),
                    'upload_date': snippet.get('publishedAt')
                }

        return result
    except Exception as e:
        logging.error(f"Error fetching video details: {e}")
        return {}

def get_youtube_video_info(youtube_url, api_key=None):
    """
    Extract info from a YouTube URL for a single video.
    If api_key is provided, will fetch video details from the YouTube API.
    """
    video_id = extract_youtube_id(youtube_url)
    if not video_id:
        raise ValueError("Invalid YouTube URL")

    # If API key is provided, fetch details from the API
    if api_key:
        try:
            video_details = get_video_details(api_key, [video_id])
            
            if video_id in video_details and video_details[video_id].get('upload_date'):
                # Parse the ISO date format
                upload_date = datetime.fromisoformat(video_details[video_id]['upload_date'].replace('Z', '+00:00'))
                
                # Get the duration
                duration_str = video_details[video_id].get('duration', 'PT0S')
                duration_seconds = parse_duration(duration_str)
                
                return {
                    'youtube_id': video_id,
                    'thumbnail_url': f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
                    'publish_date': upload_date,
                    'duration_seconds': duration_seconds
                }
        except Exception as e:
            logging.error(f"Error fetching video info from API: {e}")
            # Fall back to basic info if API call fails
    
    # Return basic info if no API key is provided or API call failed
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
