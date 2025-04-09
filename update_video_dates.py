#!/usr/bin/env python3
"""
Script to update video publish dates in the database
using the YouTube API to get actual upload dates
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Add the current directory to the path so we can import the app modules
sys.path.append('.')

# Import app modules
from app import app, db
from models import Lecture
from youtube_utils import get_video_details, parse_duration

def update_video_dates(api_key, dry_run=False):
    """
    Update the publish_date field for all videos in the database
    using the YouTube API to get the actual upload date.
    
    Args:
        api_key (str): YouTube API key
        dry_run (bool): If True, don't actually update the database
    """
    # Use app context for database operations
    with app.app_context():
        # Get all lectures
        lectures = Lecture.query.all()
        
        if not lectures:
            logging.info("No lectures found in the database.")
            return
        
        logging.info(f"Found {len(lectures)} lectures in the database.")
        
        # Process videos in batches of 50 (YouTube API limit)
        video_batches = []
        current_batch = []
        
        for lecture in lectures:
            current_batch.append(lecture)
            if len(current_batch) == 50:
                video_batches.append(current_batch)
                current_batch = []
        
        # Add any remaining videos
        if current_batch:
            video_batches.append(current_batch)
        
        total_updated = 0
        
        # Process each batch
        for batch_idx, batch in enumerate(video_batches):
            logging.info(f"Processing batch {batch_idx + 1}/{len(video_batches)} ({len(batch)} videos)")
            
            # Get list of video IDs
            video_ids = [lecture.youtube_id for lecture in batch]
            
            # Get video details from YouTube API
            video_details = get_video_details(api_key, video_ids)
            
            # Update each lecture in the batch
            batch_updated = 0
            for lecture in batch:
                if lecture.youtube_id in video_details and video_details[lecture.youtube_id].get('upload_date'):
                    # Get the upload date from the API response
                    upload_date_str = video_details[lecture.youtube_id]['upload_date']
                    upload_date = datetime.fromisoformat(upload_date_str.replace('Z', '+00:00'))
                    
                    # Get the duration if available
                    if 'duration' in video_details[lecture.youtube_id]:
                        duration_str = video_details[lecture.youtube_id]['duration']
                        duration_seconds = parse_duration(duration_str)
                    else:
                        duration_seconds = None
                    
                    # Log the changes
                    if lecture.publish_date != upload_date:
                        logging.info(f"Video {lecture.youtube_id} ({lecture.title}):")
                        logging.info(f"  Current date: {lecture.publish_date}")
                        logging.info(f"  Updated date: {upload_date}")
                        
                        # Update the lecture
                        if not dry_run:
                            lecture.publish_date = upload_date
                            if duration_seconds and not lecture.duration_seconds:
                                lecture.duration_seconds = duration_seconds
                                logging.info(f"  Updated duration to {duration_seconds} seconds")
                        
                        batch_updated += 1
                else:
                    logging.warning(f"Could not get details for video {lecture.youtube_id} ({lecture.title})")
            
            # Commit changes for this batch
            if not dry_run and batch_updated > 0:
                db.session.commit()
                logging.info(f"Committed {batch_updated} updates for batch {batch_idx + 1}")
            
            total_updated += batch_updated
        
        if dry_run:
            logging.info(f"Dry run complete. {total_updated} videos would be updated.")
        else:
            logging.info(f"Update complete. {total_updated} videos were updated.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update video publish dates using YouTube API")
    parser.add_argument("--api-key", required=True, help="YouTube API key")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually update the database")
    
    args = parser.parse_args()
    
    update_video_dates(args.api_key, args.dry_run)