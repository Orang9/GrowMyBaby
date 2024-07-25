import os
from pymongo import MongoClient
from dotenv import load_dotenv
import bcrypt

# Memuat variabel lingkungan dari file .env
load_dotenv()

# Ambil URI MongoDB dari environment variable
mongo_uri = os.getenv("MONGO_URI")
if not mongo_uri:
    raise ValueError("MONGO_URI environment variable not set")

# Connect to MongoDB Atlas
client = MongoClient(mongo_uri)
db = client["sic5_belajar"]  # Replace with your database name
users_collection = db["login"]  # Collection to store user information
chat_collection = db["chat_history"] # Collection to store chat history

pw_hashing_key = os.getenv("PASSWORD_HASH_KEY")
def get_user(username, password):
    """Retrieve a user from the database by username and password."""
    user = users_collection.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode(), user["password"].encode()):
        return user
    return None

def add_user(username, password):
    """Add a new user to the database. Return True if successful, else False."""
    if users_collection.find_one({"username": username}):
        return False
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode(), salt).decode()
    users_collection.insert_one({"username": username, "password": hashed_password})
    return True

def fetch_users():
    users = users_collection.find()
    user_dict = {"usernames": {}}
    for user in users:
        user_dict["usernames"][user["username"]] = {
            "email": user.get("email", ""),
            "failed_login_attempts": user.get("failed_login_attempts", 0),
            "logged_in": user.get("logged_in", False),
            "name": user.get("name", "Unknown"),
            "password": str(user["password"])  # Ensure password is a string
        }
    return user_dict

def save_session_to_db(session_id, username, session_name, messages):
    """Save the entire session to the MongoDB collection."""
    session = {
        "session_id": session_id,
        "username": username,
        "session_name": session_name,
        "messages": messages
    }
    chat_collection.update_one(
        {"session_id": session_id},
        {"$set": session},
        upsert=True
    )
    users_collection.update_one(
        {"username": username},
        {"$addToSet": {"chat_sessions": session_id}},
        upsert=True
    )

def load_session_from_db(session_id):
    """Load a session from the MongoDB collection."""
    session = chat_collection.find_one({"session_id": session_id})
    return session["messages"] if session else []

def get_session_name(session_id):
    """Retrieve the session name from the MongoDB collection."""
    session = chat_collection.find_one({"session_id": session_id})
    return session["session_name"] if session else None

def get_session_ids_for_user(username):
    user_data = users_collection.find_one({"username": username})
    session_ids = []
    if user_data and "chat_sessions" in user_data:
        session_ids = user_data["chat_sessions"]
    return session_ids if user_data else []