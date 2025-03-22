
from app import app, db
from models import User
import logging

def add_is_admin_column():
    """Add is_admin column to user table if it doesn't exist."""
    # This function is no longer needed for PostgreSQL as we can define
    # the column in our model and SQLAlchemy will handle it
    return True

def init_default_users():
    """Initialize default admin and regular users if they don't exist."""
    with app.app_context():
        try:
            # First ensure the is_admin column exists
            add_is_admin_column()
            
            # Check if admin exists
            admin = User.query.filter_by(username="admin").first()
            if not admin:
                logging.info("Creating default admin user")
                admin = User(username="admin", is_admin=True)
                admin.set_password("BadukAdmin2025!")
                db.session.add(admin)
            else:
                logging.info("Admin user already exists")
                # Ensure admin has admin privileges
                if not getattr(admin, 'is_admin', None):
                    admin.is_admin = True
                    logging.info("Updated admin user privileges")
                
            # Check if regular user exists
            regular_user = User.query.filter_by(username="Qi").first()
            if not regular_user:
                logging.info("Creating default regular user")
                regular_user = User(username="Qi", is_admin=False)
                regular_user.set_password("User@23")
                db.session.add(regular_user)
            else:
                logging.info("Regular user already exists")
                
            db.session.commit()
            logging.info("Default users initialized")
        except Exception as e:
            logging.error(f"Error initializing users: {e}")
            db.session.rollback()
