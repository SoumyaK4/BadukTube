
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Set secret key for session management
app.secret_key = os.environ.get("SESSION_SECRET")

# YouTube API configuration
app.config['YOUTUBE_API_KEY'] = os.environ.get('YOUTUBE_API_KEY', '')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import routes after initializing app to avoid circular imports
from routes import *
from models import *

# Initialize database and users
with app.app_context():
    # Create all tables based on models
    db.create_all()
    logging.info("Database tables created")
    
    # Import and initialize users
    from init_users import init_default_users
    init_default_users()
