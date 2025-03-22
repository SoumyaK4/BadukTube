"""
Seed data script for populating initial data in the database
"""
from app import app, db
from models import Topic, Tag, Rank, Collection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

def seed_data():
    """Seed initial data if tables are empty"""
    with app.app_context():
        try:
            # Only seed if data doesn't exist
            if Topic.query.count() == 0:
                logging.info("Seeding topics...")
                topics = [
                    "Opening Theory", "Middle Game", "End Game", 
                    "Joseki", "Fuseki", "Life and Death", 
                    "Tesuji", "Strategy", "Professional Games"
                ]
                for topic_name in topics:
                    topic = Topic(name=topic_name)
                    db.session.add(topic)
                
                db.session.commit()
                logging.info(f"Added {len(topics)} topics")
            
            if Tag.query.count() == 0:
                logging.info("Seeding tags...")
                tags = [
                    "Attack", "Defense", "Influence", "Territory", 
                    "Thickness", "Sabaki", "Invasion", "Reduction", 
                    "Shape", "Direction of Play", "Advanced", "Beginner"
                ]
                for tag_name in tags:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                    
                db.session.commit()
                logging.info(f"Added {len(tags)} tags")
            
            if Rank.query.count() == 0:
                logging.info("Seeding ranks...")
                ranks = [
                    "All Levels", "Beginner", "25-20 kyu", "19-15 kyu", 
                    "14-10 kyu", "9-5 kyu", "4-1 kyu", 
                    "1-3 dan", "4-6 dan", "7-9 dan"
                ]
                for rank_name in ranks:
                    rank = Rank(name=rank_name)
                    db.session.add(rank)
                    
                db.session.commit()
                logging.info(f"Added {len(ranks)} ranks")
                
            if Collection.query.count() == 0:
                logging.info("Seeding collections...")
                collections = [
                    {"name": "Beginner Fundamentals", "description": "Essential concepts for new Go players", "is_paid": False},
                    {"name": "Opening Theory", "description": "Master the early game", "is_paid": False},
                    {"name": "Advanced Concepts", "description": "For experienced players looking to improve", "is_paid": True},
                    {"name": "Professional Game Analysis", "description": "Learn from the masters", "is_paid": True},
                ]
                
                for collection_data in collections:
                    collection = Collection(**collection_data)
                    db.session.add(collection)
                    
                db.session.commit()
                logging.info(f"Added {len(collections)} collections")
                
            logging.info("Seeding completed successfully")
            return True
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error seeding data: {e}")
            return False

if __name__ == "__main__":
    seed_data()