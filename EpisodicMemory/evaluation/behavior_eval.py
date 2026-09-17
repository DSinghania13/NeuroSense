"""
Full Memory Diagnostic Suite (Immediate + Delayed Recall)
--------------------------------------------------------
Simulates clinical story recall with delay and evaluates memory decline.
"""

import os

os.environ["TOKENIZERS_PARALLELISM"] = "false"

from gtts import gTTS
from pydub import AudioSegment
from EpisodicMemory.service.episodic_memory_audio_service import MemoryQAAudioService

# ==========================================
# 1. MEMORY SCENARIOS
# ==========================================
SCENARIOS = {
    "A_Healthy": {
        "immediate": [
            ("Last Monday Ravi went to the market to buy groceries.", 0.2),
            ("He bought vegetables, bread, and milk.", 0.2),
            ("He met a neighbor and talked for a while.", 0.2),
            ("Then he returned home and prepared breakfast.", 0.0)
        ],
        "delayed": [
            ("Ravi went to the market and bought vegetables, bread and milk.", 0.5),
            ("He met a neighbor and later returned home to prepare breakfast.", 0.0)
        ]
    },

        "B_MCI": {
        "immediate": [
            ("Ravi went to a market and bought some things.", 1.0),
            ("He got vegetables and maybe milk.", 0.5),
            ("Then he came back home.", 0.0)
        ],
        "delayed": [
            ("He went out to meet a neighbor.", 2.5),
            ("I think he bought something, but I don't remember.", 0.0)
        ]
    },

    "C_High_Risk": {
        "immediate": [
            ("He went to the market.", 1.0),
            ("He bought something.", 0.0)
        ],
        "delayed": [
            ("He went outside.", 3.0),
            ("Then came back.", 0.0)
        ]
    }
}

# ==========================================
# 2. AUDIO GENERATOR
# ==========================================
def generate_audio(segments, filename):
    combined = AudioSegment.empty()

    if not os.path.exists("temp_chunks"):
        os.makedirs("temp_chunks")

    print(f"   🔨 Generating {filename}...")

    for i, (text, pause) in enumerate(segments):
        path = f"temp_chunks/chunk_{i}.mp3"
        gTTS(text=text, lang="en").save(path)

        combined += AudioSegment.from_mp3(path)

        if pause > 0:
            combined += AudioSegment.silent(duration=pause * 1000)

    combined.export(filename, format="mp3")

    for f in os.listdir("temp_chunks"):
        os.remove(os.path.join("temp_chunks", f))
    os.rmdir("temp_chunks")


# ==========================================
# 3. HELPER: FINAL SCORE + INTERPRETATION
# ==========================================
def compute_final_memory_metrics(analysis):
    immediate = analysis["immediate_score"]
    delayed = analysis["delayed_score"]
    forgetting = analysis["forgetting_rate"]

    # Final score (0–100)
    if forgetting is None:
        final_score = 0
    else:
        final_score = max(0, min(100, int((delayed * 0.7 + (1 - forgetting) * 0.3) * 100)))

    # Explanation
    if analysis["memory_status"] == "healthy":
        explanation = "Memory retention is strong with minimal forgetting."
    elif analysis["memory_status"] == "mci":
        explanation = "Moderate memory decline detected; possible early impairment."
    elif analysis["memory_status"] == "high_risk":
        explanation = "Significant memory loss observed; high clinical concern."
    else:
        explanation = "Insufficient data for reliable memory assessment."

    return final_score, explanation


# ==========================================
# 4. MEMORY REPORT
# ==========================================
def print_memory_report(label, result):
    analysis = result["memory_analysis"]

    final_score, explanation = compute_final_memory_metrics(analysis)

    print(f"\n{'='*80}")
    print(f"🧠 MEMORY REPORT: {label}")
    print(f"{'='*80}")

    print("\n📊 MEMORY SCORES")
    print(f"  Immediate Score : {analysis['immediate_score']}")
    print(f"  Delayed Score   : {analysis['delayed_score']}")
    print(f"  Forgetting Rate : {analysis['forgetting_rate']}")
    print(f"  Efficiency      : {analysis['recall_efficiency']}")

    print("\n📉 MEMORY DROP")
    print(f"  Drop Value      : {result['memory_drop']}")

    print("\n🚨 FINAL DIAGNOSIS")
    print(f"  Status          : {analysis['memory_status']}")
    print(f"  Final Score     : {final_score}/100")

    print("\n🧾 INTERPRETATION")
    print(f"  {explanation}")


# ==========================================
# 5. MAIN EXECUTION
# ==========================================
def run_memory_suite():
    service = MemoryQAAudioService(data_dir="../data")

    print("\n🚀 STARTING MEMORY DIAGNOSTIC SUITE")

    for label, scenario in SCENARIOS.items():

        immediate_file = f"{label}_immediate.mp3"
        delayed_file = f"{label}_delayed.mp3"

        # Generate audio
        generate_audio(scenario["immediate"], immediate_file)
        generate_audio(scenario["delayed"], delayed_file)

        # Analyze
        result = service.score_memory_session_audio(
            story_id="1",
            immediate_audio_path=immediate_file,
            delayed_audio_path=delayed_file
        )

        # Report
        print_memory_report(label, result)

        # Cleanup
        for f in [immediate_file, delayed_file]:
            if os.path.exists(f):
                os.remove(f)

    print("\n✅ MEMORY SUITE COMPLETE")


if __name__ == "__main__":
    run_memory_suite()