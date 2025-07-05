
from app import app, db
from models import User
import logging
import os

def add_is_admin_column():
    """Add is_admin column to user table if it doesn't exist."""
    # This function is no longer needed for PostgreSQL as we can define
    # the column in our model and SQLAlchemy will handle it
    return True

def init_default_users():
    """Initialize default admin and regular users if they don't exist.
    
    Uses environment variables:
    - ADMIN_USERNAME: Username for admin (default: "admin")
    - ADMIN_PASSWORD: Password for admin (required if creating admin)
    - USER_USERNAME: Username for regular user (default: "user")
    - USER_PASSWORD: Password for regular user (required if creating user)
    """
    with app.app_context():
        try:
            # First ensure the is_admin column exists
            add_is_admin_column()
            
            # Get admin credentials from environment variables
            admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            
            # Check if admin exists
            admin = User.query.filter_by(username=admin_username).first()
            if not admin:
                if admin_password:
                    logging.info('Creating admin user: %s', admin_username)
                    admin = User(username=admin_username, is_admin=True)
                    admin.set_password(admin_password)
                    db.session.add(admin)
                else:
                    logging.warning('ADMIN_PASSWORD environment variable not set. Skipping admin creation.')
            else:
                logging.info('Admin user already exists')
                # Ensure admin has admin privileges
                if not getattr(admin, 'is_admin', None):
                    admin.is_admin = True
                    logging.info('Updated admin user privileges')
                
            # Get regular user credentials from environment variables
            user_username = os.environ.get('USER_USERNAME', 'user')
            user_password = os.environ.get('USER_PASSWORD')
            
            # Check if regular user exists
            regular_user = User.query.filter_by(username=user_username).first()
            if not regular_user:
                if user_password:
                    logging.info('Creating regular user: %s', user_username)
                    regular_user = User(username=user_username, is_admin=False)
                    regular_user.set_password(user_password)
                    db.session.add(regular_user)
                else:
                    logging.warning('USER_PASSWORD environment variable not set. Skipping user creation.')
            else:
                logging.info('Regular user already exists')
                
            db.session.commit()
            logging.info('Default users initialized')
        except Exception as e:
            logging.error('Error initializing users: %s', e)
            db.session.rollback()
