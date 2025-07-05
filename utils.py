import os
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import logging
import isodate

from youtube_utils import get_youtube_video_info as fallback_get_info

def extract_youtube_video_id(url):
    """
    Extract YouTube video ID from various URL formats
    Returns video_id or None if not found
    """
    logging.debug(f'Processing YouTube URL: {url}')
    parsed_url = urlparse(url)
    video_id = None

    try:
        # youtu.be format (short URL)
        if parsed_url.hostname == 'youtu.be':
            video_id = parsed_url.path.lstrip('/').split('?')[0]

        # youtube.com formats
        elif parsed_url.hostname in ['www.youtube.com', 'youtube.com']:
            # Standard watch URL with v parameter
            if 'v' in parse_qs(parsed_url.query):
                video_id = parse_qs(parsed_url.query)['v'][0]
            # Live URL format
            elif 'live' in parsed_url.path:
                parts = parsed_url.path.split('/live/')
                if len(parts) > 1:
                    video_id = parts[1].split('?')[0]
            # Embed URL format
            elif '/embed/' in parsed_url.path:
                video_id = parsed_url.path.split('/embed/')[1].split('?')[0]
            # Shorts URL format
            elif '/shorts/' in parsed_url.path:
                video_id = parsed_url.path.split('/shorts/')[1].split('?')[0]

        if video_id:
            logging.debug(f'Extracted video ID: {video_id}')
            return video_id

        logging.error(f'Unsupported URL format: {url}')
        return None

    except Exception as e:
        logging.error(f'Error parsing YouTube URL: {str(e)}')
        return None

def get_youtube_video_info(url, api_key=None):
    # Extract video ID from URL
    video_id = extract_youtube_video_id(url)
    if not video_id:
        raise ValueError('Invalid YouTube URL')

    # Use provided API key or fall back to environment variable
    youtube_api_key = api_key or os.environ.get('YOUTUBE_API_KEY')
    
    if not youtube_api_key:
        logging.warning('No YouTube API key provided - using fallback method')
        # If no API key is available, use the function from youtube_utils
        return fallback_get_info(url, api_key)
    
    # Get video info using YouTube Data API
    api_url = f'https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={youtube_api_key}&part=snippet,contentDetails,statistics'
    response = requests.get(api_url)

    if response.status_code != 200:
        raise ValueError(f'Error fetching video info: {response.status_code}')

    data = response.json()

    if not data['items']:
        raise ValueError('Video not found')

    video_info = data['items'][0]

    # Parse publish date
    publish_date = datetime.strptime(
        video_info['snippet']['publishedAt'], 
        '%Y-%m-%dT%H:%M:%SZ'
    )

    # Get thumbnail URL (highest quality available)
    thumbnail_url = video_info['snippet']['thumbnails']['high']['url']

    # Parse duration
    duration_seconds = 0
    if 'contentDetails' in video_info and 'duration' in video_info['contentDetails']:
        duration = isodate.parse_duration(video_info['contentDetails']['duration'])
        duration_seconds = int(duration.total_seconds())

    return {
        'youtube_id': video_id,
        'title': video_info['snippet']['title'],
        'publish_date': publish_date,
        'thumbnail_url': thumbnail_url,
        'duration_seconds': duration_seconds
    }
