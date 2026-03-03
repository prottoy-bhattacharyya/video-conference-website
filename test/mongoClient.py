# from pymongo.mongo_client import MongoClient
# from pymongo.server_api import ServerApi

# uri = "mongodb+srv://prottoybubt_db_user:nYa0bpNBVhkLvFjI@videoconferenceapp.bpkn0bh.mongodb.net/?appName=VideoConferenceApp"

# # Create a new client and connect to the server
# client = MongoClient(uri, server_api=ServerApi('1'))

# # Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)


import pymongo

uri = "mongodb+srv://prottoybubt_db_user:nYa0bpNBVhkLvFjI@videoconferenceapp.bpkn0bh.mongodb.net/?appName=VideoConferenceApp"

client = pymongo.MongoClient(uri)

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)