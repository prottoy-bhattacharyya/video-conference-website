import pymongo

def get_db():
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client["video_conference_app"]
    return db

def get_users_collection():
    db = get_db()
    usersCollection = db["users"]
    return usersCollection

def get_rooms_collection():
    db = get_db()
    roomsCollection = db["rooms"]
    return roomsCollection

def meeting_logs_collection():
    db = get_db()
    meetingsCollection = db["meeting_logs"]
    return meetingsCollection

def get_messages_collection():
    db = get_db()
    messagesCollection = db["messages"]
    return messagesCollection