import os
import certifi
from pymongo import MongoClient

# Read MongoDB URI from environment variable.
# Set MONGODB_URI in your local environment or Hugging Face Secrets.
MONGO_URI = os.getenv("MONGODB_URI")

if not MONGO_URI:
    raise RuntimeError(
        "MONGODB_URI environment variable is not set. "
        "Please configure it in your environment/secrets."
    )

try:
    client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
    db = client.neurosense_db  # Creates/uses the 'neurosense_db' database

    # Define your collections
    doctors_collection = db.doctors
    patients_collection = db.patients
    sessions_collection = db.sessions
    results_collection = db.results
    activity_collection = db.activity

    print("🟢 Successfully connected to MongoDB!")

except Exception as e:
    print(f"❌ Failed to connect to MongoDB: {e}")
    raise
