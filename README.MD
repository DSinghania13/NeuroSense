# 🧠 NeuroSense – AI-Assisted Cognitive Speech Assessment

**NeuroSense** is a full-stack clinical workflow application for collecting and analysing speech-based cognitive assessment tasks. It combines a React dashboard for clinicians with a Flask API and NLP/audio pipelines for **free speech, picture description, story recall, and episodic memory** tasks.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Flask](https://img.shields.io/badge/Backend-Flask-green)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB)
![AI](https://img.shields.io/badge/AI-Whisper%20%7C%20SBERT%20%7C%20NLP-orange)

---

> ⚕️ **Research and decision-support tool:** NeuroSense generates automated assessment signals and reports. It is not a substitute for clinical judgment, formal diagnosis, or emergency medical care.

## 🚀 Features

- **🗣️ Free Speech Analysis** – Analyses fluency, disfluencies, lexical diversity, coherence, syntax, repetition, idea density, and language-model perplexity.
- **🖼️ Picture Description** – Records a response to a clinical image stimulus and evaluates information units, spatial language, and pause behaviour.
- **📖 Story Recall** – Presents a story, records recall, and scores recalled information units and speech pauses.
- **🧠 Episodic Memory** – Supports immediate and delayed recall to assess encoding, retention, forgetting rate, and recall efficiency.
- **🎙️ Audio-First Workflow** – Browser recording, speech-to-text processing, optional text-to-speech narration, and background scoring.
- **👩‍⚕️ Clinician Workspace** – Doctor accounts, patient management, activity history, diagnostic sessions, and generated reports.
- **📄 Report Export** – Presents per-module results and supports PDF report generation from the dashboard.
- **⚡ Model Warm-Up** – Loads AI services in the background and keeps assessment screens locked until they are ready.

---

## 🛠️ Tech Stack

| Component | Technology Used |
| --- | --- |
| Frontend | React 19, Vite, React Router, Tailwind CSS |
| Backend | Python, Flask, Flask-CORS |
| Database | MongoDB / PyMongo |
| Speech | OpenAI Whisper, gTTS, pydub, SoundFile |
| NLP & Scoring | spaCy, NLTK, Sentence Transformers (SBERT), scikit-learn |
| Deep Learning | PyTorch, Transformers |
| Reporting | html2pdf.js, react-to-print |

---

## 📋 Assessment Modules

| Module | What it evaluates |
| --- | --- |
| **Free Speech** | Speech fluency, lexical and syntactic features, disfluency, coherence, repetition, and idea density. |
| **Picture Description** | Relevant information units, semantic similarity, spatial relations, and pauses from a spoken image description. |
| **Story Recall** | Recall of story information units, structure, semantic similarity, and pause analysis. |
| **Episodic Memory** | Immediate and delayed story recall, memory drop, forgetting rate, and recall efficiency. |

---

## 📁 Project Structure

```text
NeuroSense/
├── app.py                         # Flask API and background scoring workers
├── db.py                          # MongoDB collections and connection setup
├── requirements.txt               # Python dependencies
├── frontend/                      # React + Vite clinician dashboard
│   ├── src/
│   │   ├── pages/                 # Auth, patient, assessment, and report views
│   │   ├── components/            # Recorder, layout, reporting, and UI components
│   │   └── context/               # Authentication and notification state
│   ├── package.json
│   └── vite.config.js             # Development proxy to Flask
├── speech/
│   ├── asr.py                     # Speech-to-text utilities
│   ├── tts.py                     # Text-to-speech narration
│   └── audio_utils.py
├── FreeSpeech/                    # Spontaneous-speech analysis pipeline
│   ├── pipeline/
│   ├── preprocessing/
│   ├── scoring/
│   ├── qc/
│   └── service/
├── PictureDescription/            # Picture-description assessment pipeline
│   ├── data/pictures/
│   ├── preprocessing/
│   ├── scoring/
│   └── service/
├── StoryRecall/                   # Story-recall assessment pipeline
│   ├── data/
│   ├── loaders/
│   ├── scoring/
│   └── service/
└── EpisodicMemory/                # Immediate and delayed recall pipeline
    ├── data/
    ├── loaders/
    ├── scoring/
    └── service/
```

---

## 🧑‍💻 Installation & Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd NeuroSense
```

### 2. Create a Python Virtual Environment

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The first run may download required NLTK data and model assets, so allow time for the initial setup.

### 4. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

### 5. Configure MongoDB

NeuroSense stores clinician accounts, patient records, activity, and assessment results in MongoDB. Ensure the connection configured in [`db.py`](db.py) points to a MongoDB deployment you can access before starting the backend.

---

## ▶️ Run NeuroSense

Start the backend from the project root:

```bash
python app.py
```

The Flask API runs at `http://127.0.0.1:5000`.

In a second terminal, start the frontend:

```bash
cd frontend
npm run dev
```

Open the local URL printed by Vite (usually `http://localhost:5173`). The frontend proxies `/api` requests to the Flask backend.

When the app opens, it starts loading the assessment models in the background. Wait until the system indicates the models are ready before beginning a session.

---

## 🩺 Typical Workflow

1. Register or sign in as a clinician.
2. Add or select a patient.
3. Create a diagnosis session and choose one or more speech tasks.
4. Record the participant's responses in the browser.
5. Wait for background processing to complete.
6. Review module-level signals and export the resulting report.

---

## ⚙️ Requirements

- **Python 3.10+** recommended
- **Node.js 18+** and npm
- A reachable **MongoDB** deployment
- A modern browser with microphone permission enabled
- Internet access on first run for model and language-resource downloads

The AI pipelines load Whisper, sentence-transformer, and NLP resources. Startup can take longer than a standard web app, particularly on the first launch.

---

## 🔌 Main API Areas

| Area | Example endpoints |
| --- | --- |
| System readiness | `GET /api/warmup`, `GET /api/health` |
| Assessment processing | `/api/freespeech`, `/api/picture`, `/api/story`, `/api/memory/*` |
| Authentication | `/api/auth/register`, `/api/auth/login` |
| Patient management | `/api/doctors/:doctor_id/patients`, `/api/patients/:patient_id` |
| Results | `GET /api/results/:session_id` |

---

## 🔒 Privacy & Deployment Notes

- Assessment audio is uploaded temporarily for processing and cleaned up by background workers.
- The application stores patient and assessment data in MongoDB; use a secure, access-controlled deployment for real data.
- Before any production or clinical use, review authentication, authorization, audit, encryption, retention, consent, and applicable privacy requirements for your setting.
