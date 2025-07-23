import os
from pymongo import MongoClient
from datetime import datetime
from dateutil import parser
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('MONGO_DBNAME', 'TechBlog')
COLLECTION_NAME = os.getenv('MONGO_COLLECTION', 'posts')

client = MongoClient(MONGO_URI)
db = client.get_database('TechBlog')
collection = db['posts']

updated_count = 0
skipped_count = 0

print("Fix script MongoDB URI:", MONGO_URI)
print("Fix script DB name:", db.name)
print("Fix script posts count:", collection.count_documents({}))

for post in collection.find():
    post_id = post.get('_id')
    date_val = post.get('date')
    new_date = None
    
    if date_val is None:
        new_date = datetime.utcnow()
    elif isinstance(date_val, str):
        try:
            new_date = parser.parse(date_val)
        except Exception:
            new_date = datetime.utcnow()
    elif not isinstance(date_val, datetime):
        new_date = datetime.utcnow()
    
    if new_date:
        collection.update_one({'_id': post_id}, {'$set': {'date': new_date}})
        print(f"Updated post {post_id} with new date: {new_date}")
        updated_count += 1
    else:
        skipped_count += 1

print(f"\nDone! Updated {updated_count} posts. Skipped {skipped_count} posts.") 

# Print all post titles and dates for verification
print("\n--- All Blog Posts (Title, Date, Type) ---")
for post in collection.find():
    print(f"Title: {post.get('title')}, Date: {post.get('date')} ({type(post.get('date'))})")
print("--- End of List ---\n") 