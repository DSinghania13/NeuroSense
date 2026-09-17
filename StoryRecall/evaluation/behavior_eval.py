"""
Full Diagnostic Suite (Audio + Behavior + Stats)
------------------------------------------------
Generates audio for the standard 5 scenarios (A-E),
runs the scoring pipeline, and prints the full "UI-style" report.
"""

import os

# --- FIX 1: Suppress Tokenizer Warnings ---
# This must be set BEFORE importing transformers/sentence-transformers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from gtts import gTTS
from pydub import AudioSegment
from StoryRecall.service.story_recall_audio_service import StoryRecallAudioService
from StoryRecall.scoring.scorer import IUScorer

# ==========================================
# 1. SCENARIO DEFINITIONS
# ==========================================
SCENARIOS = {
    "A_Full_Recall": [
        ("Last Monday morning Ravi went to the local market near his house to buy groceries.", 0.2),
        ("He bought vegetables, bread, and milk.", 0.2),
        ("On the way back he met his neighbor and talked about the weather for a few minutes.", 0.2),
        ("After returning home he prepared breakfast, ate his meal, and left for work.", 0.0)
    ],

    "B_Paraphrase_Recall": [
        ("Ravi visited a nearby market...", 2.5),
        ("early in the morning...", 1.0),
        ("to purchase food items.", 0.5),
        ("He got vegetables, milk, and bread.", 0.5),
        ("Later he returned home...", 3.0),
        ("made breakfast, had his food, and went to his office.", 0.0)
    ],

    "C_Partial_Ordered": [
        ("He went to the market and bought vegetables and milk.", 0.5),
        ("Then he returned home and prepared breakfast.", 0.0)
    ],

    "D_Partial_Shuffled": [
        ("After preparing breakfast...", 2.0),
        ("he went to the market and bought milk.", 0.0)
    ],

    "E_Poor_Recall": [
        ("He went out...", 4.0),
        ("and came back home.", 0.0)
    ]
}

# ==========================================
# 2. AUDIO GENERATOR
# ==========================================
def generate_simulation_audio(segments, output_filename):
    combined_audio = AudioSegment.empty()
    if not os.path.exists("temp_chunks"): os.makedirs("temp_chunks")

    print(f"   🔨 Synthesizing {output_filename}...")

    for i, (text, pause_sec) in enumerate(segments):
        chunk_path = f"temp_chunks/chunk_{i}.mp3"
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(chunk_path)

        combined_audio += AudioSegment.from_mp3(chunk_path)
        if pause_sec > 0:
            combined_audio += AudioSegment.silent(duration=pause_sec * 1000)

    combined_audio.export(output_filename, format="mp3")

    for f in os.listdir("temp_chunks"): os.remove(os.path.join("temp_chunks", f))
    os.rmdir("temp_chunks")

# ==========================================
# 3. REPORTING ENGINE (UI STYLE)
# ==========================================
def print_ui_report(label, result):
    s = result["scores"]["summary"]
    d = result["scores"]["details"]
    p = d["pause_details"]

    print(f"\n{'='*80}")
    print(f"▶️  REPORT: {label}")
    print(f"{'='*80}")

    print(f"\n🗣️  TRANSCRIPT (ASR):\n    \"{result['transcript']}\"")

    # --- 1. TRAFFIC LIGHT SCORES ---
    print(f"\n📊 CLINICAL METRICS")
    print(f"  Final Risk Score : {s['final_score']:.4f}  (1.0=Healthy, 0.0=Severe)")
    print(f"  Content (IU)     : {s['iu_normalized']:.4f}")
    print(f"  Structure (G)    : {1.0 - s['gmatch_penalty']:.4f}")
    print(f"  Fluency Score    : {1.0 - s['pause_penalty']:.4f}")

    # --- 2. DETAILED FLUENCY ---
    print(f"\n⏱️  FLUENCY ANALYSIS")
    print(f"  Speech Rate      : {p.get('speech_rate', 0)} words/sec")
    print(f"  Long Pauses      : {p.get('pause_count', 0)} detected (>2.0s)")
    print(f"  Avg Pause Duration: {p.get('avg_pause', 0)} sec")

    # --- 3. IU TRACE TABLE (COMPARISON VIEW) ---
    # FIX 2: Added "EXPECTED" vs "RECALLED" columns
    print(f"\n📋 INFORMATION UNIT TRACE")
    header = f"  {'ID':<5} | {'TYPE':<7} | {'MATCH':<10} | {'SCORE':<5} | {'EXPECTED (Template)':<30} | {'RECALLED (User)'}"
    print(header)
    print(f"  {'-'*len(header)}")

    iu_table = d["iu_table"]
    missed_core = []

    for iu_id, row in iu_table.items():
        if row['score'] == 0 and iu_id in IUScorer.CORE_IUS:
            missed_core.append(iu_id)

        # Truncate texts for cleaner CLI table
        exp = row['expected_text']
        rec = row['matched_recall_text'] or "---"

        if len(exp) > 28: exp = exp[:25] + "..."
        if len(rec) > 28: rec = rec[:25] + "..."

        print(f"  {iu_id:<5} | {row['iu_type']:<7} | {row['match_type']:<10} | {row['score']:<5} | {exp:<30} | {rec}")

    # --- 4. STRUCTURAL INSIGHTS ---
    print(f"\n🧠 STRUCTURAL INSIGHTS")
    print(f"  Missed Core Concepts : {missed_core}")
    print(f"  Primacy (Start) Ratio: {s['primacy_ratio']:.2f}")
    print(f"  Sequence Order       : {d['gmatch_details']['recalled_order']}")

# ==========================================
# 4. MAIN EXECUTION
# ==========================================
def run_full_suite():
    if not os.path.exists("../data"): os.makedirs("../data", exist_ok=True)
    service = StoryRecallAudioService(data_dir="../data")

    print("\n🚀 STARTING FULL AUDIO DIAGNOSTIC SUITE")

    for label, segments in SCENARIOS.items():
        filename = f"{label}.mp3"

        # 1. Generate
        generate_simulation_audio(segments, filename)

        # 2. Analyze
        # We rely on ASR to convert audio to text, simulating real world input
        # NOTE: Ensure your 'asr.py' returns (text, segments) tuple!
        result = service.score_recall_audio(
            story_id="1",
            recall_audio_path=filename
        )

        # 3. Report
        print_ui_report(label, result)

        # 4. Clean
        if os.path.exists(filename): os.remove(filename)
        wav_name = filename.replace(".mp3", ".wav")
        if os.path.exists(wav_name): os.remove(wav_name)

    print("\n✅ SUITE COMPLETE")

if __name__ == "__main__":
    run_full_suite()