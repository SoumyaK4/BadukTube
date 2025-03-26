from flask import render_template, redirect, url_for, request, jsonify, flash, send_from_directory, session
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
import os
import uuid
import logging
import json
from datetime import datetime
from models import User, Lecture, Topic, Tag, Rank, Collection, collection_lecture
from forms import LoginForm, LectureForm, MetadataForm, CollectionForm
from utils import get_youtube_video_info
from db_utils import (
    get_metadata, get_filtered_lectures_query, apply_search_filters,
    safe_commit, get_collection_lectures
)

# Setup CSRF protection
def generate_csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = str(uuid.uuid4())
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = generate_csrf_token

@app.route('/about')
def about():
    return render_template('about.html')

# Latest route has been removed

@app.route('/')
def search():
    # Get metadata using utility function
    metadata = get_metadata()
    return render_template('search.html', **metadata)

@app.route('/api/search')
def api_search():
    try:
        # Validate and sanitize input parameters
        try:
            page = max(1, request.args.get('page', 1, type=int))
            per_page = min(50, request.args.get('per_page', 9, type=int))  # Default 9 items per page
        except (ValueError, TypeError):
            page = 1
            per_page = 9

        # Collect search parameters
        search_params = {
            'q': request.args.get('q', ''),
            'topics': request.args.getlist('topics[]'),
            'tags': request.args.getlist('tags[]'),
            'rank': request.args.get('rank')
        }

        # Get base query and apply filters
        lectures_query = get_filtered_lectures_query(include_paid=False)
        lectures_query = apply_search_filters(lectures_query, search_params)

        # Add pagination
        pagination = lectures_query.paginate(page=page, per_page=per_page, error_out=False)
        lectures = pagination.items

        # Process results
        lecture_data = []
        for lecture in lectures:
            lecture_data.append({
                'id': lecture.id,
                'title': lecture.title,
                'youtube_id': lecture.youtube_id,
                'thumbnail_url': lecture.thumbnail_url,
                'publish_date': lecture.publish_date.isoformat(),
                'duration_seconds': lecture.duration_seconds,
                'topics': [t.name for t in lecture.topics],
                'tags': [t.name for t in lecture.tags],
                'rank': lecture.rank.name if lecture.rank else None
            })

        return jsonify({
            'lectures': lecture_data,
            'has_next': pagination.has_next,
            'total_pages': pagination.pages,
            'current_page': pagination.page
        })
    except Exception as e:
        logging.error(f"Error in api_search: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('search'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('search'))
        flash('Invalid username or password')
    return render_template('admin/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('search'))

# The add_lecture route has been removed in favor of playlist import

@app.route('/admin/lecture/edit/<int:lecture_id>', methods=['GET', 'POST'])
@login_required
def edit_lecture(lecture_id):
    lecture = Lecture.query.get_or_404(lecture_id)
    form = LectureForm()
    form.topics.choices = [(t.id, t.name) for t in Topic.query.all()]
    form.tags.choices = [(t.id, t.name) for t in Tag.query.all()]
    form.rank.choices = [(r.id, r.name) for r in Rank.query.all()]
    form.collections.choices = [(c.id, c.name) for c in Collection.query.all()]

    if form.validate_on_submit():
        try:
            # Update basic info
            lecture.title = form.title.data

            # Only update YouTube info if URL changed
            if form.youtube_url.data != f"https://youtu.be/{lecture.youtube_id}":
                video_info = get_youtube_video_info(form.youtube_url.data)
                lecture.youtube_id = video_info['youtube_id']
                lecture.thumbnail_url = video_info['thumbnail_url']
                lecture.publish_date = video_info['publish_date']

            # Update relationships
            selected_topic = Topic.query.get(form.topics.data)
            selected_tags = Tag.query.filter(Tag.id.in_(form.tags.data)).all()
            selected_rank = Rank.query.get(form.rank.data)
            selected_collections = Collection.query.filter(Collection.id.in_(form.collections.data)).all()

            # Clear existing relationships
            lecture.topics = []
            lecture.tags = []

            # Add new selections
            if selected_topic:
                lecture.topics.append(selected_topic)
            lecture.tags = selected_tags

            lecture.rank_id = selected_rank.id if selected_rank else None

            # Update collections
            # First get current collections
            current_collections = Collection.query.join(
                collection_lecture,
                Collection.id == collection_lecture.c.collection_id
            ).filter(collection_lecture.c.lecture_id == lecture.id).all()

            # Remove lecture from collections that are no longer selected
            for collection in current_collections:
                if collection not in selected_collections:
                    collection.lectures.remove(lecture)

            # Add lecture to newly selected collections
            for collection in selected_collections:
                if collection not in current_collections:
                    collection.lectures.append(lecture)

            db.session.commit()
            flash('Lecture updated successfully!')
            return redirect(url_for('manage_lectures'))
        except Exception as e:
            logging.error(f"Error updating lecture: {str(e)}")
            flash('Error updating lecture. Please check the form data.')

    elif request.method == 'GET':
        form.title.data = lecture.title
        form.youtube_url.data = f"https://youtu.be/{lecture.youtube_id}"

        # Set form data to first item in each relationship for topic
        if lecture.topics:
            form.topics.data = lecture.topics[0].id

        # Set tags (now multi-select)
        form.tags.data = [tag.id for tag in lecture.tags]

        form.rank.data = lecture.rank_id if lecture.rank_id else None

        # Get all collections that contain this lecture
        lecture_collections = Collection.query.join(
            collection_lecture,
            Collection.id == collection_lecture.c.collection_id
        ).filter(collection_lecture.c.lecture_id == lecture.id).all()

        form.collections.data = [collection.id for collection in lecture_collections]

    return render_template('admin/edit_lecture.html', form=form, lecture=lecture)

@app.route('/admin/metadata', methods=['GET', 'POST'])
@login_required
def manage_metadata():
    topic_form = MetadataForm(prefix="topic")
    tag_form = MetadataForm(prefix="tag")
    rank_form = MetadataForm(prefix="rank")
    collection_form = MetadataForm(prefix="collection")

    if request.method == 'POST':
        # Handle additions
        if 'add_topic' in request.form and topic_form.validate():
            topic = Topic(name=topic_form.name.data)
            db.session.add(topic)
            success, error = safe_commit()
            flash('Topic added successfully' if success else f'Error adding topic: {error}')

        elif 'add_tag' in request.form and tag_form.validate():
            tag = Tag(name=tag_form.name.data)
            db.session.add(tag)
            success, error = safe_commit()
            flash('Tag added successfully' if success else f'Error adding tag: {error}')

        elif 'add_rank' in request.form and rank_form.validate():
            rank = Rank(name=rank_form.name.data)
            db.session.add(rank)
            success, error = safe_commit()
            flash('Rank added successfully' if success else f'Error adding rank: {error}')

        elif 'add_collection' in request.form and collection_form.validate():
            collection = Collection(name=collection_form.name.data)
            db.session.add(collection)
            success, error = safe_commit()
            flash('Collection added successfully' if success else f'Error adding collection: {error}')

        # Handle deletions with common pattern
        elif 'delete_topic' in request.form:
            topic_id = request.form['delete_topic']
            topic = Topic.query.get(topic_id)
            if topic:
                try:
                    db.session.delete(topic)
                    success, error = safe_commit()
                    if success:
                        flash(f'Topic "{topic.name}" deleted successfully')
                    else:
                        flash(f'Cannot delete topic: {error}')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Cannot delete topic: it may be used by lectures. Error: {str(e)}')

        elif 'delete_tag' in request.form:
            tag_id = request.form['delete_tag']
            tag = Tag.query.get(tag_id)
            if tag:
                try:
                    db.session.delete(tag)
                    success, error = safe_commit()
                    if success:
                        flash(f'Tag "{tag.name}" deleted successfully')
                    else:
                        flash(f'Cannot delete tag: {error}')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Cannot delete tag: it may be used by lectures. Error: {str(e)}')

        elif 'delete_rank' in request.form:
            rank_id = request.form['delete_rank']
            rank = Rank.query.get(rank_id)
            if rank:
                try:
                    db.session.delete(rank)
                    success, error = safe_commit()
                    if success:
                        flash(f'Rank "{rank.name}" deleted successfully')
                    else:
                        flash(f'Cannot delete rank: {error}')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Cannot delete rank: it may be used by lectures. Error: {str(e)}')

        elif 'delete_collection' in request.form:
            collection_id = request.form['delete_collection']
            collection = Collection.query.get(collection_id)
            if collection:
                try:
                    db.session.delete(collection)
                    success, error = safe_commit()
                    if success:
                        flash(f'Collection "{collection.name}" deleted successfully')
                    else:
                        flash(f'Cannot delete collection: {error}')
                except Exception as e:
                    db.session.rollback()
                    flash(f'Cannot delete collection: it may be used by lectures. Error: {str(e)}')

        # Handle edits with common pattern
        elif 'edit_topic' in request.form:
            topic_id = request.form['topic_id']
            new_name = request.form['topic_name']
            topic = Topic.query.get(topic_id)
            if topic and new_name:
                topic.name = new_name
                success, error = safe_commit()
                flash('Topic updated successfully' if success else f'Error updating topic: {error}')

        elif 'edit_tag' in request.form:
            tag_id = request.form['tag_id']
            new_name = request.form['tag_name']
            tag = Tag.query.get(tag_id)
            if tag and new_name:
                tag.name = new_name
                success, error = safe_commit()
                flash('Tag updated successfully' if success else f'Error updating tag: {error}')

        elif 'edit_rank' in request.form:
            rank_id = request.form['rank_id']
            new_name = request.form['rank_name']
            rank = Rank.query.get(rank_id)
            if rank and new_name:
                rank.name = new_name
                success, error = safe_commit()
                flash('Rank updated successfully' if success else f'Error updating rank: {error}')

    # Get metadata for the page
    metadata = get_metadata()

    return render_template('admin/manage_metadata.html',
                         topic_form=topic_form,
                         tag_form=tag_form,
                         rank_form=rank_form,
                         topics=metadata['topics'],
                         tags=metadata['tags'],
                         ranks=metadata['ranks'],
                         collection_form=collection_form,
                         collections=metadata['collections'])

@app.route('/admin/export', methods=['GET'])
@login_required
def export_data():
    try:
        # Get all data
        lectures = Lecture.query.all()
        topics = Topic.query.all()
        tags = Tag.query.all()
        ranks = Rank.query.all()
        collections = Collection.query.all()

        # Prepare data for export
        export_data = {
            'lectures': [],
            'topics': [],
            'tags': [],
            'ranks': [],
            'collections': []
        }

        # Add topics
        for topic in topics:
            export_data['topics'].append({
                'id': topic.id,
                'name': topic.name
            })

        # Add tags
        for tag in tags:
            export_data['tags'].append({
                'id': tag.id,
                'name': tag.name
            })

        # Add ranks
        for rank in ranks:
            export_data['ranks'].append({
                'id': rank.id,
                'name': rank.name
            })

        # Add collections
        for collection in collections:
            # Get lectures with their positions
            lecture_positions = []
            for lecture in collection.lectures:
                position_data = db.session.query(collection_lecture.c.position).filter(
                    collection_lecture.c.collection_id == collection.id,
                    collection_lecture.c.lecture_id == lecture.id
                ).first()

                position = position_data[0] if position_data else 0
                lecture_positions.append({
                    'lecture_id': lecture.id,
                    'position': position
                })

            # Sort by position
            lecture_positions.sort(key=lambda x: x['position'])

            export_data['collections'].append({
                'id': collection.id,
                'name': collection.name,
                'description': collection.description,
                'is_paid': collection.is_paid,
                'created_at': collection.created_at.isoformat() if collection.created_at else None,
                'lectures': lecture_positions
            })

        # Add lectures
        for lecture in lectures:
            lecture_data = {
                'id': lecture.id,
                'title': lecture.title,
                'youtube_id': lecture.youtube_id,
                'thumbnail_url': lecture.thumbnail_url,
                'publish_date': lecture.publish_date.isoformat(),
                'duration_seconds': lecture.duration_seconds,
                'rank_id': lecture.rank_id,
                'topic_ids': [topic.id for topic in lecture.topics],
                'tag_ids': [tag.id for tag in lecture.tags],
                'collection_ids': [c.id for c in Collection.query.join(
                    collection_lecture, 
                    Collection.id == collection_lecture.c.collection_id
                ).filter(collection_lecture.c.lecture_id == lecture.id).all()]
            }
            export_data['lectures'].append(lecture_data)

        # Return JSON file for download
        response = jsonify(export_data)
        response.headers.set('Content-Disposition', 'attachment', filename='baduk_lectures_export.json')
        return response
    except Exception as e:
        logging.error(f"Error exporting data: {str(e)}")
        flash(f'Error exporting data: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin/import', methods=['GET', 'POST'])
@login_required
def import_data():
    if request.method == 'POST':
        try:
            if 'import_file' not in request.files:
                flash('No file part')
                return redirect(request.url)

            file = request.files['import_file']
            if file.filename == '':
                flash('No selected file')
                return redirect(request.url)

            if file:
                import_data = json.loads(file.read().decode('utf-8'))

                # Create mappings to store old ID to new ID relationships
                topic_id_map = {}
                tag_id_map = {}
                rank_id_map = {}
                collection_id_map = {}
                lecture_id_map = {}

                # Process topics
                if 'topics' in import_data:
                    for topic_data in import_data['topics']:
                        # Check if topic already exists
                        existing_topic = Topic.query.filter_by(name=topic_data['name']).first()
                        if not existing_topic:
                            # Always create with a new ID
                            new_topic = Topic(name=topic_data['name'])
                            db.session.add(new_topic)
                            db.session.flush()
                            topic_id_map[topic_data['id']] = new_topic.id
                        else:
                            topic_id_map[topic_data['id']] = existing_topic.id

                # Process tags
                if 'tags' in import_data:
                    for tag_data in import_data['tags']:
                        # Check if tag already exists
                        existing_tag = Tag.query.filter_by(name=tag_data['name']).first()
                        if not existing_tag:
                            # Always create with a new ID
                            new_tag = Tag(name=tag_data['name'])
                            db.session.add(new_tag)
                            db.session.flush()
                            tag_id_map[tag_data['id']] = new_tag.id
                        else:
                            tag_id_map[tag_data['id']] = existing_tag.id

                # Process ranks
                if 'ranks' in import_data:
                    for rank_data in import_data['ranks']:
                        # Check if rank already exists
                        existing_rank = Rank.query.filter_by(name=rank_data['name']).first()
                        if not existing_rank:
                            # Always create with a new ID
                            new_rank = Rank(name=rank_data['name'])
                            db.session.add(new_rank)
                            db.session.flush()
                            rank_id_map[rank_data['id']] = new_rank.id
                        else:
                            rank_id_map[rank_data['id']] = existing_rank.id

                # Process collections (basic info first, we'll assign lectures later)
                if 'collections' in import_data:
                    for collection_data in import_data['collections']:
                        # Check if collection already exists
                        existing_collection = Collection.query.filter_by(name=collection_data['name']).first()
                        if not existing_collection:
                            # Always create with a new ID
                            new_collection = Collection(
                                name=collection_data['name'],
                                description=collection_data.get('description', ''),
                                is_paid=collection_data.get('is_paid', False),
                                created_at=datetime.fromisoformat(collection_data['created_at']) if collection_data.get('created_at') else datetime.utcnow()
                            )
                            db.session.add(new_collection)
                            db.session.flush()
                            collection_id_map[collection_data['id']] = new_collection.id
                        else:
                            collection_id_map[collection_data['id']] = existing_collection.id

                # Process lectures
                if 'lectures' in import_data:
                    for lecture_data in import_data['lectures']:
                        # Check if lecture already exists by YouTube ID
                        existing_lecture = Lecture.query.filter_by(youtube_id=lecture_data['youtube_id']).first()
                        if not existing_lecture:
                            # Always create with a new ID
                            new_lecture = Lecture(
                                title=lecture_data['title'],
                                youtube_id=lecture_data['youtube_id'],
                                thumbnail_url=lecture_data['thumbnail_url'],
                                publish_date=datetime.fromisoformat(lecture_data['publish_date']),
                                duration_seconds=lecture_data.get('duration_seconds',0)
                            )

                            # Set rank
                            if lecture_data.get('rank_id') and lecture_data['rank_id'] in rank_id_map:
                                new_lecture.rank_id = rank_id_map[lecture_data['rank_id']]
                            
                            db.session.add(new_lecture)
                            db.session.flush()
                            
                            # Add topics
                            if 'topic_ids' in lecture_data:
                                for old_topic_id in lecture_data['topic_ids']:
                                    if old_topic_id in topic_id_map:
                                        topic = Topic.query.get(topic_id_map[old_topic_id])
                                        if topic:
                                            new_lecture.topics.append(topic)

                            # Add tags
                            if 'tag_ids' in lecture_data:
                                for old_tag_id in lecture_data['tag_ids']:
                                    if old_tag_id in tag_id_map:
                                        tag = Tag.query.get(tag_id_map[old_tag_id])
                                        if tag:
                                            new_lecture.tags.append(tag)
                            
                            lecture_id_map[lecture_data['id']] = new_lecture.id
                        else:
                            lecture_id_map[lecture_data['id']] = existing_lecture.id

                # Now associate lectures with collections
                if 'collections' in import_data:
                    for collection_data in import_data['collections']:
                        if collection_data['id'] in collection_id_map:
                            collection = Collection.query.get(collection_id_map[collection_data['id']])
                            if collection:
                                # Handle both new and old format
                                if 'lectures' in collection_data:
                                    # New format with position data
                                    for lecture_data in collection_data['lectures']:
                                        old_lecture_id = lecture_data['lecture_id']
                                        position = lecture_data.get('position', 0)

                                        if old_lecture_id in lecture_id_map:
                                            lecture = Lecture.query.get(lecture_id_map[old_lecture_id])
                                            if lecture:
                                                if lecture not in collection.lectures:
                                                    collection.lectures.append(lecture)

                                                # Set position
                                                db.session.execute(
                                                    collection_lecture.update().
                                                    where(collection_lecture.c.collection_id == collection.id).
                                                    where(collection_lecture.c.lecture_id == lecture.id).
                                                    values(position=position)
                                                )

                                elif 'lecture_ids' in collection_data:
                                    # Old format without position
                                    for position, old_lecture_id in enumerate(collection_data['lecture_ids']):
                                        if old_lecture_id in lecture_id_map:
                                            lecture = Lecture.query.get(lecture_id_map[old_lecture_id])
                                            if lecture:
                                                if lecture not in collection.lectures:
                                                    collection.lectures.append(lecture)

                                                # Set position
                                                db.session.execute(
                                                    collection_lecture.update().
                                                    where(collection_lecture.c.collection_id == collection.id).
                                                    where(collection_lecture.c.lecture_id == lecture.id).
                                                    values(position=position)
                                                )

                db.session.commit()
                flash('Data imported successfully')
                return redirect(url_for('admin_panel'))

        except Exception as e:
            db.session.rollback()
            logging.error(f"Error importing data: {str(e)}")
            flash(f'Error importing data: {str(e)}')
            return redirect(request.url)

    return render_template('admin/import.html')

@app.route('/admin/reset', methods=['POST'])
@login_required
def reset_data():
    try:
        # Get all data first for backup
        lectures = Lecture.query.all()
        topics = Topic.query.all()
        tags = Tag.query.all()
        ranks = Rank.query.all()
        collections = Collection.query.all()

        # Prepare data for export (same as in export_data)
        export_data = {
            'lectures': [],
            'topics': [],
            'tags': [],
            'ranks': [],
            'collections': []
        }

        # Add topics
        for topic in topics:
            export_data['topics'].append({
                'id': topic.id,
                'name': topic.name
            })

        # Add tags
        for tag in tags:
            export_data['tags'].append({
                'id': tag.id,
                'name': tag.name
            })

        # Add ranks
        for rank in ranks:
            export_data['ranks'].append({
                'id': rank.id,
                'name': rank.name
            })

        # Add collections with full details
        for collection in collections:
            # Get lectures with their positions
            lecture_positions = []
            for lecture in collection.lectures:
                position_data = db.session.query(collection_lecture.c.position).filter(
                    collection_lecture.c.collection_id == collection.id,
                    collection_lecture.c.lecture_id == lecture.id
                ).first()

                position = position_data[0] if position_data else 0
                lecture_positions.append({
                    'lecture_id': lecture.id,
                    'position': position
                })

            # Sort by position
            lecture_positions.sort(key=lambda x: x['position'])
            
            export_data['collections'].append({
                'id': collection.id,
                'name': collection.name,
                'description': collection.description,
                'is_paid': collection.is_paid,
                'created_at': collection.created_at.isoformat() if collection.created_at else None,
                'lectures': lecture_positions
            })

        # Add lectures
        for lecture in lectures:
            lecture_data = {
                'id': lecture.id,
                'title': lecture.title,
                'youtube_id': lecture.youtube_id,
                'thumbnail_url': lecture.thumbnail_url,
                'publish_date': lecture.publish_date.isoformat(),
                'duration_seconds': lecture.duration_seconds,
                'rank_id': lecture.rank_id,
                'topic_ids': [topic.id for topic in lecture.topics],
                'tag_ids': [tag.id for tag in lecture.tags],
                'collection_ids': [c.id for c in Collection.query.join(
                    collection_lecture, 
                    Collection.id == collection_lecture.c.collection_id
                ).filter(collection_lecture.c.lecture_id == lecture.id).all()]
            }
            export_data['lectures'].append(lecture_data)

        # Clear database
        # Use raw SQL for faster deletion of many records
        db.session.execute(db.text("DELETE FROM lecture_topic"))
        db.session.execute(db.text("DELETE FROM lecture_tag"))
        db.session.execute(db.text("DELETE FROM collection_lecture"))
        db.session.execute(db.text("DELETE FROM lecture"))
        db.session.execute(db.text("DELETE FROM topic"))
        db.session.execute(db.text("DELETE FROM tag"))
        db.session.execute(db.text("DELETE FROM rank"))
        db.session.execute(db.text("DELETE FROM collection"))
        
        # Reset the auto-increment counters
        db.session.execute(db.text("ALTER SEQUENCE lecture_id_seq RESTART WITH 1"))
        db.session.execute(db.text("ALTER SEQUENCE topic_id_seq RESTART WITH 1"))
        db.session.execute(db.text("ALTER SEQUENCE tag_id_seq RESTART WITH 1"))
        db.session.execute(db.text("ALTER SEQUENCE rank_id_seq RESTART WITH 1"))
        db.session.execute(db.text("ALTER SEQUENCE collection_id_seq RESTART WITH 1"))
        db.session.commit()

        flash('All data has been reset successfully')
        # Return JSON for download with proper headers
        response = jsonify(export_data)
        response.headers.set('Content-Disposition', 'attachment', 
                             filename=f'baduk_lectures_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        return response
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error resetting data: {str(e)}")
        flash(f'Error resetting data: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin')
@login_required
def check_admin():
    if not current_user.is_admin:
        flash('You do not have admin privileges')
        return redirect(url_for('search'))
    return redirect(url_for('admin_panel'))

@app.route('/admin/panel')
@login_required
def admin_panel():
    return render_template('admin/panel.html')

@app.route('/admin/lectures')
@login_required
def manage_lectures():
    if not current_user.is_admin:
        flash('You do not have admin privileges')
        return redirect(url_for('search'))

    # Get only necessary metadata
    topics = Topic.query.all()
    tags = Tag.query.all()
    ranks = Rank.query.all()
    return render_template('admin/manage_lectures.html', topics=topics, tags=tags, ranks=ranks)

@app.cli.command("create-admin")
def create_admin():
    """Create an admin user."""
    admin = User(username="admin")
    admin.set_password("BadukAdmin2025!")
    db.session.add(admin)
    db.session.commit()
    logging.info("Admin user created successfully!")
@app.route('/collections')
def collections():
    collections = Collection.query.filter_by(is_paid=False).all()
    
    # Calculate total duration for each collection
    for collection in collections:
        total_duration_seconds = sum(lecture.duration_seconds or 0 for lecture in collection.lectures)
        hours, remainder = divmod(total_duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        collection.total_duration = {
            'hours': hours, 
            'minutes': minutes, 
            'seconds': seconds,
            'total_seconds': total_duration_seconds
        }
    
    return render_template('collections.html', collections=collections)

@app.route('/paid-collections')
@login_required
def paid_collections():
    collections = Collection.query.filter_by(is_paid=True).all()
    
    # Calculate total duration for each collection
    for collection in collections:
        total_duration_seconds = sum(lecture.duration_seconds or 0 for lecture in collection.lectures)
        hours, remainder = divmod(total_duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        collection.total_duration = {
            'hours': hours, 
            'minutes': minutes, 
            'seconds': seconds,
            'total_seconds': total_duration_seconds
        }
    
    return render_template('paid_collections.html', collections=collections)

@app.route('/collection/<int:collection_id>', methods=['GET', 'POST'])
def view_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)

    # Restrict access to paid collections if user is not logged in
    if collection.is_paid and not current_user.is_authenticated:
        flash('You need to login to access paid collections.')
        return redirect(url_for('login'))

    # Handle admin actions (remove lecture)
    if request.method == 'POST' and current_user.is_authenticated and current_user.is_admin:
        if 'remove_lecture' in request.form:
            lecture_id = int(request.form['remove_lecture'])

            # Use direct SQL to remove just this relationship
            db.session.execute(
                db.text(f"DELETE FROM collection_lecture WHERE collection_id = {collection_id} AND lecture_id = {lecture_id}")
            )
            success, error = safe_commit()

            if success:
                flash('Lecture removed from collection')
            else:
                flash(f'Error removing lecture: {error}')

            return redirect(url_for('view_collection', collection_id=collection_id))

    # Get lectures for this collection using utility function
    lectures = get_collection_lectures(collection_id)
    
    # Calculate total duration
    total_duration_seconds = sum(lecture.duration_seconds or 0 for lecture in lectures)
    # Convert to hours, minutes, seconds format
    hours, remainder = divmod(total_duration_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    total_duration = {'hours': hours, 'minutes': minutes, 'seconds': seconds, 'total_seconds': total_duration_seconds}

    return render_template('view_collection.html', 
                          collection=collection, 
                          lectures=lectures, 
                          total_duration=total_duration)

@app.route('/collection/<int:collection_id>/reorder', methods=['POST'])
@login_required
def reorder_collection_lectures_frontend(collection_id):
    # Only admin can reorder collections
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin privileges required'}), 403

    try:
        # Get lecture IDs from request
        lecture_ids = request.json.get('lecture_ids', [])

        # Verify all lectures exist in this collection before making changes
        collection = Collection.query.get_or_404(collection_id)
        collection_lecture_ids = [lecture.id for lecture in collection.lectures]

        # Ensure we're only reordering existing items, not adding or removing
        if not all(int(lid) in collection_lecture_ids for lid in lecture_ids):
            return jsonify({'success': False, 'error': 'Lecture IDs do not match collection content'}), 400

        # Update positions in the database - ONLY update position
        for position, lecture_id in enumerate(lecture_ids):
            db.session.execute(
                collection_lecture.update().
                where(collection_lecture.c.collection_id == collection_id).
                where(collection_lecture.c.lecture_id == lecture_id).
values(position=position)

            )

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error reordering lectures: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/collections', methods=['GET', 'POST'])
@login_required
def manage_collections():
    form = CollectionForm()

    if request.method == 'POST':
        if 'add_collection' in request.form and form.validate_on_submit():
            is_paid = form.is_paid.data == 1  # Direct comparison since is_paid is an integer
            collection = Collection(
                name=form.name.data,
                description=form.description.data,
                is_paid=is_paid
            )
            db.session.add(collection)
            db.session.commit()
            flash('Collection added successfully!')
            return redirect(url_for('manage_collections'))

        if 'delete_collection' in request.form:
            collection_id = int(request.form['delete_collection'])
            collection = Collection.query.get_or_404(collection_id)
            db.session.delete(collection)
            db.session.commit()
            flash('Collection deleted successfully!')
            return redirect(url_for('manage_collections'))

    collections = Collection.query.all()
    return render_template('admin/manage_collections.html', form=form, collections=collections)

@app.route('/admin/collection/edit/<int:collection_id>', methods=['GET', 'POST'])
@login_required
def edit_collection(collection_id):
    collection = Collection.query.get_or_404(collection_id)
    form = CollectionForm()

    # Get lectures for this collection
    lectures_query = db.session.query(
        Lecture
    ).join(
        collection_lecture,
        Lecture.id == collection_lecture.c.lecture_id
    ).filter(
        collection_lecture.c.collection_id == collection_id
    )

    # Try to order by position if it exists
    try:
        lectures = lectures_query.order_by(collection_lecture.c.position).all()
    except:
        # Fall back to default ordering
        lectures = lectures_query.all()

    if request.method == 'POST':
        # Handle lecture removal if explicitly requested
        if 'remove_lecture' in request.form:
            lecture_id = int(request.form['remove_lecture'])
            lecture = Lecture.query.get_or_404(lecture_id)

            # Use direct SQL to remove just this relationship
            db.session.execute(
                db.text(f"DELETE FROM collection_lecture WHERE collection_id = {collection_id} AND lecture_id = {lecture_id}")
            )
            db.session.commit()

            flash('Lecture removed from collection')
            # Redirect to same page to refresh lecture list
            return redirect(url_for('edit_collection', collection_id=collection_id))

        # Handle form submission - only update basic collection info
        elif form.validate_on_submit():
            # Only update the collection metadata, not touching lectures at all

            # Save original values before modification
            orig_name = collection.name
            orig_desc = collection.description
            orig_paid = collection.is_paid

            # Get new values from form
            new_name = form.name.data
            new_desc = form.description.data 
            new_paid = form.is_paid.data == 1  # Direct comparison since is_paid is an integer

            # Update basic collection info with direct SQL to avoid ORM issues
            db.session.execute(
                db.text(f"""
                    UPDATE collection 
                    SET name = :name, description = :description, is_paid = :is_paid 
                    WHERE id = :id
                """),
                {
                    'name': new_name,
                    'description': new_desc,
                    'is_paid': new_paid,
                    'id': collection_id
                }
            )

            db.session.commit()

            # Log changes for debugging
            changes = []
            if orig_name != new_name:
                changes.append(f"Name: '{orig_name}' → '{new_name}'")
            if orig_desc != new_desc:
                changes.append(f"Description updated")
            if orig_paid != new_paid:
                changes.append(f"Paid status: {orig_paid} → {new_paid}")

            change_msg = ", ".join(changes) if changes else "No changes detected"
            flash(f'Collection updated successfully! {change_msg}')
            return redirect(url_for('manage_collections'))

    elif request.method == 'GET':
        # Populate form with current values
        form.name.data = collection.name
        form.description.data = collection.description
        form.is_paid.data = [1] if collection.is_paid else [0]

    return render_template('admin/edit_collection.html', form=form, collection=collection, lectures=lectures)

@app.route('/admin/collection/<int:collection_id>/reorder', methods=['POST'])
@login_required
def reorder_collection_lectures(collection_id):
    if not current_user.is_admin:
        flash('You do not have admin privileges')
        return redirect(url_for('search'))

    try:
        # Get lecture IDs from request
        lecture_ids = request.json.get('lecture_ids', [])

        # Check if this is only a reorder action (not modifying collection content)
        action = request.json.get('action', '')

        # Verify all lectures exist in this collection before making changes
        collection = Collection.query.get_or_404(collection_id)
        collection_lecture_ids = [lecture.id for lecture in collection.lectures]

        # Ensure we're only reordering existing items, not adding or removing
        if set(int(lid) for lid in lecture_ids) != set(collection_lecture_ids):
            return jsonify({'success': False, 'error': 'Lecture IDs do not match collection content'}), 400

        # Update positions in the database - ONLY update position
        for position, lecture_id in enumerate(lecture_ids):
            db.session.execute(
                collection_lecture.update().
                where(collection_lecture.c.collection_id == collection_id).
                where(collection_lecture.c.lecture_id == lecture_id).
                values(position=position)
            )

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error reordering lectures: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/collection/<int:collection_id>/move-lecture', methods=['POST'])
@login_required
def move_lecture_position(collection_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'error': 'Admin privileges required'}), 403

    try:
        # Get lecture ID and new position from request
        lecture_id = request.json.get('lecture_id')
        new_position = request.json.get('new_position')  # 0-based index

        if lecture_id is None or new_position is None:
            return jsonify({'success': False, 'error': 'Missing lecture_id or new_position'}), 400

        # Get the collection
        collection = Collection.query.get_or_404(collection_id)

        # Get all lectures in this collection with their positions
        lectures_positions = db.session.query(
            Lecture.id, 
            collection_lecture.c.position
        ).join(
            collection_lecture,
            Lecture.id == collection_lecture.c.lecture_id
        ).filter(
            collection_lecture.c.collection_id == collection_id
        ).order_by(
            collection_lecture.c.position
        ).all()

        # Find the current position of the lecture to move
        current_position = None
        for lp in lectures_positions:
            if lp[0] == int(lecture_id):
                current_position = lp[1]
                break

        if current_position is None:
            return jsonify({'success': False, 'error': 'Lecture not found in this collection'}), 404

        # Convert new_position to int
        new_position = int(new_position)

        # Ensure new_position is within bounds
        if new_position < 0 or new_position >= len(lectures_positions):
            return jsonify({'success': False, 'error': 'Invalid position'}), 400

        # Skip if the position is the same
        if current_position == new_position:
            return jsonify({'success': True, 'message': 'Position unchanged'})

        # Update positions of all affected lectures
        if current_position < new_position:
            # Moving down: shift lectures between current+1 and new up by 1
            db.session.execute(
                collection_lecture.update().
                where(collection_lecture.c.collection_id == collection_id).
                where(collection_lecture.c.position > current_position).
                where(collection_lecture.c.position <= new_position).
                values(position=collection_lecture.c.position - 1)
            )
        else:
            # Moving up: shift lectures between new and current-1 down by 1
            db.session.execute(
                collection_lecture.update().
                where(collection_lecture.c.collection_id == collection_id).
                where(collection_lecture.c.position >= new_position).
                where(collection_lecture.c.position < current_position).
                values(position=collection_lecture.c.position + 1)
            )

        # Finally, update the position of the lecture being moved
        db.session.execute(
            collection_lecture.update().
            where(collection_lecture.c.collection_id == collection_id).
            where(collection_lecture.c.lecture_id == lecture_id).
            values(position=new_position)
        )

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error moving lecture: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/playlist-import', methods=['GET', 'POST'])
@login_required
def playlist_import():
    if not current_user.is_admin:
        flash('You do not have admin privileges')
        return redirect(url_for('search'))

    from youtube_utils import extract_playlist_id, fetch_playlist_videos

    # Default values
    videos = []
    current_video = None
    current_video_index = 0
    youtube_api_key = ""
    playlist_url = ""

    # Get metadata for the dropdown selections
    topics = Topic.query.all()
    tags = Tag.query.all()
    ranks = Rank.query.all()
    collections = Collection.query.all()

    if request.method == 'POST':
        youtube_api_key = request.form.get('youtube_api_key', '')
        playlist_url = request.form.get('playlist_url', '')
        step = request.form.get('step')

        # Step 1: Fetch videos from playlist
        if step == '1':
            playlist_id = extract_playlist_id(playlist_url)
            if not playlist_id:
                flash('Invalid YouTube playlist URL')
                return render_template('admin/playlist_import.html', topics=topics, tags=tags, 
                                      ranks=ranks, collections=collections)

            videos, error = fetch_playlist_videos(youtube_api_key, playlist_id)
            if error:
                flash(error)
                return render_template('admin/playlist_import.html', topics=topics, tags=tags, 
                                      ranks=ranks, collections=collections)

            if not videos:
                flash('No videos found in the playlist')
                return render_template('admin/playlist_import.html', topics=topics, tags=tags, 
                                      ranks=ranks, collections=collections)

            # Start with the first video
            current_video = videos[0]
            current_video_index = 0

            return render_template('admin/playlist_import.html', videos=videos, 
                                  current_video=current_video, current_video_index=current_video_index,
                                  youtube_api_key=youtube_api_key, playlist_url=playlist_url,
                                  topics=topics, tags=tags, ranks=ranks, collections=collections)

        # Step 2: Process current video
        elif step == '2':
            video_index = int(request.form.get('video_index', 0))
            action = request.form.get('action', '')

            # Re-fetch videos to maintain state
            playlist_id = extract_playlist_id(playlist_url)
            videos, _ = fetch_playlist_videos(youtube_api_key, playlist_id)

            current_video = videos[video_index]
            
            # If user chose to save this video
            if action == 'save':
                # Get form data
                rank_id = request.form.get('rank')
                topic_id = request.form.get('topic')
                tag_id = request.form.get('tag')
                collection_id = request.form.get('collection')

                # Check if video already exists
                existing_lecture = Lecture.query.filter_by(youtube_id=current_video['video_id']).first()
                if not existing_lecture:
                    # Create new lecture - rank is required
                    new_lecture = Lecture(
                        title=current_video['title'],
                        youtube_id=current_video['video_id'],
                        thumbnail_url=current_video['thumbnail_url'],
                        publish_date=current_video['published_at'],
                        duration_seconds=current_video.get('duration_seconds', 0),
                        rank_id=rank_id
                    )

                    # Add topic (required)
                    topic = Topic.query.get(topic_id)
                    if topic:
                        new_lecture.topics.append(topic)

                    # Add tag (optional)
                    if tag_id:
                        tag = Tag.query.get(tag_id)
                        if tag:
                            new_lecture.tags.append(tag)

                    # Add to collection
                    if collection_id:
                        collection = Collection.query.get(collection_id)
                        if collection:
                            collection.lectures.append(new_lecture)

                    db.session.add(new_lecture)
                    db.session.commit()
                    flash(f'Video "{current_video["title"]}" added successfully')
                else:
                    flash(f'Video "{current_video["title"]}" already exists in the database')
            elif action == 'skip':
                flash(f'Skipped video "{current_video["title"]}"')

            # Move to next video
            video_index += 1

            # If there are more videos to process
            if video_index < len(videos):
                current_video = videos[video_index]
                current_video_index = video_index
            else:
                current_video = None
                current_video_index = video_index
                flash('All videos processed successfully')

            return render_template('admin/playlist_import.html', videos=videos, 
                                  current_video=current_video, current_video_index=current_video_index,
                                  youtube_api_key=youtube_api_key, playlist_url=playlist_url,
                                  topics=topics, tags=tags, ranks=ranks, collections=collections)

    # GET request
    return render_template('admin/playlist_import.html', topics=topics, tags=tags, 
                          ranks=ranks, collections=collections)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_panel'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('admin_panel'))
        else:
            flash('Invalid username or password')
            # Log authentication failures at info level
            if user:
                logging.info(f"Failed login attempt: Password incorrect for user {user.username}")
            else:
                logging.info(f"Failed login attempt: User not found: {form.username.data}")
    return render_template('admin/login.html', form=form)

# Service worker route
@app.route('/service-worker.js')
def service_worker():
    return send_from_directory('.', 'service-worker.js')

# Sitemap route
@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory('.', 'sitemap.xml', mimetype='application/xml')