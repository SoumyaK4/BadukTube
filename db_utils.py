
"""
Database utility functions to centralize common database operations
"""
from app import db
from models import Topic, Tag, Rank, Lecture, Collection, collection_lecture
import logging

def get_metadata():
    """Get all metadata for forms and filtering"""
    return {
        'topics': Topic.query.all(),
        'tags': Tag.query.all(),
        'ranks': Rank.query.all(),
        'collections': Collection.query.all(),
    }

def get_filtered_lectures_query():
    """Get base query for lectures with eager loading"""
    query = Lecture.query.options(
        db.joinedload(Lecture.topics),
        db.joinedload(Lecture.tags),
        db.joinedload(Lecture.rank),
    ).distinct()
    
    return query

def apply_search_filters(query, search_params):
    """Apply search filters to a lecture query"""
    # Text search
    if search_params.get('q'):
        query = query.filter(Lecture.title.ilike(f'%{search_params["q"]}%'))

    # Topic filtering
    if search_params.get('topics') and any(search_params['topics']):
        valid_topic_ids = [tid for tid in search_params['topics'] if tid]
        if valid_topic_ids:
            query = query.join(Lecture.topics).filter(Topic.id.in_(valid_topic_ids))

    # Tag filtering
    if search_params.get('tags') and any(search_params['tags']):
        valid_tag_ids = [tid for tid in search_params['tags'] if tid]
        if valid_tag_ids:
            query = query.join(Lecture.tags).filter(Tag.id.in_(valid_tag_ids))

    # Rank filtering
    if search_params.get('rank'):
        query = query.filter(Lecture.rank_id == search_params['rank'])
    
    # Always sort by newest
    query = query.order_by(Lecture.publish_date.desc())
    
    return query

def safe_commit():
    """Commit changes with error handling"""
    try:
        db.session.commit()
        return True, None
    except Exception as e:
        db.session.rollback()
        logging.error(f'Database error: {str(e)}')
        return False, str(e)

def get_collection_lectures(collection_id):
    """Get lectures for a collection with proper ordering"""
    query = db.session.query(Lecture).join(
        collection_lecture,
        Lecture.id == collection_lecture.c.lecture_id,
    ).filter(
        collection_lecture.c.collection_id == collection_id,
    )

    # Try to order by position if the column exists
    try:
        return query.order_by(collection_lecture.c.position).all()
    except Exception:
        # Fall back to no ordering if position column doesn't exist
        return query.all()
