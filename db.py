import os
import certifi
from pymongo import MongoClient

# For local development, it connects to local Mongo.
# On Hugging Face, you will set the 'MONGO_URI' environment variable!
MONGO_URI = "mongodb+srv://divitsinghania05_db_user:RoebPHqKKQM7R7Pt@neurosense.ap1nzze.mongodb.net/?appName=NeuroSense"

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.neurosense_db  # Creates a database called 'neurosense_db'

    # Define your collections (Tables)
    doctors_collection = db.doctors
    patients_collection = db.patients
    sessions_collection = db.sessions
    results_collection = db.results
    activity_collection = db.activity

    print("🟢 Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")