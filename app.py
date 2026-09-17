import os
import threading
import json
import random
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import uuid
from datetime import datetime, timezone
import time
from werkzeug.security import generate_password_hash, check_password_hash
from db import doctors_collection, patients_collection, results_collection, activity_collection
import glob

# --- 1. Import Backend Modules ---
from EpisodicMemory.service.episodic_memory_audio_service import MemoryQAAudioService
from FreeSpeech.service.free_speech_audio_service import FreeSpeechAudioService
from PictureDescription.service.picture_description_audio_service import PictureDescriptionAudioService
from StoryRecall.service.story_recall_audio_service import StoryRecallAudioService
from speech.tts import text_to_speech

# --- THE FIX: MACOS SSL BYPASS FOR SILENT AI HANGS ---
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context
import nltk
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)

app = Flask(__name__)
CORS(app)

# Create a persistent folder for background uploads
UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- GLOBAL AI SERVICE VARIABLES ---
is_ready = False
is_warming_up = False
warmup_lock = threading.Lock()

_memory_service = None
_freespeech_service = None
_picture_service = None
_story_service = None


# --- BACKGROUND WARMUP THREAD ---
def load_ai_models_background():
    global is_ready, is_warming_up, _memory_service, _freespeech_service, _picture_service, _story_service

    print("🚀 STARTING BACKGROUND AI WARMUP... (This may take 45-90 seconds)")
    try:
        print("🔵 Loading Episodic Memory Pipeline...")
        _memory_service = MemoryQAAudioService(data_dir="EpisodicMemory/data")

        print("🔵 Loading Free Speech Pipeline...")
        _freespeech_service = FreeSpeechAudioService()

        print("🔵 Loading Picture Description Pipeline...")
        _picture_service = PictureDescriptionAudioService(data_dir="./PictureDescription/data")

        print("🔵 Loading Story Recall Pipeline...")
        _story_service = StoryRecallAudioService(data_dir="./StoryRecall/data")

        is_ready = True
        print("✅ ALL MODELS LOADED INTO RAM. SYSTEM UNLOCKED.")
    except Exception as e:
        print(f"❌ FATAL ERROR LOADING MODELS: {str(e)}")
    finally:
        is_warming_up = False


# ==========================================
# SYSTEM ROUTES
# ==========================================

@app.route('/api/warmup', methods=['GET'])
def warmup_models():
    """Silent endpoint hit by the React UI to wake up the AI models."""
    global is_warming_up, is_ready

    # If done, give the green light immediately
    if is_ready:
        return jsonify({"status": "online", "ready": True}), 200

    # If not started, lock the state and start ONE thread
    if not is_warming_up:
        is_warming_up = True
        threading.Thread(target=load_ai_models_background, daemon=True).start()
        return jsonify({"status": "warming_up", "ready": False}), 202

    # If already loading, just tell the frontend to keep waiting (This triggers your 200 loop)
    return jsonify({"status": "warming_up", "ready": False}), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"ready": is_ready}), 200


def get_stories_db_path():
    possible_paths = [
        'MemoryQA/data/stories.json',
        'EpisodicMemory/data/stories.json',
        './MemoryQA/data/stories.json',
        'stories.json'
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return path
    raise FileNotFoundError("Could not find stories.json in any expected directory!")


# --- MONGODB DATABASE HELPER ---
def save_to_db(session_id, test_name, result_data, patient_id=None):
    """Saves AI results and links them to the patient."""
    try:
        update_payload = {
            test_name: result_data,
            "updated_at": datetime.utcnow().isoformat()
        }

        set_on_insert = {"created_at": datetime.utcnow().isoformat()}
        if patient_id:
            set_on_insert["patient_id"] = patient_id

        results_collection.update_one(
            {"session_id": session_id},
            {"$set": update_payload, "$setOnInsert": set_on_insert},
            upsert=True
        )
        if patient_id:
            patient = patients_collection.find_one({"patient_id": patient_id})
            if patient and "doctor_id" in patient:
                formatted_test_name = test_name.replace('_', ' ').title()
                log_activity(
                    patient["doctor_id"],
                    "Diagnostic Completed",
                    f"{formatted_test_name} processed for {patient.get('name', 'Patient')}",
                    "analytics"
                )
        print(f"💾 Saved {test_name} results for session {session_id} to MongoDB!")
    except Exception as e:
        print(f"❌ MongoDB Save Error: {str(e)}")

# --- AUDIT LOG HELPER ---
def log_activity(doctor_id, title, subtitle, icon="info"):
    """Pushes a timeline event to the doctor's dashboard."""
    try:
        activity_collection.insert_one({
            "doctor_id": doctor_id,
            "title": title,
            "subtitle": subtitle,
            "icon": icon,
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        print(f"⚠️ Failed to log activity: {e}")


# --- BACKGROUND SCORING WORKERS ---
def process_memory_bg(story_id, imm_path, del_path, session_id, patient_id=None):
    try:
        print(f"⚙️ [Background] Scoring Memory QA for {session_id}...")
        result = _memory_service.score_memory_session_audio(
            story_id=story_id, immediate_audio_path=imm_path, delayed_audio_path=del_path
        )
        save_to_db(session_id, "memory_qna", result, patient_id)
    except Exception as e:
        print(f"❌ [Background] Memory Error: {str(e)}")
        save_to_db(session_id, "memory_qna", {"error": str(e), "status": "failed"}, patient_id)
    finally:
        # ---> THE FIX: Use your new threaded safe_delete!
        safe_delete(imm_path)
        safe_delete(del_path)

def process_freespeech_bg(audio_path, session_id, patient_id=None):
    try:
        print(f"⚙️ [Background] Analyzing Free Speech for {session_id}...")
        result = _freespeech_service.analyze_audio(audio_path=audio_path)
        save_to_db(session_id, "free_speech", result, patient_id)
    except Exception as e:
        print(f"❌ [Background] Free Speech Error: {str(e)}")
        save_to_db(session_id, "free_speech", {"error": str(e), "status": "failed"}, patient_id)
    finally:
        # ---> THE FIX: Use your new threaded safe_delete!
        safe_delete(audio_path)

def process_picture_bg(picture_id, audio_path, session_id, patient_id=None):
    try:
        print(f"⚙️ [Background] Scoring Picture Description for {session_id}...")
        result = _picture_service.score_description_audio(
            picture_id=picture_id, audio_path=audio_path
        )
        save_to_db(session_id, "picture_description", result, patient_id)
    except Exception as e:
        print(f"❌ [Background] Picture Error: {str(e)}")
        save_to_db(session_id, "picture_description", {"error": str(e), "status": "failed"}, patient_id)
    finally:
        # ---> THE FIX: Use your new threaded safe_delete!
        safe_delete(audio_path)

def process_story_bg(story_id, audio_path, session_id, patient_id=None):
    try:
        print(f"⚙️ [Background] Scoring Story Recall for {session_id}...")
        result = _story_service.score_recall_audio(
            story_id=story_id, recall_audio_path=audio_path
        )
        save_to_db(session_id, "story_recall", result, patient_id)
    except Exception as e:
        print(f"❌ [Background] Story Recall Error: {str(e)}")
        save_to_db(session_id, "story_recall", {"error": str(e), "status": "failed"}, patient_id)
    finally:
        # ---> THE FIX: Use your new threaded safe_delete!
        safe_delete(audio_path)


# --- GARBAGE COLLECTION HELPER ---
def cleanup_zombie_files():
    """Runs in the background and deletes any intermediate temp files older than 2 hours."""
    import time  # <--- BULLETPROOF LOCAL IMPORT
    import os
    import glob

    while True:
        try:
            now = time.time()
            # Look at all files in the temp folder
            for filepath in glob.glob(os.path.join(UPLOAD_DIR, "*")):
                # If the file has been sitting there for more than 2 hours (7200 seconds)
                if os.path.getmtime(filepath) < now - 7200:
                    os.remove(filepath)
                    print(f"🧹 Swept up abandoned zombie file: {filepath}")
        except Exception as e:
            print(f"⚠️ Warning in zombie sweeper: {e}")

        time.sleep(3600)  # Go back to sleep for 1 hour


def _background_delete(filepath, max_retries=5, delay=2):
    """Worker function that continuously tries to delete a locked file."""
    import time  # <--- BULLETPROOF LOCAL IMPORT
    import os

    for attempt in range(max_retries):
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"🗑️ Cleaned up temp file: {filepath}")
            return  # Exit the thread immediately if successful
        except OSError:
            # File is likely still locked by the OS or PyTorch
            # Sleep and try again on the next loop
            time.sleep(delay)

    print(f"⚠️ Warning: OS refused to release lock on {filepath} after {max_retries} attempts.")


def safe_delete(filepath):
    """Spawns a detached background thread to delete the file without blocking anything."""
    threading.Thread(target=_background_delete, args=(filepath,), daemon=True).start()


# ==========================================
# TEST ROUTES
# ==========================================

@app.route('/api/memory/random_story', methods=['GET'])
def get_random_story():
    try:
        db_path = get_stories_db_path()
        with open(db_path, 'r') as f:
            stories_db = json.load(f)
        story_id = random.choice(list(stories_db.keys()))
        story_text = stories_db[story_id]['text']
        return jsonify({"story_id": story_id, "text": story_text}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to load random story: {str(e)}"}), 500


@app.route('/api/tts', methods=['POST'])
def generate_tts():
    story_id = request.json.get('story_id')
    session_id = request.json.get('session_id', 'temp')
    if not story_id:
        return jsonify({"error": "No story_id provided"}), 400
    try:
        db_path = get_stories_db_path()
        with open(db_path, 'r') as f:
            stories_db = json.load(f)
        story_text = stories_db[str(story_id)]['text']
    except Exception as e:
        return jsonify({"error": f"Failed to load story from DB: {str(e)}"}), 500

    out_path = os.path.join(UPLOAD_DIR, f"{session_id}_tts.mp3")
    text_to_speech(story_text, out_path)

    # ---> THE FIX: Trigger safe_delete in the background after sending!
    @after_this_request
    def remove_file(response):
        # Pass the filepath directly to our threaded deleter
        threading.Thread(target=_background_delete, args=(out_path, 5, 2), daemon=True).start()
        return response

    return send_file(out_path, mimetype="audio/mpeg")


@app.route('/api/memory/immediate', methods=['POST'])
def process_memory_immediate():
    if 'audio' not in request.files:
        return jsonify({"error": "Missing audio file"}), 400
    session_id = request.form.get('session_id', 'unknown_session')

    imm_path = os.path.join(UPLOAD_DIR, f"{session_id}_imm.webm")
    request.files['audio'].save(imm_path)
    return jsonify({"status": "immediate_saved"}), 200


@app.route('/api/memory/delayed', methods=['POST'])
def process_memory_delayed():
    if 'audio' not in request.files:
        return jsonify({"error": "Missing audio file"}), 400
    story_id = request.form.get('story_id', '1')
    session_id = request.form.get('session_id', 'unknown_session')
    patient_id = request.form.get('patient_id')

    del_path = os.path.join(UPLOAD_DIR, f"{session_id}_del.webm")
    request.files['audio'].save(del_path)

    imm_path = os.path.join(UPLOAD_DIR, f"{session_id}_imm.webm")
    threading.Thread(target=process_memory_bg, args=(story_id, imm_path, del_path, session_id, patient_id)).start()
    return jsonify({"status": "processing"}), 202


@app.route('/api/freespeech', methods=['POST'])
def process_freespeech():
    if 'audio' not in request.files:
        return jsonify({"error": "Missing audio file"}), 400
    session_id = request.form.get('session_id', 'unknown_session')
    patient_id = request.form.get('patient_id')

    audio_path = os.path.join(UPLOAD_DIR, f"{session_id}_freespeech.webm")
    request.files['audio'].save(audio_path)

    threading.Thread(target=process_freespeech_bg, args=(audio_path, session_id, patient_id)).start()
    return jsonify({"status": "processing", "session_id": session_id}), 202


@app.route('/api/picture', methods=['POST'])
def process_picture():
    if 'audio' not in request.files:
        return jsonify({"error": "Missing audio file"}), 400
    picture_id = request.form.get('picture_id', 'cookie_theft')
    session_id = request.form.get('session_id', 'unknown_session')
    patient_id = request.form.get('patient_id')

    audio_path = os.path.join(UPLOAD_DIR, f"{session_id}_picture.webm")
    request.files['audio'].save(audio_path)

    threading.Thread(target=process_picture_bg, args=(picture_id, audio_path, session_id, patient_id)).start()
    return jsonify({"status": "processing", "session_id": session_id}), 202


@app.route('/api/story', methods=['POST'])
def process_story():
    if 'audio' not in request.files:
        return jsonify({"error": "Missing audio file"}), 400
    story_id = request.form.get('story_id', '1')
    session_id = request.form.get('session_id', 'unknown_session')
    patient_id = request.form.get('patient_id')

    audio_path = os.path.join(UPLOAD_DIR, f"{session_id}_story.webm")
    request.files['audio'].save(audio_path)

    threading.Thread(target=process_story_bg, args=(story_id, audio_path, session_id, patient_id)).start()
    return jsonify({"status": "processing", "session_id": session_id}), 202


# ==========================================
# AUTH & PATIENT MANAGEMENT ROUTES
# ==========================================

@app.route('/api/auth/register', methods=['POST'])
def register_doctor():
    data = request.json
    email = data.get('email')

    if doctors_collection.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 400

    doctor_id = f"DOC-{uuid.uuid4().hex[:8].upper()}"
    hashed_password = generate_password_hash(data.get('password'))

    # Hash the security answer so it can never be stolen! (Convert to lowercase to make it case-insensitive)
    security_answer_raw = data.get('security_answer', '').strip().lower()
    hashed_answer = generate_password_hash(security_answer_raw)

    doctor_profile = {
        "doctor_id": doctor_id,
        "name": data.get('name'),
        "email": email,
        "password": hashed_password,
        "specialty": data.get('specialty', 'General Practice'),
        "clinic_name": data.get('clinic_name', 'Independent Clinic'),
        "security_question": data.get('security_question', "What is your mother's maiden name?"),
        "security_answer": hashed_answer,
        "created_at": datetime.utcnow().isoformat()
    }

    doctors_collection.insert_one(doctor_profile)

    # Return profile without sensitive data
    doctor_profile.pop('_id', None)
    doctor_profile.pop('password', None)
    doctor_profile.pop('security_answer', None)

    return jsonify({"status": "success", **doctor_profile}), 201


@app.route('/api/auth/login', methods=['POST'])
def login_doctor():
    data = request.json
    doctor = doctors_collection.find_one({"email": data.get('email')})

    if doctor and check_password_hash(doctor['password'], data.get('password')):
        doctor.pop('_id', None)
        doctor.pop('password', None)
        return jsonify({"status": "success", **doctor}), 200

    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/api/doctors/<doctor_id>/password', methods=['PUT'])
def update_password(doctor_id):
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    doctor = doctors_collection.find_one({"doctor_id": doctor_id})
    if not doctor:
        return jsonify({"error": "Doctor not found"}), 404

    # Verify old password
    if not check_password_hash(doctor['password'], current_password):
        return jsonify({"error": "Incorrect current password"}), 401

    # Save new password
    hashed_password = generate_password_hash(new_password)
    doctors_collection.update_one(
        {"doctor_id": doctor_id},
        {"$set": {"password": hashed_password}}
    )

    # Log it to the Dashboard Audit Trail!
    log_activity(doctor_id, "Security Update", "Account password was changed.", "lock")

    return jsonify({"status": "success", "message": "Password updated successfully"}), 200

# --- NEW: FETCH SECURITY QUESTION ---
@app.route('/api/auth/security-question', methods=['POST'])
def get_security_question():
    email = request.json.get('email')
    doctor = doctors_collection.find_one({"email": email})

    if not doctor:
        return jsonify({"error": "Account not found."}), 404

    question = doctor.get('security_question', "What is your mother's maiden name?")
    return jsonify({"status": "success", "question": question}), 200

# --- NEW: RESET PASSWORD VIA SECURITY QUESTION ---
@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.json
    email = data.get('email')
    answer = data.get('security_answer', '').strip().lower()
    new_password = data.get('new_password')

    doctor = doctors_collection.find_one({"email": email})
    if not doctor:
        return jsonify({"error": "Account not found."}), 404

    # Verify the security answer matches the hash in the database
    if not check_password_hash(doctor.get('security_answer', ''), answer):
        return jsonify({"error": "Incorrect security answer."}), 401

    # Save the new password
    hashed_password = generate_password_hash(new_password)
    doctors_collection.update_one({"email": email}, {"$set": {"password": hashed_password}})

    # Audit Trail
    log_activity(doctor["doctor_id"], "Password Reset", "Account password was reset via security verification.",
                 "lock_reset")

    return jsonify({"status": "success", "message": "Password reset successfully"}), 200

@app.route('/api/doctors/<doctor_id>/activity', methods=['GET'])
def get_activity(doctor_id):
    """Fetches the 10 most recent activities for the dashboard."""
    # Sort by newest first, limit to 10 so the UI doesn't get cluttered
    activities = list(activity_collection.find({"doctor_id": doctor_id}, {"_id": 0}).sort("timestamp", -1).limit(10))
    return jsonify(activities), 200

@app.route('/api/doctors/<doctor_id>/patients', methods=['POST'])
def add_patient(doctor_id):
    data = request.json
    patient_id = f"PAT-{uuid.uuid4().hex[:8].upper()}"

    new_patient = {
        "patient_id": patient_id,
        "doctor_id": doctor_id,
        "name": data.get('name', 'Anonymous'),
        "dob": data.get('dob'),  # <-- CHANGED FROM AGE TO DOB
        "gender": data.get('gender'),
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    patients_collection.insert_one(new_patient)
    log_activity(
        doctor_id,
        "New Patient Registered",
        f"Added {new_patient['name']} to the directory.",
        "person_add"
    )
    new_patient.pop('_id', None)
    return jsonify({"status": "success", "patient": new_patient}), 201


@app.route('/api/doctors/<doctor_id>/patients', methods=['GET'])
def get_patients(doctor_id):
    patients = list(patients_collection.find({"doctor_id": doctor_id}, {"_id": 0}).sort("created_at", -1))
    return jsonify(patients), 200


# --- NEW: EDIT PATIENT ---
@app.route('/api/patients/<patient_id>', methods=['PUT'])
def edit_patient(patient_id):
    data = request.json
    update_fields = {}

    if 'name' in data: update_fields['name'] = data['name']
    if 'dob' in data: update_fields['dob'] = data['dob']
    if 'gender' in data: update_fields['gender'] = data['gender']

    if update_fields:
        patients_collection.update_one({"patient_id": patient_id}, {"$set": update_fields})

    return jsonify({"status": "success", "message": "Patient updated successfully"}), 200


# --- NEW: DELETE PATIENT (CASCADING) ---
@app.route('/api/patients/<patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    try:
        # 1. Delete the patient profile
        patients_collection.delete_one({"patient_id": patient_id})

        # 2. Delete ALL their cognitive reports to prevent orphaned data!
        deleted_reports = results_collection.delete_many({"patient_id": patient_id})

        return jsonify({
            "status": "success",
            "message": f"Patient and {deleted_reports.deleted_count} reports deleted."
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/patients/<patient_id>/reports', methods=['GET'])
def get_patient_reports(patient_id):
    reports = list(results_collection.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1))
    return jsonify(reports), 200

@app.route('/api/results/<session_id>', methods=['GET'])
def get_results(session_id):
    """Fetches the diagnostic results for a specific session from MongoDB."""
    try:
        result = results_collection.find_one({"session_id": session_id}, {"_id": 0})
        if not result:
            return jsonify({"error": "Session not found", "status": "processing"}), 404

        patient_id = result.get("patient_id")
        if patient_id:
            patient = patients_collection.find_one({"patient_id": patient_id}, {"_id": 0})
            if patient:
                result["patient"] = patient

        result.pop("session_id", None)
        return jsonify(result), 200
    except Exception as e:
        print(f"❌ MongoDB Fetch Error: {str(e)}")
        return jsonify({"error": f"Failed to fetch results: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(port=5000, debug=True, use_reloader=False)