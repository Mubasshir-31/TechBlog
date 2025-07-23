from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import re
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
import os
load_dotenv()
from dateutil import parser
# Add import for newspaper3k
try:
    from newspaper import Article as NewsArticle
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
app.secret_key = 'your_secret_key'

# Remove admin blueprint registration

NEWS_API_KEY = os.getenv("NEWSDATA_API_KEY")  # Replace with your NewsData.io API key
def fetch_and_store_tech_news():
    if not hasattr(mongo, 'db') or mongo.db is None:
        return
    posts = mongo.db.posts
    url = f'https://newsdata.io/api/1/news?apikey={NEWS_API_KEY}&category=technology&language=en'

    # Tech keywords and sources for stricter filtering
    TECH_KEYWORDS = [
        'ai', 'artificial intelligence', 'machine learning', 'deep learning', 'data science', 'programming',
        'software', 'hardware', 'computer', 'cloud', 'cybersecurity', 'blockchain', 'web', 'app', 'mobile',
        'gadget', 'robotics', 'coding', 'developer', 'tech', 'technology', 'startup', 'quantum', 'internet', 'network'
    ]
    TECH_SOURCES = [
        'techcrunch', 'thenextweb', 'wired', 'theverge', 'engadget', 'gizmodo', 'arstechnica', 'zdnet', 'cnet',
        'mashable', 'venturebeat', 'digitaltrends', 'androidcentral', '9to5mac', '9to5google'
    ]

    def is_tech_post(title, description, source_id):
        title = (title or '').lower()
        description = (description or '').lower()
        source_id = (source_id or '').lower()
        for kw in TECH_KEYWORDS:
            if kw in title or kw in description:
                return True
        for src in TECH_SOURCES:
            if src == source_id:
                return True
        return False

    try:
        resp = requests.get(url, timeout=15)
        data = resp.json()
        for article in data.get('results', []):
            title = article.get('title')
            description = article.get('description', '')
            source_id = article.get('source_id', '')
            if not title or posts.find_one({'title': title}):
                continue
            if not is_tech_post(title, description, source_id):
                continue  # Skip non-tech posts
            # Try to fetch full content using newspaper3k
            full_content = description
            if NEWSPAPER_AVAILABLE and article.get('link'):
                try:
                    news_article = NewsArticle(article['link'])
                    news_article.download()
                    news_article.parse()
                    if news_article.text and len(news_article.text) > len(full_content):
                        full_content = news_article.text
                except Exception as e:
                    print(f"[Warning] Could not extract full content for {title}: {e}")
            elif not NEWSPAPER_AVAILABLE:
                print("[Warning] newspaper3k not installed. Using description as content.")
            post = {
                'title': title,
                'content': full_content,
                'author': source_id or 'NewsData.io',
                'category': 'Technology',
                'tags': ['Tech', 'News', 'AutoUpdate'],
                'image_url': article.get('image_url', ''),
                'date': article.get('pubDate'),
                'source_url': article.get('link', '')
            }
            posts.insert_one(post)
    except Exception as e:
        print('Error fetching tech news:', e)

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(fetch_and_store_tech_news, 'interval', hours=1)
scheduler.start()

def fix_post_dates():
    """
    Update all posts in the database so that the 'date' field is always a valid datetime object.
    Converts string dates to datetime, and sets missing/invalid dates to now.
    """
    if not hasattr(mongo, 'db') or mongo.db is None:
        print("MongoDB connection is not available.")
        return
    posts = mongo.db.posts
    updated_count = 0
    for post in posts.find():
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
            posts.update_one({'_id': post_id}, {'$set': {'date': new_date}})
            updated_count += 1
    print(f"Updated {updated_count} posts with valid date fields.")

# Flask CLI command to run the fix manually
@app.cli.command('fix-dates')
def fix_dates_command():
    """Fix blog post date fields in the database."""
    if not hasattr(mongo, 'db') or mongo.db is None:
        print("MongoDB connection is not available.")
        return
    print("Flask app MongoDB URI:", app.config["MONGO_URI"])
    print("Flask app DB name:", mongo.db.name)
    print("Flask app posts count:", mongo.db.posts.count_documents({}))
    fix_post_dates()
    print("Date fields fixed.")

@app.context_processor
def utility_processor():
    return dict(str=str)

@app.context_processor
def inject_current_year():
    return {'current_year': datetime.utcnow().year}

@app.template_filter('date_display')
def date_display(value):
    from datetime import datetime
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, str):
        return value[:10]
    return str(value)

@app.route('/')
def home():
    if not hasattr(mongo, 'db') or mongo.db is None:
        posts = []
        latest_post_id = None
    else:
        posts_collection = mongo.db.posts
        q = request.args.get('q', '').strip()
        latest_post = posts_collection.find_one(sort=[('date', -1)])
        latest_post_id = str(latest_post['_id']) if latest_post else None
        if posts_collection is not None:
            if q:
                regex = re.compile(re.escape(q), re.IGNORECASE)
                # Get the latest post matching the query
                latest_post = posts_collection.find_one({
                    "$or": [
                        {"title": {"$regex": regex}},
                        {"content": {"$regex": regex}},
                        {"tags": {"$elemMatch": {"$regex": regex}}}
                    ]
                }, sort=[('date', -1)])
                latest_post_id = str(latest_post['_id']) if latest_post else None
                # Get the next 5 most recent posts (excluding the latest)
                other_posts = []
                if latest_post:
                    other_posts = list(posts_collection.find({
                        "$and": [
                            {"_id": {"$ne": latest_post['_id']}},
                            {"$or": [
                                {"title": {"$regex": regex}},
                                {"content": {"$regex": regex}},
                                {"tags": {"$elemMatch": {"$regex": regex}}}
                            ]}
                        ]
                    }).sort('date', -1).limit(5))
                    posts = [latest_post] + other_posts
                else:
                    posts = []
            else:
                # No search: get latest post, then next 5
                latest_post = posts_collection.find_one(sort=[('date', -1)])
                latest_post_id = str(latest_post['_id']) if latest_post else None
                other_posts = []
                if latest_post:
                    other_posts = list(posts_collection.find({"_id": {"$ne": latest_post['_id']}}).sort('date', -1).limit(5))
                    posts = [latest_post] + other_posts
                else:
                    posts = []
        else:
            posts = []
    return render_template('home.html', posts=posts, active_page='home', latest_post_id=latest_post_id)

@app.route('/about')
def about():
    return render_template('about.html', active_page='about')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        if name and email and message:
            if hasattr(mongo, 'db') and mongo.db is not None:
                mongo.db.contacts.insert_one({
                    'name': name,
                    'email': email,
                    'message': message,
                    'date': datetime.utcnow()
                })
                # Append to a single file in submissions folder
                submissions_dir = os.path.join(os.path.dirname(__file__), 'submissions')
                os.makedirs(submissions_dir, exist_ok=True)
                all_submissions_path = os.path.join(submissions_dir, 'all_submissions.txt')
                with open(all_submissions_path, 'a', encoding='utf-8') as f:
                    f.write(f"Name: {name}\nEmail: {email}\nMessage: {message}\nDate: {datetime.utcnow()}\n{'-'*40}\n")
                success = True
            else:
                flash('Database connection error. Message not saved.', 'danger')
        else:
            flash('All fields are required.', 'warning')
    return render_template('contact.html', active_page='contact', success=success)

@app.route('/blog')
def blog():
    if not hasattr(mongo, 'db') or mongo.db is None:
        posts = []
        latest_post_id = None
    else:
        posts_collection = mongo.db.posts
        q = request.args.get('q', '').strip()
        category = request.args.get('category', '').strip()
        tag = request.args.get('tag', '').strip()
        latest_post = posts_collection.find_one(sort=[('date', -1)])
        latest_post_id = str(latest_post['_id']) if latest_post else None
        if posts_collection is not None:
            query = {}
            if q:
                regex = re.compile(re.escape(q), re.IGNORECASE)
                query["$or"] = [
                    {"title": {"$regex": regex}},
                    {"content": {"$regex": regex}},
                    {"tags": {"$elemMatch": {"$regex": regex}}}
                ]
            if category:
                query["category"] = category
            if tag:
                query["tags"] = tag
            posts = list(posts_collection.find(query).sort('date', -1))
            # Filter posts to only those with more than 50 words in content
            posts = [post for post in posts if len((post.get('content') or '').split()) > 30]
        else:
            posts = []
    print("\n--- Blog Posts Sent to Template ---")
    for post in posts:
        print(f"Title: {post.get('title')}, Date: {post.get('date')} ({type(post.get('date'))}), Word count: {len((post.get('content') or '').split())}")
    print("--- End of List ---\n")
    return render_template('blog.html', posts=posts, active_page='blog', latest_post_id=latest_post_id)

@app.route('/blog/<ObjectId:post_id>', methods=['GET', 'POST'])
def blog_post(post_id):
    if not hasattr(mongo, 'db') or mongo.db is None:
        return "Database connection error", 500
    post = mongo.db.posts.find_one({'_id': post_id})
    if not post:
        return "Post not found", 404
    comment_submitted = False
    if request.method == 'POST':
        name = request.form.get('comment_name')
        text = request.form.get('comment_text')
        if name and text:
            mongo.db.comments.insert_one({
                'post_id': post_id,
                'name': name,
                'text': text,
                'date': datetime.utcnow(),
                'approved': True
            })
            # Redirect to avoid form resubmission
            return redirect(url_for('blog_post', post_id=post_id, _anchor='comments'))
    comments = list(mongo.db.comments.find({'post_id': post_id}).sort('date', 1))
    return render_template('post.html', post=post, comments=comments, comment_submitted=comment_submitted)

# Remove the like_post route and all like-related logic

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        post = {
            'title': request.form['title'],
            'content': request.form['content'],
            'author': request.form['author'],
            'category': request.form['category'],
            'tags': [tag.strip() for tag in request.form['tags'].split(',')],
            'image_url': request.form['image_url'],
            'date': datetime.utcnow(),
        }
        if hasattr(mongo, 'db') and mongo.db is not None:
            mongo.db.posts.insert_one(post)
            flash('Post created successfully!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Database connection error. Post not created.', 'danger')
    return render_template('create.html')

@app.route('/admin/messages')
def view_messages():
    if not hasattr(mongo, 'db') or mongo.db is None:
        messages = []
    else:
        messages = list(mongo.db.contacts.find().sort('date', -1))
    return render_template('messages.html', messages=messages, active_page='messages')

if __name__ == '__main__':
    app.run(debug=True) 