# Baduk Lectures Platform

A comprehensive web application built with Flask for organizing and delivering educational video content through YouTube integration. This platform allows users to browse, search, and watch lectures based on topics, tags, and skill levels.

## Features

- **Content Organization**: Organizes lectures by topics, tags, and skill ranks
- **Collections**: Groups related lectures into collections (both free and premium)
- **Search Functionality**: Powerful search with filtering capabilities
- **YouTube Integration**: Seamlessly imports YouTube videos and playlists
- **Admin Panel**: Complete content management system for administrators
- **User Authentication**: Secure login system with role-based access control
- **Responsive Design**: Mobile-friendly interface with dark mode support
- **PWA Support**: Enhanced Progressive Web App capabilities:
  - App installation on mobile and desktop devices
  - Offline access to recently viewed content
  - Custom app icons and splash screens
  - Shortcuts for quick access to search and collections
- **SEO Optimization**: Proper sitemap.xml and robots.txt configuration

## Technical Stack

- **Backend**: Python, Flask
- **Database**: PostgreSQL (with SQLAlchemy ORM)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF, WTForms
- **External APIs**: YouTube Data API

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL database
- YouTube API key (for video imports)

### Environment Variables

The application requires the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: Secret key for Flask session management
- `YOUTUBE_API_KEY`: YouTube Data API key for fetching video information

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd baduk-lectures-platform
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (see section above)

4. Initialize the database:
   ```
   python
   >>> from app import app, db
   >>> with app.app_context():
   >>>     db.create_all()
   ```

5. Run the application:
   ```
   python main.py
   ```

## Application Structure

- `app.py`: Main application configuration and setup
- `main.py`: Application entry point
- `models.py`: Database models (User, Lecture, Topic, Tag, Rank, Collection)
- `routes.py`: URL routing and view functions
- `forms.py`: Form definitions for data input and validation
- `utils.py` & `youtube_utils.py`: Utility functions for YouTube integration
- `db_utils.py`: Database operation utilities
- `init_users.py`: User initialization and management
- `seed_data.py`: Initial data seeding
- `/templates`: HTML templates organized by functionality
- `/static`: CSS, JavaScript, images, and other static assets

## User Guide

### Public Features

- **Home Page**: Displays the latest lectures
- **Search Page**: Search and filter lectures by topic, tag, and rank
- **Collections**: Browse free lecture collections
- **Individual Lectures**: Watch lectures with embedded YouTube player

### Administrator Features

- **Admin Panel**: Accessible at `/admin` after login
- **Lecture Management**: Add, edit, and organize lectures
- **Collection Management**: Create and manage collections
- **Metadata Management**: Manage topics, tags, and ranks
- **Playlist Import**: Import multiple videos from YouTube playlists
- **Bulk Operations**: 
  - Add multiple existing lectures to collections at once
  - Filter lectures by topic, tag, rank, or keyword before bulk operations
  - Reorder lectures within collections using drag-and-drop
- **Data Management**: 
  - Export and import database tables (topics, tags, ranks, lectures, collections)
  - Options for merging or replacing data on import
  - Automatic data backup before destructive operations
- **Video Metadata**: Update video publish dates and durations from YouTube API

## Development Notes

### Database Management

- Models are defined in `models.py`
- ORM relationships are set up for easy querying
- Use database utilities in `db_utils.py` for common operations

### YouTube Integration

- YouTube video information is fetched via the YouTube Data API
- Video IDs are extracted from various URL formats
- Playlists can be imported in bulk
- Efficient batching of API requests (50 videos per batch) to stay within API limits
- Metadata updates for videos to ensure accurate publish dates and durations
- Utility script (`update_video_dates.py`) to correct dates for existing videos

### Authentication System

- User authentication is handled by Flask-Login
- Admin accounts have additional privileges
- Default admin account is created on first run

### Front-end Assets

- CSS is organized in the `/static/css` directory
- JavaScript functionality is in `/static/js`
- The site supports dark mode via `/static/js/theme.js`

### Progressive Web App

- Service worker for caching and offline capabilities
- Manifest configuration for installation on devices
- App icons in various sizes for different platforms
- Splash screens for iOS and Android devices
- App shortcuts for quick access to key features
- Desktop installation support

### SEO Optimization

- Properly formatted sitemap.xml for search engine indexing
- Robots.txt configuration for crawler guidance
- Structured metadata for better search engine visibility

## Deployment

The application is configured to run on port 5000 by default:

```python
app.run(host="0.0.0.0", port=5000)
```

For production deployment, consider using Gunicorn or uWSGI with a proper web server like Nginx.

## License

This project is licensed under the terms of the MIT license.