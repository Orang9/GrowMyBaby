from pymongo import MongoClient

# Connect to MongoDB Atlas
client = MongoClient("mongodb+srv://alfiSkibidi:alfi123@belajarcrud.p8wz7lk.mongodb.net/?retryWrites=true&w=majority&appName=BelajarCRUD")
db = client["sic5_belajar"]  # Replace with your database name
users_collection = db["login"]  # Collection to store user information

def get_user(username, password):
    """Retrieve a user from the database by username and password."""
    user = users_collection.find_one({"username": username, "password": password})
    return user

def add_user(username, password):
    """Add a new user to the database. Return True if successful, else False."""
    if users_collection.find_one({"username": username}):
        return False
    users_collection.insert_one({"username": username, "password": password})
    return True
